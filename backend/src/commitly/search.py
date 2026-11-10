"""Direct search over the human-readable Markdown journal files."""

from datetime import date
from pathlib import Path

from commitly.journal import JournalFormatError, entry_sort_key, parse_journal


def search_entries(workspace: Path, q: str = "", project_id: str | None = None, entry_type: str | None = None, from_date: date | None = None, to_date: date | None = None) -> list[dict]:
    if entry_type is not None and entry_type not in {"work", "note", "blocker"}:
        raise ValueError("type must be work, note, or blocker")
    needle = q.strip().casefold()
    result = []
    root = workspace / "journals"
    for path in sorted(root.glob("*.md")) if root.exists() else []:
        try:
            current_date = date.fromisoformat(path.stem)
        except ValueError as exc:
            raise JournalFormatError("Journal filename must use YYYY-MM-DD", path) from exc
        if (from_date and current_date < from_date) or (to_date and current_date > to_date):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise JournalFormatError(f"Cannot read journal file: {exc}", path) from exc
        document = parse_journal(raw, current_date, path)
        for entry in document["entries"]:
            if project_id and entry["project_id"] != project_id:
                continue
            if entry_type and entry["type"] != entry_type:
                continue
            searchable = "\n".join(str(entry.get(key) or "") for key in ("description", "result", "blocker", "next_step", "notes", "tags", "references"))
            if needle and needle not in searchable.casefold():
                continue
            result.append({"date": document["date"], "entry": entry})
    result.sort(key=lambda item: entry_sort_key(item["entry"]), reverse=True)
    return result
