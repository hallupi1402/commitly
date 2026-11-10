"""Local-only prose generation with evidence IDs checked at the boundary."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Callable
from uuid import NAMESPACE_URL, uuid5


class AnalysisUnavailable(RuntimeError):
    pass


_SENSITIVE_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|secret|password)\s*([=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"\b(?:ghp|github_pat|glpat|xox[baprs])_[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)(https?://)[^/@:\s]+:[^/@\s]+@"),
)


def redact_text(value: str) -> str:
    """Mask common credential shapes before model input and report persistence."""
    # shortcut: masks common token shapes only; broaden before handling new credential formats.
    value = _SENSITIVE_PATTERNS[0].sub(r"\1\2[REDACTED]", value)
    value = _SENSITIVE_PATTERNS[1].sub("Bearer [REDACTED]", value)
    value = _SENSITIVE_PATTERNS[2].sub("[REDACTED_TOKEN]", value)
    value = _SENSITIVE_PATTERNS[3].sub("[REDACTED_AWS_KEY]", value)
    return _SENSITIVE_PATTERNS[4].sub(r"\1[REDACTED]@", value)


def _redact_value(value):
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact_value(item) for key, item in value.items()}
    return value


def local_runner(model: str | None = None, executable: str | None = None) -> Callable[[str], str]:
    def run(prompt: str) -> str:
        command = os.environ.get("COMMITLY_LLM_EXECUTABLE", executable or "llama-cli")
        model_path = model or os.environ.get("COMMITLY_LLM_MODEL")
        if not model_path or not shutil.which(command):
            raise AnalysisUnavailable("Local model is not configured; source evidence was retained without prose analysis")
        try:
            result = subprocess.run(
                [command, "-m", model_path, "-p", prompt, "-n", "1000", "--no-display-prompt"],
                capture_output=True, text=True, timeout=180, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AnalysisUnavailable("The configured local model could not complete analysis") from exc
        if result.returncode:
            raise AnalysisUnavailable("The configured local model returned an error")
        return result.stdout
    return run


def analyze(evidence: list[dict], runner: Callable[[str], str] | None = None) -> dict:
    if not evidence or runner is None:
        raise AnalysisUnavailable("Local model is unavailable for semantic report generation")
    evidence_ids = {item["id"] for item in evidence}
    sanitized = _redact_value(evidence)
    prompt = (
        "Bạn là công cụ viết báo cáo công việc từ bằng chứng Git. Chỉ dùng dữ liệu JSON dưới đây; "
        "không suy đoán ý định hoặc việc developer đã đọc tài liệu. Viết tiếng Việt tự nhiên. "
        "Trả về duy nhất JSON dạng {summary:{text,evidence_ids,certainty},highlights:[{text,evidence_ids,certainty}],details:[{text,evidence_ids,certainty}]}. "
        "Mỗi claim phải trỏ tới một hoặc nhiều id thật; giữ nguyên tên file và identifier.\n"
        + json.dumps(sanitized, ensure_ascii=False)
    )
    if len(prompt) > 50_000:
        raise AnalysisUnavailable("Daily source content exceeds the local analysis limit; Git evidence was retained")
    raw = runner(prompt)
    try:
        value = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError) as exc:
        raise AnalysisUnavailable("Local model output was not valid report JSON") from exc
    if not isinstance(value, dict) or not isinstance(value.get("summary"), dict):
        raise AnalysisUnavailable("Local model output was missing its summary")

    def claim(item: dict, kind: str, index: int) -> dict:
        text = item.get("text")
        refs = item.get("evidence_ids")
        if not isinstance(text, str) or not text.strip() or not isinstance(refs, list) or not refs or not set(refs) <= evidence_ids:
            raise AnalysisUnavailable("Local model returned a claim without valid evidence")
        refs = sorted(set(refs))
        certainty = item.get("certainty", "supported")
        if certainty not in {"supported", "uncertain"}:
            raise AnalysisUnavailable("Local model returned an invalid certainty value")
        stable = f"{kind}:{index}:{','.join(refs)}"
        return {"id": str(uuid5(NAMESPACE_URL, stable)), "text": redact_text(text.strip()), "evidence_ids": refs, "certainty": certainty}

    try:
        return {
            "summary": claim(value["summary"], "summary", 0),
            "highlights": [claim(item, "highlight", i) for i, item in enumerate(value.get("highlights", []))],
            "details": [claim(item, "detail", i) for i, item in enumerate(value.get("details", []))],
        }
    except (TypeError, AttributeError) as exc:
        raise AnalysisUnavailable("Local model returned a malformed report claim") from exc
