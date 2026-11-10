import socket
from uuid import uuid4


def test_core_journal_operations_need_no_network(client, monkeypatch) -> None:
    def blocked(*_args, **_kwargs):
        raise AssertionError("Core journal operations attempted a network connection")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    projects = client.get("/api/v1/projects")
    project = {"id": str(uuid4()), "name": "Offline", "created_at": "2026-11-10T02:00:00Z", "archived_at": None}
    saved_project = client.put("/api/v1/projects", headers={"If-Match": projects.headers["etag"]}, json=[project])
    day = "2026-11-10"; url = f"/api/v1/journals/{day}"
    journal = client.get(url)
    entry = {"id": str(uuid4()), "created_at": f"{day}T03:00:00Z", "date": day, "type": "work", "description": "Offline entry", "project_id": project["id"]}
    saved = client.put(url, headers={"If-Match": journal.headers["etag"]}, json={"date": day, "entries": [entry], "reflection": {"accomplishments": "Saved offline"}})
    assert saved.status_code == 200 and saved_project.status_code == 200
    assert client.get("/api/v1/entries/search", params={"q": "Offline"}).json()[0]["entry"]["id"] == entry["id"]
    deleted = client.put(url, headers={"If-Match": saved.headers["etag"]}, json={"date": day, "entries": []})
    assert deleted.status_code == 200


def test_write_requests_reject_non_loopback_hosts(client) -> None:
    response = client.put("/api/v1/journals/2026-11-10", headers={"Host": "example.com", "If-Match": '"empty"'}, json={"date": "2026-11-10", "entries": []})
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_host"
