from __future__ import annotations

import subprocess
from datetime import date
import hashlib

from fastapi import Request, Response

from commitly.api import routes
from commitly.api.schemas import RefreshInput, RepositoryInput, UserContextInput
from commitly.app import create_app


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def test_selected_pushed_activity_becomes_offline_markdown_report(tmp_path):
    remote, repo = tmp_path / "remote.git", tmp_path / "source"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "user.email", "test@example.test")
    (repo / "logic.py").write_text("def result():\n    return 42\n", encoding="utf-8")
    git(repo, "add", "logic.py")
    git(repo, "commit", "-m", "Implement result")
    git(repo, "branch", "-M", "main")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")

    workspace = tmp_path / "journal"
    app = create_app(workspace=workspace, config_dir=tmp_path / "config", state_dir=tmp_path / "state")
    request = Request({"type": "http", "method": "POST", "path": "/api/v1", "headers": [], "query_string": b"", "server": ("testserver", 80), "client": ("test", 1), "scheme": "http", "app": app})
    day = date.today().isoformat()
    selected = routes.add_repository(RepositoryInput(path=str(repo)), request)
    assert selected["id"]
    refreshed = routes.refresh_activity(RefreshInput.model_validate({"from": day, "to": day}), request)
    assert refreshed["repositories"][0]["fetch_status"] == "success"
    routes.refresh_activity(RefreshInput.model_validate({"from": day, "to": day}), request)
    report_response = Response()
    report = routes.get_report(date.fromisoformat(day), request, report_response)
    assert report["analysis_status"] == "unavailable"
    assert "chưa khả dụng" in report["summary"]["text"]
    assert report["evidence"][0]["changed_paths"] == ["logic.py"]
    assert len(report["evidence"]) == 1
    assert (workspace / "reports" / f"{day}.md").exists()

    context_response = Response()
    context = routes.put_report_context(date.fromisoformat(day), UserContextInput(text="Đã kiểm tra logic đầu vào"), request, context_response, report_response.headers["etag"])
    assert context["user_context"][0]["text"] == "Đã kiểm tra logic đầu vào"
    rejected = routes.put_report_context(date.fromisoformat(day), UserContextInput(text="hai\ndòng"), request, Response(), context_response.headers["etag"])
    assert rejected.status_code == 422


def test_user_context_can_create_a_report_without_git_evidence(tmp_path):
    workspace = tmp_path / "journal"
    app = create_app(workspace=workspace, config_dir=tmp_path / "config", state_dir=tmp_path / "state")
    request = Request({"type": "http", "method": "PUT", "path": "/api/v1", "headers": [], "query_string": b"", "server": ("testserver", 80), "client": ("test", 1), "scheme": "http", "app": app})
    day = date.today()
    empty_revision = f'"{hashlib.sha256(b"").hexdigest()}"'

    result = routes.put_report_context(day, UserContextInput(text="Pairing session"), request, Response(), empty_revision)

    assert result["user_context"][0]["text"] == "Pairing session"
    assert result["evidence"] == []
    assert result["summary"]["evidence_ids"] == []
    assert (workspace / "reports" / f"{day.isoformat()}.md").exists()
