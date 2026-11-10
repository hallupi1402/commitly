"""Markdown persistence for generated daily reports."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from commitly import journal

_META = re.compile(r"^<!-- commitly:report-data v1\n(\{.*\})\n-->$", re.M | re.S)


def _revision(raw: bytes) -> str:
    return f'"{hashlib.sha256(raw).hexdigest()}"'


def _validate(report: dict, expected_date: date | None = None) -> dict:
    if not isinstance(report, dict):
        raise ValueError("Report must be an object")
    try:
        report_date = date.fromisoformat(report["date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Report date must use YYYY-MM-DD") from exc
    if expected_date and report_date != expected_date:
        raise ValueError("Report date does not match the requested date")
    if report.get("analysis_status") not in {"complete", "partial", "unavailable"}:
        raise ValueError("Report analysis status is invalid")
    evidence = report.get("evidence")
    if not isinstance(evidence, list):
        raise ValueError("Report evidence must be a list")
    evidence_ids = set()
    for item in evidence:
        try:
            item["id"] = str(UUID(item["id"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Evidence IDs must be UUIDs") from exc
        evidence_ids.add(item["id"])
    for claim in [report.get("summary"), *report.get("highlights", []), *report.get("details", [])]:
        if not isinstance(claim, dict) or not isinstance(claim.get("text"), str):
            raise ValueError("Every report claim must have text")
        claim["text"] = " ".join(claim["text"].split())
        try:
            claim["id"] = str(UUID(claim["id"]))
            claim["evidence_ids"] = [str(UUID(value)) for value in claim["evidence_ids"]]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Report claims require valid IDs and evidence links") from exc
        if (not claim["evidence_ids"] and evidence_ids) or not set(claim["evidence_ids"]) <= evidence_ids:
            raise ValueError("Every report claim must link to evidence in this report")
        if claim.get("certainty") not in {"supported", "uncertain"}:
            raise ValueError("Report claim certainty is invalid")
    context = report.get("user_context", [])
    if not isinstance(context, list) or len(context) > 1:
        raise ValueError("A report can contain at most one user context line")
    for item in context:
        try:
            item["id"] = str(UUID(item["id"]))
            text = item["text"].strip()
            if not text or len(text) > 500 or "\n" in text or "\r" in text:
                raise ValueError("User context must be one non-empty line of at most 500 characters")
            item["text"] = text
            timestamp = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError("User context timestamp must include a timezone")
        except (KeyError, TypeError, AttributeError, ValueError) as exc:
            raise ValueError("User context requires a UUID, timestamp, and one non-empty line") from exc
    return report


def render_report(report: dict) -> str:
    value = _validate(report)
    day = date.fromisoformat(value["date"])
    def linked(claim: dict) -> str:
        qualifier = "Có thể: " if claim["certainty"] == "uncertain" else ""
        link = f" [evidence: {', '.join(claim['evidence_ids'])}]" if claim["evidence_ids"] else ""
        return f"{qualifier}{claim['text']}{link}"

    lines = [f"<!-- commitly:report v1 date={value['date']} -->", f"# Báo cáo công việc — {day:%d/%m/%Y}", "", "## Tóm tắt", "", linked(value["summary"]), "", "## Điểm chính", ""]
    lines.extend(f"- {linked(claim)}" for claim in value["highlights"])
    lines.extend(f"- Người dùng ghi: {context['text']}" for context in value.get("user_context", []))
    if not value["highlights"] and not value.get("user_context"):
        lines.append("Chưa có điểm chính.")
    lines.extend(["", "## Chi tiết", ""])
    lines.extend(f"- {linked(claim)}" for claim in value["details"])
    if not value["details"]:
        lines.append("Phân tích chi tiết chưa khả dụng.")
    lines.extend(["", "## Log nguồn", ""])
    for item in value["evidence"]:
        paths = ", ".join(f"`{path}`" for path in item["changed_paths"])
        counts = "" if item["added_lines"] is None else f" (+{item['added_lines']} / -{item['deleted_lines']})"
        lines.append(f"- {item['repository_name']} (`{item['repository_path']}`) · `{item['commit_id']}` — {item['subject']} · {item['authored_at']} · {paths}{counts}")
    lines.extend(["", "<!-- commitly:report-data v1", json.dumps(value, ensure_ascii=False, separators=(",", ":")), "-->", ""])
    return "\n".join(lines)


def parse_report(raw: str, expected_date: date | None = None) -> dict:
    match = _META.search(raw)
    if not match:
        raise ValueError("Report Markdown is malformed or uses an unsupported version")
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError("Report metadata is malformed") from exc
    value = _validate(value, expected_date)
    return _read_visible_report(raw, value)


def _claim_from_visible(line: str, kind: str, index: int, existing: dict | None, report_date: str, evidence_ids: set[str]) -> dict:
    match = re.search(r"\s+\[evidence: ([0-9a-fA-F,-]+(?:, [0-9a-fA-F,-]+)*)\]$", line)
    if match:
        refs = [str(UUID(item.strip())) for item in match.group(1).split(",")]
        text = line[:match.start()].strip()
    elif not evidence_ids:
        refs, text = [], line.strip()
    else:
        raise ValueError("Edited report claim is missing its visible evidence link")
    certainty = "uncertain" if text.startswith("Có thể: ") else "supported"
    if certainty == "uncertain":
        text = text.removeprefix("Có thể: ").strip()
    identifier = existing["id"] if existing else str(uuid5(NAMESPACE_URL, f"{report_date}:{kind}:{index}:{','.join(refs)}"))
    return {"id": identifier, "text": text, "evidence_ids": refs, "certainty": certainty}


def _visible_claims(lines: list[str], kind: str, existing: list[dict], report_date: str, evidence_ids: set[str], empty_text: str) -> list[dict]:
    nonempty = [line.strip() for line in lines if line.strip()]
    if nonempty == [empty_text]:
        return []
    result = []
    for index, line in enumerate(nonempty):
        if not line.startswith("- "):
            raise ValueError("Edited report section must keep one Markdown bullet per item")
        text = line[2:]
        if kind == "highlights" and text.startswith("Người dùng ghi: "):
            continue
        result.append(_claim_from_visible(text, kind, index, existing[index] if index < len(existing) else None, report_date, evidence_ids))
    return result


def _read_visible_report(raw: str, value: dict) -> dict:
    marker = _META.search(raw)
    if not marker:
        raise ValueError("Report Markdown is malformed or uses an unsupported version")
    if raw[marker.end():] not in {"", "\n"}:
        raise ValueError("Report Markdown contains external content after its metadata")
    body = raw[:marker.start()]
    lines = body.splitlines()
    headings = ["## Tóm tắt", "## Điểm chính", "## Chi tiết", "## Log nguồn"]
    positions = [lines.index(heading) for heading in headings if heading in lines]
    if len(positions) != 4 or positions != sorted(positions) or len(lines) < 2 or lines[1] != f"# Báo cáo công việc — {date.fromisoformat(value['date']):%d/%m/%Y}":
        raise ValueError("Report Markdown sections or title were edited outside Commitly")
    # Keep evidence records controlled by the source log; user edits prose and context.
    expected = render_report(value).split("## Log nguồn\n", 1)[1].split("<!-- commitly:report-data", 1)[0]
    actual = body.split("## Log nguồn\n", 1)[1]
    if expected != actual:
        raise ValueError("Report source log was edited outside Commitly")
    summary_lines = lines[positions[0] + 1:positions[1]]
    summary_text = " ".join(line.strip() for line in summary_lines if line.strip())
    value["summary"] = _claim_from_visible(summary_text, "summary", 0, value["summary"], value["date"], {item["id"] for item in value["evidence"]})
    evidence_ids = {item["id"] for item in value["evidence"]}
    value["highlights"] = _visible_claims(lines[positions[1] + 1:positions[2]], "highlights", value["highlights"], value["date"], evidence_ids, "Chưa có điểm chính.")
    context_texts = [line[2 + len("Người dùng ghi: "):] for line in lines[positions[1] + 1:positions[2]] if line.startswith("- Người dùng ghi: ")]
    if len(context_texts) > 1 or any("\n" in text or "\r" in text for text in context_texts):
        raise ValueError("Report may contain only one line of user context")
    if context_texts:
        prior = value["user_context"][0] if value["user_context"] else {"id": str(uuid4()), "created_at": datetime.now().astimezone().isoformat()}
        value["user_context"] = [{**prior, "text": context_texts[0]}]
    else:
        value["user_context"] = []
    value["details"] = _visible_claims(lines[positions[2] + 1:positions[3]], "details", value["details"], value["date"], evidence_ids, "Phân tích chi tiết chưa khả dụng.")
    return _validate(value, date.fromisoformat(value["date"]))


def read_report(workspace: Path, report_date: date) -> tuple[dict, str]:
    path = workspace / "reports" / f"{report_date.isoformat()}.md"
    try:
        raw = path.read_bytes()
        parsed = raw.decode("utf-8")
    except FileNotFoundError:
        raise
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"Cannot read report Markdown: {path}") from exc
    return parse_report(parsed, report_date), _revision(raw)


def write_report(workspace: Path, report: dict, expected_revision: str) -> tuple[dict, str]:
    value = _validate(report)
    path = workspace / "reports" / f"{value['date']}.md"
    if path.exists():
        try:
            parse_report(path.read_text(encoding="utf-8"), date.fromisoformat(value["date"]))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            recovery = journal.preserve_draft(workspace, render_report(value).encode("utf-8"))
            raise ValueError(f"Existing report is malformed and was left untouched; candidate preserved at {recovery}") from exc
    candidate = render_report(value).encode("utf-8")
    revision = journal._safe_replace(path, candidate, expected_revision, workspace, f"report:{value['date']}")
    return value, revision


def list_report_dates(workspace: Path) -> list[str]:
    root = workspace / "reports"
    dates = []
    for path in root.glob("*.md") if root.exists() else []:
        try:
            day = date.fromisoformat(path.stem)
            dates.append(day.isoformat())
        except ValueError:
            continue
    return sorted(dates, reverse=True)


def read_report_conflict(workspace: Path, report_date: date, conflict_id: str) -> dict:
    value = journal.read_conflict(workspace, conflict_id, f"report:{report_date.isoformat()}")
    generated = parse_report(value["local_markdown"], report_date)
    external = parse_report(value["external_markdown"], report_date)
    return {
        "conflict_id": conflict_id, "date": report_date.isoformat(),
        "external_markdown": value["external_markdown"],
        "generated_report": generated, "external_report": external,
        "external_revision": value["current_revision"],
    }


def resolve_report_conflict(workspace: Path, report_date: date, conflict_id: str, report: dict, expected_revision: str) -> tuple[dict, str]:
    conflict = journal.read_conflict(workspace, conflict_id, f"report:{report_date.isoformat()}")
    if conflict["current_revision"].strip('"') != expected_revision.strip('"'):
        journal._safe_replace(
            workspace / "reports" / f"{report_date.isoformat()}.md",
            render_report(report).encode("utf-8"), expected_revision, workspace,
            f"report:{report_date.isoformat()}",
        )
    saved, revision = write_report(workspace, report, expected_revision)
    folder = workspace / ".commitly" / "conflicts" / f"report:{report_date.isoformat()}" / conflict_id
    for name in ("local.md", "external.md", "conflict.json"):
        (folder / name).unlink(missing_ok=True)
    folder.rmdir()
    return saved, revision


def keep_external_report_conflict(workspace: Path, report_date: date, conflict_id: str, expected_revision: str) -> tuple[dict, str]:
    conflict = journal.read_conflict(workspace, conflict_id, f"report:{report_date.isoformat()}")
    external = parse_report(conflict["external_markdown"], report_date)
    path = workspace / "reports" / f"{report_date.isoformat()}.md"
    revision = journal._safe_replace(
        path, conflict["external_markdown"].encode("utf-8"), expected_revision,
        workspace, f"report:{report_date.isoformat()}",
    )
    folder = workspace / ".commitly" / "conflicts" / f"report:{report_date.isoformat()}" / conflict_id
    for name in ("local.md", "external.md", "conflict.json"):
        (folder / name).unlink(missing_ok=True)
    folder.rmdir()
    return external, revision
