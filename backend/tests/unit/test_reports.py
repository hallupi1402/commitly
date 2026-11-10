from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from commitly.journal import JournalConflictError
from commitly.reports import keep_external_report_conflict, read_report, read_report_conflict, render_report, resolve_report_conflict, write_report


def report(day: date) -> dict:
    evidence_id = str(uuid4())
    return {
        "date": day.isoformat(),
        "summary": {"id": str(uuid4()), "text": "Sửa luồng lưu báo cáo.", "evidence_ids": [evidence_id], "certainty": "supported"},
        "highlights": [], "details": [], "evidence": [{
            "id": evidence_id, "repository_id": "repo", "repository_name": "sample",
            "repository_path": "/tmp/sample", "commit_id": "a" * 40,
            "authored_at": "2026-01-02T03:04:05+07:00", "subject": "Fix report save",
            "changed_paths": ["src/save.py"], "added_lines": 2, "deleted_lines": 1,
            "analysis_status": "complete", "analysis_note": None,
        }], "user_context": [], "analysis_status": "complete",
    }


def test_report_round_trips_as_markdown_and_preserves_revision(tmp_path) -> None:
    workspace = tmp_path / "journal"
    original = report(date(2026, 1, 2))
    saved, revision = write_report(workspace, original, '"' + __import__("hashlib").sha256(b"").hexdigest() + '"')
    loaded, loaded_revision = read_report(workspace, date(2026, 1, 2))

    assert saved == original
    assert loaded == original
    assert loaded_revision == revision
    assert "## Tóm tắt" in (workspace / "reports" / "2026-01-02.md").read_text(encoding="utf-8")
    assert "## Log nguồn" in (workspace / "reports" / "2026-01-02.md").read_text(encoding="utf-8")


def test_external_markdown_edit_is_preserved_as_conflict(tmp_path) -> None:
    workspace = tmp_path / "journal"
    candidate = report(date(2026, 1, 2))
    _, revision = write_report(workspace, candidate, '"' + __import__("hashlib").sha256(b"").hexdigest() + '"')
    path = workspace / "reports" / "2026-01-02.md"
    external = report(date(2026, 1, 2))
    external["summary"]["text"] = "External note."
    path.write_text(render_report(external), encoding="utf-8")

    with pytest.raises(JournalConflictError):
        write_report(workspace, candidate, revision)

    assert "External note." in path.read_text(encoding="utf-8")
    assert list((workspace / ".commitly" / "conflicts" / "report:2026-01-02").glob("*/conflict.json"))


def test_new_external_edit_during_resolution_creates_another_conflict(tmp_path) -> None:
    workspace = tmp_path / "journal"
    candidate = report(date(2026, 1, 2))
    _, revision = write_report(workspace, candidate, '"' + __import__("hashlib").sha256(b"").hexdigest() + '"')
    path = workspace / "reports" / "2026-01-02.md"
    external = report(date(2026, 1, 2))
    external["summary"]["text"] = "External edit one."
    path.write_text(render_report(external), encoding="utf-8")
    with pytest.raises(JournalConflictError) as first:
        write_report(workspace, candidate, revision)
    first_conflict = read_report_conflict(workspace, date(2026, 1, 2), first.value.conflict_id)
    external["summary"]["text"] = "External edit two."
    path.write_text(render_report(external), encoding="utf-8")

    with pytest.raises(JournalConflictError) as second:
        resolve_report_conflict(workspace, date(2026, 1, 2), first.value.conflict_id, candidate, first_conflict["external_revision"])

    assert second.value.conflict_id != first.value.conflict_id
    assert "External edit two." in path.read_text(encoding="utf-8")


def test_keep_external_conflict_preserves_the_exact_markdown_body(tmp_path) -> None:
    workspace = tmp_path / "journal"
    candidate = report(date(2026, 1, 2))
    _, revision = write_report(workspace, candidate, '"' + __import__("hashlib").sha256(b"").hexdigest() + '"')
    path = workspace / "reports" / "2026-01-02.md"
    external = report(date(2026, 1, 2))
    external["summary"]["text"] = "My edited explanation."
    path.write_text(render_report(external), encoding="utf-8")
    with pytest.raises(JournalConflictError) as first:
        write_report(workspace, candidate, revision)
    conflict = read_report_conflict(workspace, date(2026, 1, 2), first.value.conflict_id)

    keep_external_report_conflict(workspace, date(2026, 1, 2), first.value.conflict_id, conflict["external_revision"])

    assert "My edited explanation." in path.read_text(encoding="utf-8")


def test_unstructured_external_body_edit_is_not_overwritten(tmp_path) -> None:
    workspace = tmp_path / "journal"
    candidate = report(date(2026, 1, 2))
    _, revision = write_report(workspace, candidate, '"' + __import__("hashlib").sha256(b"").hexdigest() + '"')
    path = workspace / "reports" / "2026-01-02.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nUnstructured external text.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Existing report is malformed"):
        write_report(workspace, candidate, revision)

    assert "Unstructured external text." in path.read_text(encoding="utf-8")
    assert list((workspace / ".commitly" / "recovery").glob("*.md"))


def test_visible_markdown_edit_is_imported_and_persisted(tmp_path) -> None:
    workspace = tmp_path / "journal"
    original = report(date(2026, 1, 2))
    write_report(workspace, original, '"' + __import__("hashlib").sha256(b"").hexdigest() + '"')
    path = workspace / "reports" / "2026-01-02.md"
    visible = path.read_text(encoding="utf-8").replace("Sửa luồng lưu báo cáo.", "Hoàn thiện lưu báo cáo.", 1)
    path.write_text(visible, encoding="utf-8")

    edited, external_revision = read_report(workspace, date(2026, 1, 2))
    write_report(workspace, edited, external_revision)

    assert edited["summary"]["text"] == "Hoàn thiện lưu báo cáo."
    assert read_report(workspace, date(2026, 1, 2))[0]["summary"]["text"] == "Hoàn thiện lưu báo cáo."
