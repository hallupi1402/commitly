from datetime import date, timedelta
from uuid import uuid4

from commitly.journal import read_journal, render_journal, write_journal


def test_today_shows_five_newest_prior_steps_and_unresolved_blockers(client, workspace) -> None:
    today = date.today()
    for offset in range(1, 8):
        day = (today - timedelta(days=offset)).isoformat()
        entry = {"id": str(uuid4()), "created_at": f"{day}T12:00:00Z", "date": day, "type": "blocker" if offset <= 6 else "work", "description": f"Entry {offset}", "next_step": f"Step {offset}", "blocker": f"Block {offset}" if offset <= 6 else None}
        write_journal(workspace, {"date": day, "entries": [entry]}, read_journal(workspace, day)[1])
    response = client.get("/api/v1/today")
    assert response.status_code == 200
    assert len([entry for group in response.json()["previous_context"] for entry in group["next_steps"]]) == 5
    assert len([entry for group in response.json()["previous_context"] for entry in group["blockers"]]) == 5
    assert all(group["source_date"] < today.isoformat() for group in response.json()["previous_context"])


def test_reflection_is_optional_and_editable(client) -> None:
    day = date.today().isoformat(); url = f"/api/v1/journals/{day}"
    first = client.get(url)
    assert first.json()["reflection"] is None
    saved = client.put(url, headers={"If-Match": first.headers["etag"]}, json={"date": day, "entries": [], "reflection": {"accomplishments": "Shipped", "blockers": None, "next_steps": "Review"}})
    assert saved.status_code == 200
    changed = client.put(url, headers={"If-Match": saved.headers["etag"]}, json={"date": day, "entries": [], "reflection": {"accomplishments": "Shipped more", "blockers": None, "next_steps": None}})
    assert changed.json()["reflection"]["accomplishments"] == "Shipped more"


def test_today_reports_malformed_prior_journal_with_path(client, workspace) -> None:
    prior = date.today() - timedelta(days=1)
    path = workspace / "journals" / f"{prior.isoformat()}.md"
    path.parent.mkdir(parents=True)
    path.write_text("malformed", encoding="utf-8")
    response = client.get("/api/v1/today")
    assert response.status_code == 422
    assert str(path) in response.json()["message"]
    assert path.read_text(encoding="utf-8") == "malformed"
