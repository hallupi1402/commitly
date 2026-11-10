from uuid import uuid4


def _entry(description: str, entry_type: str = "work") -> dict:
    return {"id": str(uuid4()), "created_at": "2026-11-10T02:03:04Z", "date": "2026-11-10", "type": entry_type, "description": description}


def test_create_edit_delete_and_persist_entry(client, workspace) -> None:
    first = client.get("/api/v1/journals/2026-11-10")
    assert first.status_code == 200
    entry = _entry("Fixed parser startup")
    saved = client.put("/api/v1/journals/2026-11-10", headers={"If-Match": first.headers["etag"]}, json={"date": "2026-11-10", "entries": [entry]})
    assert saved.status_code == 200
    assert saved.json()["entries"][0]["type"] == "work"
    original_created = saved.json()["entries"][0]["created_at"]
    edited = {**saved.json()["entries"][0], "description": "Fixed parser startup and recovery"}
    updated = client.put("/api/v1/journals/2026-11-10", headers={"If-Match": saved.headers["etag"]}, json={"date": "2026-11-10", "entries": [edited]})
    assert updated.status_code == 200
    assert updated.json()["entries"][0]["id"] == entry["id"]
    assert updated.json()["entries"][0]["created_at"] == original_created
    assert (workspace / "journals" / "2026-11-10.md").exists()
    persisted = client.get("/api/v1/journals/2026-11-10")
    assert persisted.json()["entries"][0]["description"] == "Fixed parser startup and recovery"
    deleted = client.put("/api/v1/journals/2026-11-10", headers={"If-Match": persisted.headers["etag"]}, json={"date": "2026-11-10", "entries": []})
    assert deleted.status_code == 200
    assert deleted.json()["entries"] == []


def test_whitespace_description_is_rejected(client) -> None:
    response = client.put("/api/v1/journals/2026-11-10", headers={"If-Match": '"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"'}, json={"date": "2026-11-10", "entries": [_entry("  \n ")]})
    assert response.status_code == 422


def test_stale_revision_does_not_overwrite_saved_entry(client) -> None:
    first = client.get("/api/v1/journals/2026-11-10")
    entry = _entry("Saved version")
    saved = client.put("/api/v1/journals/2026-11-10", headers={"If-Match": first.headers["etag"]}, json={"date": "2026-11-10", "entries": [entry]})
    stale = client.put("/api/v1/journals/2026-11-10", headers={"If-Match": first.headers["etag"]}, json={"date": "2026-11-10", "entries": [_entry("Local draft")]})
    assert saved.status_code == 200
    assert stale.status_code == 409
    assert client.get("/api/v1/journals/2026-11-10").json()["entries"][0]["description"] == "Saved version"
