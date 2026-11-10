import subprocess

from commitly.backup import run_backup
from commitly.config import update_backup_configuration


def _git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def test_backup_skips_empty_commit_and_retries_failed_push(workspace, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Commitly Test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "commitly-test@example.invalid")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Commitly Test")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "commitly-test@example.invalid")
    config_dir = tmp_path / "config"; state_dir = tmp_path / "state"; remote = tmp_path / "journal.git"
    update_backup_configuration({"enabled": True, "remote_url": str(remote), "branch": "main", "private_confirmed": True}, config_dir)
    (workspace / "journals").mkdir(parents=True)
    (workspace / "journals" / "2026-11-10.md").write_text("journal", encoding="utf-8")
    failed = run_backup(workspace, config_dir, state_dir)
    assert failed["last_error"] and failed["pending_commits"] == 1
    _git("init", "--bare", str(remote))
    succeeded = run_backup(workspace, config_dir, state_dir)
    assert succeeded["last_error"] is None
    assert succeeded["pending_commits"] == 0
    before = subprocess.run(["git", "--git-dir", str(remote), "rev-list", "--count", "main"], text=True, check=True, capture_output=True).stdout.strip()
    run_backup(workspace, config_dir, state_dir)
    after = subprocess.run(["git", "--git-dir", str(remote), "rev-list", "--count", "main"], text=True, check=True, capture_output=True).stdout.strip()
    assert before == after == "1"


def test_backup_requires_private_confirmation(workspace, tmp_path) -> None:
    update_backup_configuration({"enabled": False, "remote_url": "git@host:private/journal.git", "branch": "main", "private_confirmed": False}, tmp_path / "config")
    status = run_backup(workspace, tmp_path / "config", tmp_path / "state")
    assert status["enabled"] is False
    assert status["last_success_at"] is None


def test_backup_refuses_commitly_source_remote_even_with_an_alias(workspace, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("commitly.backup._source_remote_urls", lambda: {"https://github.com/commitly/commitly.git"})
    config_dir = tmp_path / "config"
    update_backup_configuration({"enabled": True, "remote_url": "git@github.com:Commitly/Commitly.git", "branch": "main", "private_confirmed": True}, config_dir)
    status = run_backup(workspace, config_dir, tmp_path / "state")
    assert status["last_error"] and "source repository" in status["last_error"]
    assert not (workspace / ".git").exists()
