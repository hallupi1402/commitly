"""One-shot Git backup; the journal workspace has its own repository."""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from commitly import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _git(workspace: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", "-C", str(workspace), *args], text=True, capture_output=True, timeout=60, check=False)
    if check and result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "Git command failed").strip())
    return result


def _label(remote: str | None) -> str | None:
    if not remote:
        return None
    parsed = urlsplit(remote)
    if parsed.hostname:
        return f"{parsed.hostname}{parsed.path}"
    return re.sub(r"^[^@]+@", "", remote)


def _safe_remote(remote: str) -> None:
    if "\n" in remote or "\r" in remote or remote.startswith("-"):
        raise ValueError("Backup destination is invalid")
    parsed = urlsplit(remote)
    scp_style = re.fullmatch(r"(?:[^@/:]+@)?([^:/]+):(.+)", remote) is not None
    if parsed.scheme and parsed.scheme not in {"https", "ssh", "git", "file"} and not scp_style:
        raise ValueError("Use an HTTPS, SSH, Git, or local file destination")
    if parsed.password or (parsed.username and parsed.scheme not in {"ssh"}):
        raise ValueError("Do not put credentials in the backup URL; use the Git credential helper")


def _canonical_remote(remote: str) -> str:
    parsed = urlsplit(remote)
    if parsed.hostname:
        path = parsed.path.rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return f"{parsed.hostname.lower()}{path.casefold()}"
    scp = re.fullmatch(r"(?:[^@/:]+@)?([^:/]+):(.+)", remote)
    if scp:
        path = scp.group(2).rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return f"{scp.group(1).lower()}/{path.casefold()}"
    return str(Path(remote).expanduser().resolve())


def status_for(workspace: Path, config_dir: Path | None = None, state_dir: Path | None = None) -> dict:
    cfg = config.get_backup_configuration(config_dir)
    state = config.read_backup_status((state_dir or config.state_dir()) / "backup-status.json")
    return {
        "enabled": bool(cfg["enabled"]),
        "configured": bool(cfg.get("remote_url")),
        "destination_label": _label(cfg.get("remote_url")),
        "private_confirmed": bool(cfg["private_confirmed"]),
        "branch": cfg.get("branch", "main"),
        "last_attempt_at": state.get("last_attempt_at"),
        "last_success_at": state.get("last_success_at"),
        "pending_commits": max(0, int(state.get("pending_commits", 0))),
        "last_error": state.get("last_error"),
    }


def _save_state(status: dict, state_dir: Path | None) -> None:
    config.write_backup_status(status, (state_dir or config.state_dir()) / "backup-status.json")


def _source_remote_urls() -> set[str]:
    root = config.source_root()
    result = subprocess.run(["git", "-C", str(root), "remote"], text=True, capture_output=True, check=False)
    if result.returncode:
        return set()
    urls: set[str] = set()
    for name in result.stdout.splitlines():
        value = subprocess.run(["git", "-C", str(root), "remote", "get-url", "--all", name], text=True, capture_output=True, check=False)
        urls.update(line.strip() for line in value.stdout.splitlines() if line.strip())
    return urls


def _ensure_repository(workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["git", "-C", str(workspace), "rev-parse", "--show-toplevel"], text=True, capture_output=True, check=False)
    if result.returncode or Path(result.stdout.strip()).resolve() != workspace.resolve():
        _git(workspace, "init")


def _switch_branch(workspace: Path, branch: str) -> None:
    checked = _git(workspace, "check-ref-format", "--branch", branch, check=False)
    if checked.returncode:
        raise ValueError("Backup branch name is not valid")
    current = _git(workspace, "branch", "--show-current", check=False).stdout.strip()
    if current == branch:
        return
    exists = _git(workspace, "show-ref", "--verify", f"refs/heads/{branch}", check=False).returncode == 0
    _git(workspace, "switch", branch if exists else "--create", *( () if exists else (branch,) ))


def _pending_count(workspace: Path, state: dict) -> int:
    head = _git(workspace, "rev-parse", "HEAD", check=False)
    if head.returncode:
        return 0
    last = state.get("last_pushed_revision")
    if last and _git(workspace, "cat-file", "-e", f"{last}^{{commit}}", check=False).returncode == 0:
        ahead = _git(workspace, "rev-list", "--count", f"{last}..HEAD", check=False)
        if ahead.returncode == 0:
            return int(ahead.stdout.strip() or 0)
    total = _git(workspace, "rev-list", "--count", "HEAD", check=False)
    return int(total.stdout.strip() or 0) if total.returncode == 0 else 0


def run_backup(workspace: Path | None = None, config_path: Path | None = None, state_path: Path | None = None) -> dict:
    workspace = config.resolve_workspace(workspace)
    cfg = config.get_backup_configuration(config_path)
    state = config.read_backup_status((state_path or config.state_dir()) / "backup-status.json")
    state["last_attempt_at"] = _now()
    state["last_error"] = None
    if not cfg["enabled"] or not cfg.get("remote_url") or not cfg["private_confirmed"]:
        state["pending_commits"] = int(state.get("pending_commits", 0))
        _save_state(state, state_path)
        return status_for(workspace, config_path, state_path)

    remote = cfg["remote_url"]
    try:
        _safe_remote(remote)
        source_remotes = {_canonical_remote(item) for item in _source_remote_urls()}
        if _canonical_remote(remote) in source_remotes:
            raise ValueError("The backup destination matches a Commitly source repository remote; choose a private journal destination")
        _ensure_repository(workspace)
        _switch_branch(workspace, cfg["branch"])
        existing = _git(workspace, "remote", "get-url", "commitly-backup", check=False)
        if existing.returncode:
            _git(workspace, "remote", "add", "commitly-backup", remote)
        elif existing.stdout.strip() != remote:
            _git(workspace, "remote", "set-url", "commitly-backup", remote)
        dirty = _git(workspace, "status", "--porcelain", "--untracked-files=all", "--", "journals", "projects.md").stdout
        if dirty.strip():
            paths = []
            if (workspace / "journals").exists():
                paths.append("journals")
            if (workspace / "projects.md").exists() or _git(workspace, "ls-files", "--error-unmatch", "projects.md", check=False).returncode == 0:
                paths.append("projects.md")
            _git(workspace, "add", "--", *paths)
            staged = _git(workspace, "diff", "--cached", "--quiet", check=False).returncode != 0
            if staged:
                _git(workspace, "commit", "-m", f"Journal backup {_now()}")
        head = _git(workspace, "rev-parse", "HEAD", check=False)
        if head.returncode:
            state["pending_commits"] = 0
            _save_state(state, state_path)
            return status_for(workspace, config_path, state_path)
        branch = cfg["branch"]
        _git(workspace, "push", "commitly-backup", f"{branch}:refs/heads/{branch}")
        state["last_success_at"] = _now()
        state["last_pushed_revision"] = head.stdout.strip()
        state["pending_commits"] = 0
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        message = str(exc)
        if remote:
            message = message.replace(remote, _label(remote) or "configured destination")
        state["last_error"] = message[:1000]
        state["pending_commits"] = _pending_count(workspace, state) if (workspace / ".git").exists() else int(state.get("pending_commits", 0))
    _save_state(state, state_path)
    return status_for(workspace, config_path, state_path)


def main() -> int:
    try:
        status = run_backup()
    except Exception as exc:
        print(f"Commitly backup failed: {exc}")
        return 1
    if status["last_error"]:
        print(f"Commitly backup failed: {status['last_error']}")
        return 1
    if not status["enabled"]:
        print("Commitly backup is not configured; no push was attempted.")
    else:
        print("Commitly backup completed.")
    return 0
