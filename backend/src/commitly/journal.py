"""Markdown journal format and Linux-safe document writes."""

from __future__ import annotations

import ctypes
import errno
import fcntl
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import UUID, uuid4


class JournalFormatError(ValueError):
    def __init__(self, message: str, path: Path | None = None):
        self.path = path
        super().__init__(f"{message} ({path})" if path else message)


class JournalConflictError(RuntimeError):
    def __init__(self, conflict_id: str, local: str, external: str, expected: str, current: str):
        self.conflict_id = conflict_id
        self.local = local
        self.external = external
        self.expected_revision = expected
        self.current_revision = current
        super().__init__("The Markdown file changed outside Commitly. Compare the saved versions before resolving.")


class SafeWriteError(OSError):
    """A safe atomic replacement is unavailable; the original is left untouched."""


def _canonical_date(value: str | date) -> str:
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError as exc:
        raise ValueError("Date must use YYYY-MM-DD format") from exc


def _timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Timestamp must be RFC 3339") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone")
    if parsed.utcoffset().total_seconds() != 0:
        raise ValueError("Creation timestamps must be UTC")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _entry_defaults(entry: dict, journal_date: str) -> dict:
    value = dict(entry)
    value.setdefault("id", str(uuid4()))
    value.setdefault("created_at", datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"))
    value.setdefault("type", "work")
    value.setdefault("project_id", None)
    value.setdefault("tags", [])
    value.setdefault("result", None)
    value.setdefault("blocker", None)
    value.setdefault("blocker_resolved_at", None)
    value.setdefault("next_step", None)
    value.setdefault("references", [])
    value.setdefault("notes", None)
    value["date"] = journal_date
    return value


def validate_entry(entry: dict, journal_date: str) -> dict:
    value = _entry_defaults(entry, journal_date)
    try:
        value["id"] = str(UUID(value["id"]))
        value["created_at"] = _timestamp(value["created_at"])
        if value["project_id"] is not None:
            value["project_id"] = str(UUID(value["project_id"]))
        if value["blocker_resolved_at"] is not None:
            value["blocker_resolved_at"] = _timestamp(value["blocker_resolved_at"])
    except (ValueError, TypeError, KeyError) as exc:
        raise JournalFormatError(str(exc)) from exc
    if value["type"] not in {"work", "note", "blocker"}:
        raise JournalFormatError("Entry type must be work, note, or blocker")
    if not isinstance(value.get("description"), str) or not value["description"].strip():
        raise JournalFormatError("Description must contain a non-whitespace character")
    value["description"] = value["description"].strip()
    for key in ("result", "blocker", "next_step", "notes"):
        if value[key] is not None and not isinstance(value[key], str):
            raise JournalFormatError(f"{key} must be text or null")
    for key in ("tags", "references"):
        if not isinstance(value[key], list) or any(not isinstance(item, str) for item in value[key]):
            raise JournalFormatError(f"{key} must be a list of text")
        if any("\n" in item or "\r" in item for item in value[key]):
            raise JournalFormatError(f"{key} values must be one line each")
    unique_tags = {}
    for tag in value["tags"]:
        normalized = tag.strip()
        if normalized:
            unique_tags.setdefault(normalized.casefold(), normalized)
    value["tags"] = list(unique_tags.values())
    if any(re.search(r"<!--\s*/?commitly:", str(value.get(key) or "")) for key in ("description", "result", "blocker", "next_step", "notes")):
        raise JournalFormatError("Journal text cannot contain Commitly metadata markers")
    return value


def entry_sort_key(entry: dict) -> tuple[datetime, str]:
    return datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00")), entry["id"]


def validate_journal(document: dict, expected_date: str | date | None = None) -> dict:
    if not isinstance(document, dict):
        raise JournalFormatError("Journal must be an object")
    try:
        journal_date = _canonical_date(document["date"])
    except (KeyError, ValueError, TypeError) as exc:
        raise JournalFormatError("Journal date is missing or invalid") from exc
    if expected_date is not None and journal_date != _canonical_date(expected_date):
        raise JournalFormatError("Journal date does not match the requested date")
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise JournalFormatError("Journal entries must be a list")
    checked = [validate_entry(entry, journal_date) for entry in entries]
    ids = [item["id"] for item in checked]
    if len(ids) != len(set(ids)):
        raise JournalFormatError("Journal contains duplicate entry IDs")
    checked.sort(key=entry_sort_key)
    reflection = document.get("reflection")
    if reflection is not None:
        if not isinstance(reflection, dict):
            raise JournalFormatError("Reflection must be an object or null")
        reflection = {key: reflection.get(key) for key in ("accomplishments", "blockers", "next_steps")}
        if any(v is not None and not isinstance(v, str) for v in reflection.values()):
            raise JournalFormatError("Reflection fields must be text or null")
    return {"date": journal_date, "entries": checked, "reflection": reflection}


_ENTRY_START = re.compile(r"^<!-- commitly:entry (\{.*\}) -->$", re.M)
_ENTRY_END = re.compile(r"^<!-- /commitly:entry ([0-9a-f-]+) -->$", re.M)
_JOURNAL_HEADER = re.compile(r"^<!-- commitly:journal v(\d+) date=(\d{4}-\d{2}-\d{2}) -->$")
_FIELD_HEADINGS = {
    "Description": "description", "Tags": "tags", "Result": "result", "Blocker": "blocker",
    "Next step": "next_step", "References": "references", "Notes": "notes",
}


def _sections(body: str, headings: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    current: str | None = None
    for line in body.splitlines():
        match = re.fullmatch(r"### (.+)", line)
        if match and match.group(1) in headings:
            current = headings[match.group(1)]
            if current in result:
                raise JournalFormatError(f"Duplicate Markdown section: {match.group(1)}")
            result[current] = ""
        elif current is not None:
            if re.fullmatch(r"\\+### .+", line) and line.lstrip("\\")[4:] in headings:
                line = line[1:]
            result[current] += ("\n" if result[current] else "") + line
        elif line.strip():
            raise JournalFormatError("Unexpected content before the Description section")
    return {key: value.strip() for key, value in result.items()}


def _escape_user_headings(value: str) -> str:
    headings = set(_FIELD_HEADINGS) | {"Accomplishments", "Blockers", "Next steps"}
    return "\n".join("\\" + line if re.fullmatch(r"\\*### (.+)", line) and line.lstrip("\\")[4:] in headings else line for line in value.split("\n"))


def parse_journal(raw: str, expected_date: str | date | None = None, path: Path | None = None) -> dict:
    try:
        lines = raw.splitlines()
        if not lines:
            raise JournalFormatError("Journal is empty")
        header = _JOURNAL_HEADER.fullmatch(lines[0])
        if not header:
            raise JournalFormatError("Missing or malformed journal schema header")
        if header.group(1) != "1":
            raise JournalFormatError(f"Unsupported journal schema version {header.group(1)}")
        journal_date = _canonical_date(header.group(2))
        if expected_date is not None and journal_date != _canonical_date(expected_date):
            raise JournalFormatError("Journal header date does not match the file date")
        if len(lines) < 2 or lines[1] != f"# Daily Journal — {journal_date}":
            raise JournalFormatError("Missing or mismatched journal title")

        entries: list[dict] = []
        reflection: dict | None = None
        tail = "\n".join(lines[2:])
        positions = [match.start() for match in _ENTRY_START.finditer(tail)]
        spans = []
        for start in positions:
            start_match = _ENTRY_START.search(tail, start)
            assert start_match is not None
            end_match = _ENTRY_END.search(tail, start_match.end())
            if end_match is None:
                raise JournalFormatError("Entry has no closing marker")
            spans.append((start_match.start(), end_match.end()))
            meta = json.loads(start_match.group(1))
            if not isinstance(meta, dict) or not {"id", "created_at", "type", "project_id", "blocker_resolved_at"}.issubset(meta):
                raise JournalFormatError("Entry metadata is missing required fields")
            if set(meta) != {"id", "created_at", "type", "project_id", "blocker_resolved_at"}:
                raise JournalFormatError("Entry metadata contains unsupported fields")
            body = tail[start_match.end():end_match.start()].strip("\n")
            fields = _sections(body, _FIELD_HEADINGS)
            entry = {**meta, **fields}
            if entry.get("tags"):
                entry["tags"] = [line[2:].strip() for line in entry["tags"].splitlines() if line.startswith("- ")]
            else:
                entry["tags"] = []
            if entry.get("references"):
                entry["references"] = [line[2:].strip() for line in entry["references"].splitlines() if line.startswith("- ")]
            else:
                entry["references"] = []
            if end_match.group(1) != str(meta.get("id")):
                raise JournalFormatError("Entry closing marker ID does not match metadata")
            entry["date"] = journal_date
            entries.append(validate_entry(entry, journal_date))

        if len(entries) != len(positions):
            raise JournalFormatError("Unable to parse all journal entries")
        remaining = tail
        for start, end in reversed(spans):
            remaining = remaining[:start] + remaining[end:]
        if remaining.strip() and not remaining.lstrip().startswith("## Reflection"):
            raise JournalFormatError("Unexpected content outside journal entries")
        if "## Reflection" in remaining:
            before, reflection_text = remaining.split("## Reflection", 1)
            if before.strip() or "## Reflection" in reflection_text:
                raise JournalFormatError("Malformed reflection section")
            fields = _sections(reflection_text, {"Accomplishments": "accomplishments", "Blockers": "blockers", "Next steps": "next_steps"})
            reflection = {key: fields.get(key) or None for key in ("accomplishments", "blockers", "next_steps")}
            if not any(reflection.values()):
                reflection = None
        result = validate_journal({"date": journal_date, "entries": entries, "reflection": reflection}, expected_date)
        return result
    except (JournalFormatError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, JournalFormatError) and exc.path:
            raise
        raise JournalFormatError(str(exc), path) from exc


def _render_field(label: str, value: str | None) -> str:
    if value is None or value == "":
        return ""
    return f"\n### {label}\n{value.strip()}\n"


def render_journal(document: dict) -> str:
    value = validate_journal(document)
    date_text = value["date"]
    out = [f"<!-- commitly:journal v1 date={date_text} -->", f"# Daily Journal — {date_text}", ""]
    for entry in value["entries"]:
        meta = {key: entry[key] for key in ("id", "created_at", "type", "project_id", "blocker_resolved_at")}
        out += [f"<!-- commitly:entry {json.dumps(meta, ensure_ascii=False, separators=(',', ':'))} -->", "### Description", _escape_user_headings(entry["description"])]
        for key, label in (("tags", "Tags"), ("result", "Result"), ("blocker", "Blocker"), ("next_step", "Next step"), ("references", "References"), ("notes", "Notes")):
            item = entry.get(key)
            if not item:
                continue
            out.append("")
            out.append(f"### {label}")
            if isinstance(item, list):
                out.extend(f"- {part}" for part in item)
            else:
                out.append(_escape_user_headings(item.strip()))
        out += [f"<!-- /commitly:entry {entry['id']} -->", ""]
    if value["reflection"]:
        out += ["## Reflection", ""]
        for key, label in (("accomplishments", "Accomplishments"), ("blockers", "Blockers"), ("next_steps", "Next steps")):
            item = value["reflection"].get(key)
            if item:
                out += [f"### {label}", _escape_user_headings(item.strip()), ""]
    return "\n".join(out).rstrip() + "\n"


def _revision(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _quoted(revision: str) -> str:
    return f'"{revision}"'


def _unquote(revision: str) -> str:
    return revision.strip().strip('"')


def read_journal(workspace: Path, journal_date: str | date) -> tuple[dict, str]:
    date_text = _canonical_date(journal_date)
    path = workspace / "journals" / f"{date_text}.md"
    if not path.exists():
        return {"date": date_text, "entries": [], "reflection": None}, _quoted(_revision(b""))
    raw = path.read_bytes()
    try:
        document = parse_journal(raw.decode("utf-8"), date_text, path)
    except UnicodeDecodeError as exc:
        raise JournalFormatError("Journal is not valid UTF-8; copy and repair the original file", path) from exc
    return document, _quoted(_revision(raw))


def _renameat2(old: Path, new: Path, flags: int) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    operation = getattr(libc, "renameat2", None)
    if operation is None:
        raise SafeWriteError(errno.ENOSYS, "Safe atomic exchange is unavailable")
    operation.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    operation.restype = ctypes.c_int
    if operation(-100, os.fsencode(old), -100, os.fsencode(new), flags) != 0:
        error = ctypes.get_errno()
        if error in (errno.ENOSYS, errno.EINVAL, errno.EOPNOTSUPP):
            raise SafeWriteError(error, "This filesystem cannot safely update Commitly journals")
        raise OSError(error, os.strerror(error), str(new))


@contextmanager
def _file_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _write_recovery(base: Path, local: bytes, external: bytes, metadata: dict) -> str:
    conflict_id = str(uuid4())
    folder = base / ".commitly" / "conflicts"
    if metadata.get("key") == "projects":
        folder = folder / "projects"
    else:
        folder = folder / str(metadata["key"])
    folder = folder / conflict_id
    folder.mkdir(parents=True, exist_ok=False)
    for name, data in (("local.md", local), ("external.md", external), ("conflict.json", json.dumps(metadata, indent=2).encode())):
        path = folder / name
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    dfd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    return conflict_id


def preserve_draft(workspace: Path, candidate: bytes) -> Path:
    folder = workspace / ".commitly" / "recovery"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid4()}.md"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(candidate)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def _safe_replace(path: Path, candidate: bytes, expected_revision: str, recovery_root: Path, conflict_key: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(f".{path.name}.lock")
    with _file_lock(lock_path):
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temp = Path(temp_name)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(candidate)
                stream.flush()
                os.fsync(stream.fileno())
            expected = _unquote(expected_revision)
            if path.exists():
                try:
                    _renameat2(temp, path, 2)  # RENAME_EXCHANGE
                except OSError as exc:
                    recovery = preserve_draft(recovery_root, candidate)
                    raise SafeWriteError(exc.errno, f"Atomic journal update failed; your draft was preserved at {recovery}") from exc
                displaced = temp.read_bytes()
                actual = _revision(displaced)
                if actual != expected:
                    conflict_id = _write_recovery(recovery_root, candidate, displaced, {
                        "key": conflict_key, "expected_revision": expected, "current_revision": actual,
                    })
                    try:
                        _renameat2(temp, path, 2)
                    except OSError as exc:
                        raise SafeWriteError(exc.errno, f"External change conflict was preserved as {conflict_id}, but the original file could not be restored safely") from exc
                    raise JournalConflictError(conflict_id, candidate.decode(), displaced.decode(errors="replace"), expected, actual)
                existing_target = True
            else:
                if expected != _revision(b""):
                    conflict_id = _write_recovery(recovery_root, candidate, b"", {
                        "key": conflict_key, "expected_revision": expected, "current_revision": _revision(b""),
                    })
                    raise JournalConflictError(conflict_id, candidate.decode(), "", expected, _revision(b""))
                try:
                    _renameat2(temp, path, 1)  # RENAME_NOREPLACE
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        recovery = preserve_draft(recovery_root, candidate)
                        raise SafeWriteError(exc.errno, f"Atomic journal creation failed; your draft was preserved at {recovery}") from exc
                    external = path.read_bytes()
                    conflict_id = _write_recovery(recovery_root, candidate, external, {
                        "key": conflict_key, "expected_revision": expected, "current_revision": _revision(external),
                    })
                    raise JournalConflictError(conflict_id, candidate.decode(), external.decode(errors="replace"), expected, _revision(external))
                existing_target = False
            try:
                dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            except OSError as exc:
                preserve_draft(recovery_root, candidate)
                if existing_target and temp.exists():
                    preserve_draft(recovery_root, temp.read_bytes())
                    try:
                        _renameat2(temp, path, 2)
                    except OSError:
                        pass
                raise SafeWriteError(exc.errno, "Could not open the journal directory for syncing; recovery copies were preserved") from exc
            try:
                try:
                    os.fsync(dir_fd)
                except OSError as exc:
                    preserve_draft(recovery_root, candidate)
                    if existing_target and temp.exists():
                        try:
                            preserve_draft(recovery_root, temp.read_bytes())
                            _renameat2(temp, path, 2)
                            os.fsync(dir_fd)
                        except OSError:
                            pass
                    raise SafeWriteError(exc.errno, "Could not sync the journal directory; the previous file was restored and the draft was preserved") from exc
            finally:
                os.close(dir_fd)
            if temp.exists():
                temp.unlink()
            return _quoted(_revision(candidate))
        finally:
            if temp.exists():
                temp.unlink()


def write_journal(workspace: Path, document: dict, expected_revision: str) -> tuple[dict, str]:
    value = validate_journal(document)
    path = workspace / "journals" / f"{value['date']}.md"
    candidate = render_journal(value).encode("utf-8")
    previous = {}
    if path.exists():
        try:
            old_bytes = path.read_bytes()
            old = parse_journal(old_bytes.decode("utf-8"), value["date"], path)
        except (JournalFormatError, UnicodeDecodeError) as exc:
            recovery_path = preserve_draft(workspace, candidate)
            raise JournalFormatError(f"Existing Markdown is malformed; the file was left untouched and your draft is preserved at {recovery_path}. Copy and repair the original file before retrying", path) from exc
        previous = {entry["id"]: entry for entry in old["entries"]}
        revision_current = _revision(old_bytes) == _unquote(expected_revision)
    else:
        revision_current = _unquote(expected_revision) == _revision(b"")
    for entry in value["entries"]:
        if revision_current and entry["id"] in previous and entry["created_at"] != previous[entry["id"]]["created_at"]:
            raise JournalFormatError("Entry creation timestamps are immutable", path)
    from commitly.projects import read_projects

    try:
        registry = read_projects(workspace)[0]
    except JournalFormatError as exc:
        recovery_path = preserve_draft(workspace, candidate)
        raise JournalFormatError(f"Project registry is invalid; it was left untouched and your draft is preserved at {recovery_path}", exc.path) from exc
    project_by_id = {project["id"]: project for project in registry}
    for entry in value["entries"]:
        project_id = entry["project_id"]
        if project_id is not None and project_id not in project_by_id:
            raise JournalFormatError("Entry refers to an unknown project", path)
        if project_id is not None and project_by_id[project_id]["archived_at"] and entry["id"] not in previous:
            raise JournalFormatError("Archived projects cannot be assigned to new entries", path)
    for other in (workspace / "journals").glob("*.md"):
        if other == path:
            continue
        try:
            other_doc = parse_journal(other.read_text(encoding="utf-8"), other.stem, other)
        except (JournalFormatError, UnicodeDecodeError) as exc:
            recovery_path = preserve_draft(workspace, candidate)
            raise JournalFormatError(f"Cannot verify workspace entry IDs because {other} is invalid; your draft is preserved at {recovery_path}", other) from exc
        other_ids = {entry["id"] for entry in other_doc["entries"]}
        if any(entry["id"] in other_ids for entry in value["entries"]):
            raise JournalFormatError("Entry ID is already used on another date", path)
    revision = _safe_replace(path, candidate, expected_revision, workspace, value["date"])
    return value, revision


def read_conflict(workspace: Path, conflict_id: str, key: str) -> dict:
    try:
        UUID(conflict_id)
    except ValueError as exc:
        raise FileNotFoundError("Conflict not found") from exc
    folder = workspace / ".commitly" / "conflicts"
    folder = folder / ("projects" if key == "projects" else key) / conflict_id
    meta = json.loads((folder / "conflict.json").read_text(encoding="utf-8"))
    if meta.get("key") != key:
        raise FileNotFoundError("Conflict not found")
    return {
        **meta,
        "local_markdown": (folder / "local.md").read_text(encoding="utf-8"),
        "external_markdown": (folder / "external.md").read_text(encoding="utf-8"),
    }


def resolve_journal_conflict(workspace: Path, conflict_id: str, document: dict, current_revision: str) -> tuple[dict, str]:
    conflict = read_conflict(workspace, conflict_id, _canonical_date(document["date"]))
    if _unquote(conflict["current_revision"]) != _unquote(current_revision):
        raise JournalConflictError(conflict_id, render_journal(document), conflict["external_markdown"], current_revision, conflict["current_revision"])
    result = write_journal(workspace, document, current_revision)
    folder = workspace / ".commitly" / "conflicts" / conflict_id
    for name in ("local.md", "external.md", "conflict.json"):
        (folder / name).unlink(missing_ok=True)
    folder.rmdir()
    return result
