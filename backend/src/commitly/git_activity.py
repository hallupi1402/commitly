"""Bounded, read-only evidence collection from explicitly selected Git remotes."""

from __future__ import annotations

import hashlib
import subprocess
from datetime import date, datetime
from pathlib import Path

from commitly.document_text import DocumentTextError, extract_document_text

class GitActivityError(ValueError):
    pass


def _git(path: str | Path, *args: str, timeout: int = 20) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitActivityError("Git could not complete the requested operation") from exc
    if result.returncode:
        # Git diagnostics can contain remote URLs, including embedded credentials.
        raise GitActivityError("Git repository or selected remote is unavailable")
    return result.stdout


def inspect_repository(path: str | Path, remote_name: str | None = None) -> dict:
    repo_path = Path(path).expanduser().resolve()
    root = Path(_git(repo_path, "rev-parse", "--show-toplevel").strip()).resolve()
    common = Path(_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()).resolve()
    remotes = _git(root, "remote").splitlines()
    remote = remote_name or ("origin" if "origin" in remotes else (remotes[0] if len(remotes) == 1 else None))
    if not remote or remote not in remotes or any(c.isspace() for c in remote):
        raise GitActivityError("Choose a configured Git remote")
    email = _git(root, "config", "--get", "user.email").strip()
    if not email:
        raise GitActivityError("Set user.email in this repository to filter your commits")
    identifier = hashlib.sha256(str(common).encode("utf-8")).hexdigest()[:24]
    return {
        "id": identifier, "path": str(root), "display_name": root.name,
        "remote_name": remote, "author_email": email,
        "common_dir": str(common),
    }


def read_remote_activity(
    repository: dict, start: date, end: date, *, fetch: bool = True,
    max_diff_chars: int = 12000,
) -> list[dict]:
    """Read commits reachable from the selected remote-tracking refs only."""
    root = repository["path"]
    remote = repository["remote_name"]
    refs = _git(root, "for-each-ref", "--format=%(refname)", f"refs/remotes/{remote}/").splitlines()
    refs = [ref for ref in refs if not ref.endswith("/HEAD")]
    if fetch:
        try:
            _git(root, "fetch", "--no-tags", remote, timeout=45)
            refs = _git(root, "for-each-ref", "--format=%(refname)", f"refs/remotes/{remote}/").splitlines()
            refs = [ref for ref in refs if not ref.endswith("/HEAD")]
        except GitActivityError:
            if not refs:
                raise
    if not refs:
        return []
    log = _git(root, "log", "--format=%H%x00%aI%x00%ae%x00%s%x1e", *refs)
    items = []
    for record in log.split("\x1e"):
        fields = record.strip("\n").split("\x00", 3)
        if len(fields) != 4 or fields[2].casefold() != repository["author_email"].casefold():
            continue
        commit, authored_at, _email, subject = fields
        timestamp = datetime.fromisoformat(authored_at)
        if not start <= timestamp.astimezone().date() <= end:
            continue
        numstat = _git(root, "diff-tree", "--root", "--no-commit-id", "-r", "--numstat", "-z", "--no-renames", commit)
        changed_paths: list[str] = []
        added = deleted = 0
        stats_known = True
        document_errors = []
        for record in numstat.split("\0"):
            if not record:
                continue
            parts = record.split("\t", 2)
            if len(parts) != 3:
                continue
            add_text, delete_text, path = parts
            changed_paths.append(path)
            if add_text.isdigit() and delete_text.isdigit():
                added += int(add_text)
                deleted += int(delete_text)
            else:
                stats_known = False
                document_errors.append({"path": path, "error": "Binary change; semantic content is unsupported"})
        diff = _git(root, "show", "--format=", "--no-ext-diff", "--no-color", "--unified=3", "--no-renames", commit)
        documents = []
        for path in changed_paths:
            if Path(path).suffix.casefold() not in {".md", ".markdown", ".txt", ".rst", ".pdf"}:
                continue
            if len(documents) >= 3:
                document_errors.append({"path": path, "error": "Only the first three changed documents are analyzed per commit"})
                continue
            try:
                content = subprocess.run(["git", "-C", root, "show", f"{commit}:{path}"], capture_output=True, timeout=15, check=False)
                if content.returncode:
                    raise DocumentTextError("Changed document content is unavailable")
                documents.append({"path": path, "text": extract_document_text(path, content.stdout)})
            except (OSError, subprocess.TimeoutExpired, DocumentTextError) as exc:
                document_errors.append({"path": path, "error": str(exc)})
        items.append({
            "commit_id": commit, "authored_at": authored_at, "subject": subject,
            "changed_paths": changed_paths, "added_lines": added if stats_known else None,
            "deleted_lines": deleted if stats_known else None, "diff": diff[:max_diff_chars],
            "documents": documents, "document_errors": document_errors,
        })
    items.sort(key=lambda item: (item["authored_at"], item["commit_id"]))
    return items


def fetch_remote(repository: dict) -> tuple[str, str | None]:
    """Fetch only the chosen remote; report cached refs when offline."""
    root, remote = repository["path"], repository["remote_name"]
    before = _git(root, "for-each-ref", "--format=%(refname)", f"refs/remotes/{remote}/").splitlines()
    try:
        _git(root, "fetch", "--no-tags", remote, timeout=45)
        return "success", None
    except GitActivityError:
        return ("cached", "Fetch failed; using previously cached remote refs") if before else ("failed", "Fetch failed and no cached remote refs are available")
