"""Markdown project registry operations."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from commitly.journal import JournalConflictError, JournalFormatError, _revision, _safe_replace, _timestamp, entry_sort_key, parse_journal, preserve_draft, read_conflict

_HEADER = "<!-- commitly:projects v1 -->"
_PROJECT = re.compile(r'^<!-- commitly:project (\{.*\}) -->\n## (.*?)\n<!-- /commitly:project ([0-9a-f-]+) -->$', re.M | re.S)


def render_projects(projects: list[dict]) -> str:
    checked = validate_projects(projects)
    lines = [_HEADER, "# Projects", ""]
    for project in checked:
        meta = {key: project[key] for key in ("id", "created_at", "archived_at")}
        lines.extend([
            f"<!-- commitly:project {json.dumps(meta, ensure_ascii=False, separators=(',', ':'))} -->",
            f"## {project['name']}",
            f"<!-- /commitly:project {project['id']} -->",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def validate_projects(projects: list[dict]) -> list[dict]:
    if not isinstance(projects, list):
        raise JournalFormatError("Project registry must be a list")
    result = []
    names = set()
    ids = set()
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for item in projects:
        if not isinstance(item, dict):
            raise JournalFormatError("Project must be an object")
        try:
            project_id = str(UUID(item.get("id") or uuid4()))
            created_at = _timestamp(item.get("created_at") or now)
            archived_at = item.get("archived_at")
            if archived_at is not None:
                archived_at = _timestamp(archived_at)
        except (ValueError, TypeError) as exc:
            raise JournalFormatError(str(exc)) from exc
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise JournalFormatError("Project name is required after trimming")
        name = name.strip()
        if "\n" in name or "\r" in name or "<!--" in name or "-->" in name:
            raise JournalFormatError("Project name must fit on one Markdown heading line")
        if project_id in ids:
            raise JournalFormatError("Project registry contains duplicate IDs")
        ids.add(project_id)
        if archived_at is None:
            folded = name.casefold()
            if folded in names:
                raise JournalFormatError("Active project names must be unique, case-insensitively")
            names.add(folded)
        result.append({"id": project_id, "name": name, "created_at": created_at, "archived_at": archived_at})
    return result


def parse_projects(raw: str, path: Path | None = None) -> list[dict]:
    try:
        lines = raw.splitlines()
        if not lines or lines[0] != _HEADER:
            raise JournalFormatError("Missing or malformed project registry header")
        if len(lines) < 2 or lines[1] != "# Projects":
            raise JournalFormatError("Missing project registry title")
        tail = "\n".join(lines[2:])
        projects = []
        matches = list(_PROJECT.finditer(tail))
        if _PROJECT.sub("", tail).strip():
            raise JournalFormatError("Project registry contains unsupported content")
        for match in matches:
            meta = json.loads(match.group(1))
            if not isinstance(meta, dict) or not {"id", "created_at", "archived_at"}.issubset(meta):
                raise JournalFormatError("Project metadata is incomplete")
            if set(meta) != {"id", "created_at", "archived_at"}:
                raise JournalFormatError("Project metadata contains unsupported fields")
            if match.group(3) != str(meta["id"]):
                raise JournalFormatError("Project closing marker ID does not match metadata")
            projects.append({**meta, "name": match.group(2)})
        return validate_projects(projects)
    except (JournalFormatError, json.JSONDecodeError, ValueError, TypeError) as exc:
        raise JournalFormatError(str(exc), path) from exc


def read_projects(workspace: Path) -> tuple[list[dict], str]:
    path = workspace / "projects.md"
    if not path.exists():
        return [], f'"{_revision(b"")}"'
    raw = path.read_bytes()
    try:
        parsed = parse_projects(raw.decode("utf-8"), path)
    except UnicodeDecodeError as exc:
        raise JournalFormatError("Project registry is not valid UTF-8; copy and repair the original file", path) from exc
    return parsed, f'"{_revision(raw)}"'


def write_projects(workspace: Path, projects: list[dict], revision: str) -> tuple[list[dict], str]:
    checked = validate_projects(projects)
    path = workspace / "projects.md"
    payload = render_projects(checked).encode("utf-8")
    if path.exists():
        try:
            old_bytes = path.read_bytes()
            old, _ = read_projects(workspace)
        except (JournalFormatError, UnicodeDecodeError) as exc:
            recovery = preserve_draft(workspace, payload)
            raise JournalFormatError(f"Existing registry is malformed; it was left untouched and your draft is preserved at {recovery}. Copy and repair the original file before retrying", path) from exc
        by_id = {p["id"]: p for p in old}
        if _revision(old_bytes) == revision.strip('"'):
            new_ids = {p["id"] for p in checked}
            if not set(by_id).issubset(new_ids):
                raise JournalFormatError("Projects cannot be deleted; archive a project to retain its history", path)
            for project in checked:
                prior = by_id.get(project["id"])
                if prior and project["created_at"] != prior["created_at"]:
                    raise JournalFormatError("Project creation timestamps are immutable")
                if prior and prior["archived_at"] is not None and project["archived_at"] is None:
                    raise JournalFormatError("Archived projects cannot be reactivated")
    new_revision = _safe_replace(path, payload, revision, workspace, "projects")
    return checked, new_revision


def read_project_conflict(workspace: Path, conflict_id: str) -> dict:
    conflict = read_conflict(workspace, conflict_id, "projects")
    return {
        "conflict_id": conflict_id,
        "expected_revision": conflict["expected_revision"],
        "current_revision": conflict["current_revision"],
        "local": parse_projects(conflict["local_markdown"]),
        "external": parse_projects(conflict["external_markdown"]) if conflict["external_markdown"].strip() else [],
    }


def resolve_project_conflict(workspace: Path, conflict_id: str, projects: list[dict], revision: str) -> tuple[list[dict], str]:
    conflict = read_conflict(workspace, conflict_id, "projects")
    if conflict["current_revision"].strip('"') != revision.strip('"'):
        raise JournalConflictError(conflict_id, render_projects(projects), conflict["external_markdown"], revision, conflict["current_revision"])
    result = write_projects(workspace, projects, revision)
    folder = workspace / ".commitly" / "conflicts" / "projects" / conflict_id
    for name in ("local.md", "external.md", "conflict.json"):
        (folder / name).unlink(missing_ok=True)
    folder.rmdir()
    return result


def activity(workspace: Path, project_id: str) -> dict:
    project_id = str(UUID(project_id))
    registry, _ = read_projects(workspace)
    project = next((value for value in registry if value["id"] == project_id), None)
    if project is None:
        raise KeyError(project_id)
    entries = []
    for path in sorted((workspace / "journals").glob("*.md")) if (workspace / "journals").exists() else []:
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise JournalFormatError(f"Cannot read journal file: {exc}", path) from exc
        journal = parse_journal(raw, path.stem, path)
        entries.extend({"date": journal["date"], "entry": entry} for entry in journal["entries"] if entry["project_id"] == project_id)
    entries.sort(key=lambda item: entry_sort_key(item["entry"]), reverse=True)
    return {
        "project": project,
        "entries": entries,
        "latest_next_steps": [item for item in entries if item["entry"].get("next_step")][:5],
        "unresolved_blockers": [item for item in entries if (item["entry"]["type"] == "blocker" or item["entry"].get("blocker")) and not item["entry"].get("blocker_resolved_at")][:5],
    }
