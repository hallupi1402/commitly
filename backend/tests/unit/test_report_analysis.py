from __future__ import annotations

import json
from uuid import uuid4

import pytest

from commitly.report_analysis import AnalysisUnavailable, analyze


def test_analyzer_requires_claims_to_reference_real_evidence() -> None:
    evidence = [{"id": str(uuid4()), "commit_id": "a" * 40, "changed_paths": ["src/a.py"], "diff": "+return 2"}]
    result = {"summary": {"text": "Sửa kết quả tính toán.", "evidence_ids": [evidence[0]["id"]]}, "highlights": [], "details": []}
    output = analyze(evidence, lambda _prompt: json.dumps(result, ensure_ascii=False))
    assert output["summary"]["evidence_ids"] == [evidence[0]["id"]]


def test_missing_local_runtime_fails_closed() -> None:
    with pytest.raises(AnalysisUnavailable, match="[Ll]ocal model"):
        analyze([], None)


def test_rejects_claims_that_reference_unknown_evidence() -> None:
    evidence = [{"id": str(uuid4()), "commit_id": "a" * 40, "changed_paths": ["src/a.py"], "diff": "+return 2"}]
    response = {"summary": {"text": "Unsupported claim", "evidence_ids": [str(uuid4())]}, "highlights": [], "details": []}
    with pytest.raises(AnalysisUnavailable, match="valid evidence"):
        analyze(evidence, lambda _prompt: json.dumps(response))


def test_masks_common_credentials_before_analysis_and_report_output() -> None:
    evidence_id = str(uuid4())
    evidence = [{"id": evidence_id, "subject": "api_key=secret-value", "diff": "Bearer abc.def.ghi"}]
    seen = []
    response = {"summary": {"text": "api_key=secret-value", "evidence_ids": [evidence_id]}, "highlights": [], "details": []}
    result = analyze(evidence, lambda prompt: seen.append(prompt) or json.dumps(response))

    assert "secret-value" not in seen[0]
    assert "abc.def.ghi" not in seen[0]
    assert "secret-value" not in result["summary"]["text"]
