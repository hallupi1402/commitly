from datetime import date
from pathlib import Path

import pytest

from commitly.journal import JournalConflictError, SafeWriteError, read_journal, write_journal


def _doc() -> dict:
    return {"date": "2026-11-10", "entries": [], "reflection": None}


def test_atomic_create_and_update_keep_previous_data_on_failed_write(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first, revision = write_journal(workspace, _doc(), read_journal(workspace, date(2026, 11, 10))[1])
    assert read_journal(workspace, date(2026, 11, 10))[0] == first
    monkeypatch.setattr("commitly.journal._renameat2", lambda *_: (_ for _ in ()).throw(SafeWriteError("unsupported")))
    with pytest.raises(OSError):
        write_journal(workspace, {**_doc(), "entries": []}, revision)
    assert read_journal(workspace, date(2026, 11, 10))[0] == first
    assert list((workspace / ".commitly" / "recovery").glob("*.md"))


def test_external_change_returns_recoverable_conflict(workspace: Path) -> None:
    _, revision = write_journal(workspace, _doc(), read_journal(workspace, date(2026, 11, 10))[1])
    path = workspace / "journals" / "2026-11-10.md"
    path.write_text(path.read_text().replace("# Daily Journal", "# Externally edited journal"), encoding="utf-8")
    with pytest.raises(JournalConflictError) as caught:
        write_journal(workspace, {**_doc(), "entries": []}, revision)
    assert (workspace / ".commitly" / "conflicts" / "2026-11-10" / caught.value.conflict_id / "local.md").exists()
    assert path.read_text(encoding="utf-8").startswith("<!-- commitly:journal v1")


def test_missing_target_uses_no_replace(workspace: Path) -> None:
    _, revision = read_journal(workspace, date(2026, 11, 10))
    write_journal(workspace, _doc(), revision)
    assert (workspace / "journals" / "2026-11-10.md").exists()


def test_atomic_exchange_error_preserves_original_and_candidate(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first, revision = write_journal(workspace, _doc(), read_journal(workspace, date(2026, 11, 10))[1])
    monkeypatch.setattr("commitly.journal._renameat2", lambda *_: (_ for _ in ()).throw(OSError(5, "I/O error")))
    with pytest.raises(SafeWriteError, match="draft was preserved"):
        write_journal(workspace, {**_doc(), "reflection": {"accomplishments": "Draft"}}, revision)
    assert read_journal(workspace, date(2026, 11, 10))[0] == first
    assert len(list((workspace / ".commitly" / "recovery").glob("*.md"))) == 1


def test_malformed_external_file_stays_untouched_and_draft_is_recoverable(workspace: Path) -> None:
    day = date(2026, 11, 10)
    _, revision = write_journal(workspace, _doc(), read_journal(workspace, day)[1])
    path = workspace / "journals" / "2026-11-10.md"
    path.write_text("broken external file", encoding="utf-8")
    with pytest.raises(ValueError, match="draft is preserved"):
        write_journal(workspace, _doc(), revision)
    assert path.read_text(encoding="utf-8") == "broken external file"
    assert list((workspace / ".commitly" / "recovery").glob("*.md"))
