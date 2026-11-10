from uuid import uuid4

from commitly.journal import read_journal, write_journal


def test_search_filters_all_expected_entries_across_one_thousand_records(client, workspace) -> None:
    date = "2026-11-10"
    entries = []
    for index in range(1000):
        entries.append({"id": str(uuid4()), "created_at": f"2026-11-10T00:{index // 60:02d}:{index % 60:02d}Z", "date": date, "type": "work" if index % 2 == 0 else "note", "description": f"Seed record {index} commitlyneedle" if index % 17 == 0 else f"Seed record {index}"})
    write_journal(workspace, {"date": date, "entries": entries}, read_journal(workspace, date)[1])
    response = client.get("/api/v1/entries/search", params={"q": "commitlyneedle"})
    assert response.status_code == 200
    assert len(response.json()) == 59
    filtered = client.get("/api/v1/entries/search", params={"type": "note"})
    assert len(filtered.json()) == 500


def test_empty_search_and_date_range(client) -> None:
    response = client.get("/api/v1/entries/search", params={"q": "no such entry", "from": "2026-11-10", "to": "2026-11-10"})
    assert response.status_code == 200
    assert response.json() == []
