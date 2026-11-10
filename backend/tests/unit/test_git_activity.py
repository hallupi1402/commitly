from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

from commitly.git_activity import fetch_remote, inspect_repository, read_remote_activity


def git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def test_reads_only_matching_commits_reachable_from_selected_remote(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    git(repo, "config", "user.name", "Journal User")
    git(repo, "config", "user.email", "journal@example.test")
    (repo / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    (repo / "notes.md").write_text("The function returns the computed answer.\n", encoding="utf-8")
    git(repo, "add", "app.py", "notes.md")
    git(repo, "commit", "-m", "Add answer")
    git(repo, "branch", "-M", "main")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")

    selected = inspect_repository(repo, "origin")
    items = read_remote_activity(selected, date.today(), date.today(), fetch=False)

    assert selected["author_email"] == "journal@example.test"
    assert len(items) == 1
    assert items[0]["subject"] == "Add answer"
    assert items[0]["changed_paths"] == ["app.py", "notes.md"]
    assert items[0]["added_lines"] == 3
    assert items[0]["deleted_lines"] == 0
    assert "def answer" in items[0]["diff"]
    assert items[0]["documents"] == [{"path": "notes.md", "text": "The function returns the computed answer.\n"}]


def test_unpushed_commit_is_not_reported(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    git(repo, "config", "user.email", "journal@example.test")
    git(repo, "config", "user.name", "Journal User")
    (repo / "first.txt").write_text("first\n", encoding="utf-8")
    git(repo, "add", "first.txt")
    git(repo, "commit", "-m", "Pushed")
    git(repo, "branch", "-M", "main")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    (repo / "local.txt").write_text("local\n", encoding="utf-8")
    git(repo, "add", "local.txt")
    git(repo, "commit", "-m", "Not pushed")

    items = read_remote_activity(inspect_repository(repo, "origin"), date.today(), date.today(), fetch=False)

    assert [item["subject"] for item in items] == ["Pushed"]


def test_failed_fetch_uses_cached_remote_refs(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    git(repo, "config", "user.email", "journal@example.test")
    git(repo, "config", "user.name", "Journal User")
    (repo / "work.txt").write_text("local\n", encoding="utf-8")
    git(repo, "add", "work.txt")
    git(repo, "commit", "-m", "Cached commit")
    git(repo, "branch", "-M", "main")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    selected = inspect_repository(repo, "origin")
    remote.rename(tmp_path / "offline.git")

    status, message = fetch_remote(selected)
    items = read_remote_activity(selected, date.today(), date.today(), fetch=False)

    assert status == "cached"
    assert message and "cached" in message
    assert [item["subject"] for item in items] == ["Cached commit"]


def test_binary_commit_keeps_path_and_marks_line_counts_unknown(tmp_path: Path) -> None:
    remote, repo = tmp_path / "remote.git", tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    git(repo, "config", "user.email", "journal@example.test")
    git(repo, "config", "user.name", "Journal User")
    (repo / "image.bin").write_bytes(b"\x00\x01\x02")
    git(repo, "add", "image.bin")
    git(repo, "commit", "-m", "Add binary fixture")
    git(repo, "branch", "-M", "main")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")

    item = read_remote_activity(inspect_repository(repo, "origin"), date.today(), date.today(), fetch=False)[0]

    assert item["changed_paths"] == ["image.bin"]
    assert item["added_lines"] is None and item["deleted_lines"] is None
    assert item["document_errors"][0]["error"].startswith("Binary change")
