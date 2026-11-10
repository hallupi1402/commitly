from datetime import date
from uuid import uuid4

import pytest

from commitly.journal import JournalFormatError, parse_journal, render_journal, validate_journal


def test_markdown_round_trip_preserves_optional_entry_fields() -> None:
    record = {
        "date": "2026-11-10",
        "entries": [{
            "id": str(uuid4()), "created_at": "2026-11-10T02:03:04Z", "date": "2026-11-10",
            "type": "work", "description": "Fixed startup.\n\nKept the parser intact.",
            "project_id": None, "tags": ["backend"], "result": "Clean startup",
            "blocker": None, "blocker_resolved_at": None, "next_step": "Add a test",
            "references": ["issue-1"], "notes": "**Details**",
        }],
        "reflection": {"accomplishments": "Done", "blockers": None, "next_steps": "Review"},
    }
    assert parse_journal(render_journal(record), date(2026, 11, 10)) == validate_journal(record, date(2026, 11, 10))


def test_markdown_round_trip_preserves_user_headings_and_backslashes() -> None:
    record = {
        "date": "2026-11-10",
        "entries": [{"id": str(uuid4()), "created_at": "2026-11-10T02:03:04Z", "type": "work",
                     "description": "### Result\n\\### Notes", "notes": "### Blocker"}],
        "reflection": {"accomplishments": "### Next steps"},
    }
    assert parse_journal(render_journal(record)) == validate_journal(record)


@pytest.mark.parametrize("raw", [
    "not a Commitly journal",
    "<!-- commitly:journal v2 date=2026-11-10 -->\n# Future\n",
    '<!-- commitly:journal v1 date=2026-11-10 -->\n<!-- commitly:entry {"id":"bad"} -->\n',
])
def test_malformed_or_unsupported_markdown_is_rejected(raw: str) -> None:
    with pytest.raises(JournalFormatError):
        parse_journal(raw, date(2026, 11, 10))


def test_duplicate_entry_ids_are_rejected() -> None:
    entry_id = str(uuid4())
    entry = {"id": entry_id, "created_at": "2026-11-10T02:03:04Z", "date": "2026-11-10", "type": "work", "description": "Done"}
    with pytest.raises(JournalFormatError):
        parse_journal(render_journal({"date": "2026-11-10", "entries": [entry, entry]}))


def test_equal_timestamps_have_stable_id_order() -> None:
    entries = [
        {"id": str(uuid4()), "created_at": "2026-11-10T02:03:04Z", "date": "2026-11-10", "type": "work", "description": "B"},
        {"id": str(uuid4()), "created_at": "2026-11-10T02:03:04Z", "date": "2026-11-10", "type": "work", "description": "A"},
    ]
    parsed = parse_journal(render_journal({"date": "2026-11-10", "entries": entries}))
    assert [e["id"] for e in parsed["entries"]] == sorted(e["id"] for e in entries)
