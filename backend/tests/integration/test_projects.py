from uuid import uuid4

from commitly.journal import read_journal, write_journal
from commitly.projects import read_projects, write_projects


def test_create_rename_archive_preserves_history_and_activity(client, workspace) -> None:
    response = client.get("/api/v1/projects")
    project = {"id": str(uuid4()), "name": "Commitly", "created_at": "2026-11-10T02:00:00Z", "archived_at": None}
    saved = client.put("/api/v1/projects", headers={"If-Match": response.headers["etag"]}, json=[project])
    assert saved.status_code == 200
    day = "2026-11-10"
    entry = {"id": str(uuid4()), "created_at": "2026-11-10T03:00:00Z", "date": day, "type": "blocker", "description": "Need access", "project_id": project["id"], "blocker": "Access required", "next_step": "Ask admin"}
    write_journal(workspace, {"date": day, "entries": [entry]}, read_journal(workspace, day)[1])
    renamed = {**project, "name": "Commitly Journal"}
    updated = client.put("/api/v1/projects", headers={"If-Match": saved.headers["etag"]}, json=[renamed])
    assert updated.status_code == 200
    assert client.get(f"/api/v1/projects/{project['id']}/activity").json()["project"]["name"] == "Commitly Journal"
    archived = {**renamed, "archived_at": "2026-11-10T04:00:00Z"}
    result = client.put("/api/v1/projects", headers={"If-Match": updated.headers["etag"]}, json=[archived])
    assert result.status_code == 200
    activity = client.get(f"/api/v1/projects/{project['id']}/activity").json()
    assert activity["entries"][0]["entry"]["id"] == entry["id"]
    assert activity["unresolved_blockers"][0]["entry"]["description"] == "Need access"


def test_project_names_are_unique_among_active_projects(workspace) -> None:
    empty, revision = read_projects(workspace)
    saved, revision = write_projects(workspace, [{"id": str(uuid4()), "name": "Core", "created_at": "2026-11-10T02:00:00Z", "archived_at": None}], revision)
    duplicate = [{**saved[0]}, {"id": str(uuid4()), "name": "core", "created_at": "2026-11-10T03:00:00Z", "archived_at": None}]
    try:
        write_projects(workspace, duplicate, revision)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate active project name was accepted")


def test_project_registry_external_edit_requires_explicit_resolution(client, workspace) -> None:
    response = client.get("/api/v1/projects")
    project = {"id": str(uuid4()), "name": "One", "created_at": "2026-11-10T02:00:00Z", "archived_at": None}
    saved = client.put("/api/v1/projects", headers={"If-Match": response.headers["etag"]}, json=[project])
    path = workspace / "projects.md"
    external = path.read_text(encoding="utf-8").replace("## One", "## External")
    path.write_text(external, encoding="utf-8")
    local = {**project, "name": "Local"}
    conflict = client.put("/api/v1/projects", headers={"If-Match": saved.headers["etag"]}, json=[local])
    assert conflict.status_code == 409
    value = conflict.json()
    assert value["local"][0]["name"] == "Local"
    assert value["external"][0]["name"] == "External"
    folder = workspace / ".commitly" / "conflicts" / "projects" / value["conflict_id"]
    assert (folder / "local.md").exists() and (folder / "external.md").exists()


def test_resolving_blocker_hides_summary_but_keeps_history(client, workspace) -> None:
    response = client.get("/api/v1/projects")
    project = {"id": str(uuid4()), "name": "Blocked", "created_at": "2026-11-10T02:00:00Z", "archived_at": None}
    saved_project = client.put("/api/v1/projects", headers={"If-Match": response.headers["etag"]}, json=[project])
    day = "2026-11-10"
    entry = {"id": str(uuid4()), "created_at": "2026-11-10T03:00:00Z", "date": day, "type": "blocker", "description": "Waiting", "project_id": project["id"], "blocker": "Access"}
    write_journal(workspace, {"date": day, "entries": [entry]}, read_journal(workspace, day)[1])
    url = f"/api/v1/journals/{day}"; current = client.get(url)
    updated_entry = {**entry, "blocker_resolved_at": "2026-11-10T04:00:00Z"}
    saved = client.put(url, headers={"If-Match": current.headers["etag"]}, json={"date": day, "entries": [updated_entry]})
    assert saved.status_code == 200
    activity = client.get(f"/api/v1/projects/{project['id']}/activity").json()
    assert activity["unresolved_blockers"] == []
    assert activity["entries"][0]["entry"]["id"] == entry["id"]
