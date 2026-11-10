from uuid import uuid4

from commitly.journal import parse_journal, render_journal


def test_conflict_preserves_both_versions_until_successful_resolution(client, workspace) -> None:
    url = "/api/v1/journals/2026-11-10"
    initial = client.get(url)
    entry = {"id": str(uuid4()), "created_at": "2026-11-10T02:03:04Z", "date": "2026-11-10", "type": "work", "description": "Base"}
    saved = client.put(url, headers={"If-Match": initial.headers["etag"]}, json={"date": "2026-11-10", "entries": [entry]})
    path = workspace / "journals" / "2026-11-10.md"
    external = parse_journal(path.read_text(encoding="utf-8"))
    external["entries"][0]["description"] = "External edit"
    path.write_text(render_journal(external), encoding="utf-8")
    local = {**saved.json(), "entries": [{**entry, "description": "Local draft"}]}
    conflict = client.put(url, headers={"If-Match": saved.headers["etag"]}, json=local)
    assert conflict.status_code == 409
    payload = conflict.json()
    assert payload["local"]["entries"][0]["description"] == "Local draft"
    assert payload["external"]["entries"][0]["description"] == "External edit"
    folder = workspace / ".commitly" / "conflicts" / "2026-11-10" / payload["conflict_id"]
    assert (folder / "local.md").exists() and (folder / "external.md").exists()
    resolution = client.post(f"{url}/conflicts/{payload['conflict_id']}/resolve", headers={"If-Match": payload["current_revision"]}, json={"date": "2026-11-10", "entries": [entry]})
    assert resolution.status_code == 200
    assert not folder.exists()
    assert client.get(url).json()["entries"][0]["description"] == "Base"


def test_new_external_edit_during_resolution_creates_another_conflict(client, workspace) -> None:
    url = "/api/v1/journals/2026-11-10"
    initial = client.get(url)
    entry = {"id": str(uuid4()), "created_at": "2026-11-10T02:03:04Z", "date": "2026-11-10", "type": "work", "description": "Base"}
    saved = client.put(url, headers={"If-Match": initial.headers["etag"]}, json={"date": "2026-11-10", "entries": [entry]})
    path = workspace / "journals" / "2026-11-10.md"
    external = parse_journal(path.read_text(encoding="utf-8")); external["entries"][0]["description"] = "External one"; path.write_text(render_journal(external), encoding="utf-8")
    first = client.put(url, headers={"If-Match": saved.headers["etag"]}, json={"date": "2026-11-10", "entries": [{**entry, "description": "Local"}]})
    conflict = first.json()
    external["entries"][0]["description"] = "External two"; path.write_text(render_journal(external), encoding="utf-8")
    result = client.post(f"{url}/conflicts/{conflict['conflict_id']}/resolve", headers={"If-Match": conflict["current_revision"]}, json=conflict["local"])
    assert result.status_code == 409
    assert result.json()["external"]["entries"][0]["description"] == "External two"
