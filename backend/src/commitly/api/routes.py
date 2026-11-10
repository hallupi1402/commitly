from __future__ import annotations

from datetime import date as CalendarDate
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from commitly import config, journal, projects, search
from commitly.api.schemas import (
    BackupConfigurationInput, BackupStatus, DailyJournal, DocumentConflict, Error,
    JournalConflict, Project, ProjectActivity, SearchResult, Settings, SettingsPatch,
    TodayResponse,
)
from commitly.backup import status_for

router = APIRouter(prefix="/api/v1")


def _workspace(request: Request) -> Path:
    return request.app.state.workspace


def _error(status: int, code: str, message: str, **details):
    return JSONResponse(status_code=status, content={"code": code, "message": message, "details": details})


def _etag(response: Response, revision: str) -> None:
    response.headers["ETag"] = revision


def _conflict_payload(workspace: Path, conflict: journal.JournalConflictError, date_text: str) -> dict:
    local = journal.parse_journal(conflict.local, date_text)
    external = journal.parse_journal(conflict.external, date_text) if conflict.external.strip() else {"date": date_text, "entries": [], "reflection": None}
    return {
        "conflict_id": conflict.conflict_id,
        "date": date_text,
        "expected_revision": conflict.expected_revision,
        "current_revision": conflict.current_revision,
        "local": local,
        "external": external,
    }


@router.get("/today", response_model=TodayResponse)
def today(request: Request):
    workspace = _workspace(request)
    today_date = CalendarDate.today()
    doc, _ = journal.read_journal(workspace, today_date)
    steps: list[dict] = []
    blockers: list[dict] = []
    for path in sorted((workspace / "journals").glob("*.md")) if (workspace / "journals").exists() else []:
        if path.stem >= today_date.isoformat():
            continue
        older = journal.parse_journal(path.read_text(encoding="utf-8"), path.stem, path)
        for entry in older["entries"]:
            if entry.get("next_step"):
                steps.append(entry)
            if (entry["type"] == "blocker" or entry.get("blocker")) and not entry.get("blocker_resolved_at"):
                blockers.append(entry)
    steps.sort(key=journal.entry_sort_key, reverse=True)
    blockers.sort(key=journal.entry_sort_key, reverse=True)
    grouped: dict[str, dict] = {}
    for key, entries in (("next_steps", steps[:5]), ("blockers", blockers[:5])):
        for entry in entries:
            group = grouped.setdefault(entry["date"], {"source_date": entry["date"], "next_steps": [], "blockers": []})
            group[key].append(entry)
    return {"date": today_date.isoformat(), "journal": doc, "previous_context": sorted(grouped.values(), key=lambda item: item["source_date"], reverse=True)}


@router.get("/journals/{date}", response_model=DailyJournal)
def get_journal(date: CalendarDate, request: Request, response: Response):
    try:
        doc, revision = journal.read_journal(_workspace(request), date)
    except (journal.JournalFormatError, OSError) as exc:
        return _error(422, "journal_invalid", str(exc))
    _etag(response, revision)
    return doc


def _save_journal(document: DailyJournal, request: Request, if_match: str, conflict_response=True):
    try:
        saved, revision = journal.write_journal(_workspace(request), document.model_dump(mode="json"), if_match)
        return saved, revision
    except journal.JournalConflictError as exc:
        try:
            payload = _conflict_payload(_workspace(request), exc, document.date.isoformat())
        except journal.JournalFormatError as invalid:
            return _error(422, "journal_invalid", str(invalid), preserved_conflict_id=exc.conflict_id)
        return JSONResponse(status_code=409, content=payload)
    except (journal.JournalFormatError, journal.SafeWriteError, OSError) as exc:
        return _error(422, "journal_write_failed", str(exc))


@router.put("/journals/{date}", response_model=DailyJournal, responses={409: {"model": JournalConflict}, 422: {"model": Error}})
def put_journal(date: CalendarDate, document: DailyJournal, request: Request, response: Response, if_match: str = Header(..., alias="If-Match")):
    if document.date != date:
        return _error(422, "date_mismatch", "Journal date must match the requested date")
    saved = _save_journal(document, request, if_match)
    if isinstance(saved, JSONResponse):
        return saved
    doc, revision = saved
    _etag(response, revision)
    return doc


@router.get("/journals/{date}/conflicts/{conflict_id}", response_model=JournalConflict, responses={404: {"model": Error}})
def get_journal_conflict(date: CalendarDate, conflict_id: str, request: Request):
    try:
        value = journal.read_conflict(_workspace(request), conflict_id, date.isoformat())
        return _conflict_payload(_workspace(request), journal.JournalConflictError(conflict_id, value["local_markdown"], value["external_markdown"], value["expected_revision"], value["current_revision"]), date.isoformat())
    except (FileNotFoundError, ValueError) as exc:
        return _error(404, "conflict_not_found", str(exc))
    except journal.JournalFormatError as exc:
        return _error(422, "journal_invalid", str(exc))


@router.post("/journals/{date}/conflicts/{conflict_id}/resolve", response_model=DailyJournal, responses={404: {"model": Error}, 409: {"model": JournalConflict}, 422: {"model": Error}})
def resolve_journal(date: CalendarDate, conflict_id: str, document: DailyJournal, request: Request, response: Response, if_match: str = Header(..., alias="If-Match")):
    if document.date != date:
        return _error(422, "date_mismatch", "Journal date must match the requested date")
    try:
        saved, revision = journal.resolve_journal_conflict(_workspace(request), conflict_id, document.model_dump(mode="json"), if_match)
    except journal.JournalConflictError as exc:
        return JSONResponse(status_code=409, content=_conflict_payload(_workspace(request), exc, date.isoformat()))
    except FileNotFoundError as exc:
        return _error(404, "conflict_not_found", str(exc))
    except (journal.JournalFormatError, OSError, journal.SafeWriteError) as exc:
        return _error(422, "resolution_failed", str(exc))
    _etag(response, revision)
    return saved


@router.get("/entries/search", response_model=list[SearchResult])
def search_entries(request: Request, q: str = "", project_id: UUID | None = None, type: str | None = None, from_date: CalendarDate | None = Query(None, alias="from"), to_date: CalendarDate | None = Query(None, alias="to")):
    if from_date and to_date and from_date > to_date:
        return _error(422, "invalid_date_range", "The start date must be on or before the end date")
    try:
        return search.search_entries(_workspace(request), q=q, project_id=str(project_id) if project_id else None, entry_type=type, from_date=from_date, to_date=to_date)
    except (journal.JournalFormatError, ValueError) as exc:
        return _error(422, "search_failed", str(exc))


@router.get("/projects", response_model=list[Project])
def get_projects(request: Request, response: Response):
    try:
        value, revision = projects.read_projects(_workspace(request))
    except (journal.JournalFormatError, OSError) as exc:
        return _error(422, "projects_invalid", str(exc))
    _etag(response, revision)
    return value


@router.put("/projects", response_model=list[Project], responses={409: {"model": DocumentConflict}, 422: {"model": Error}})
def put_projects(value: list[Project], request: Request, response: Response, if_match: str = Header(..., alias="If-Match")):
    try:
        saved, revision = projects.write_projects(_workspace(request), [item.model_dump(mode="json") for item in value], if_match)
    except journal.JournalConflictError as exc:
        try:
            external = projects.parse_projects(exc.external) if exc.external.strip() else []
            local = projects.parse_projects(exc.local)
        except journal.JournalFormatError as invalid:
            return _error(422, "projects_invalid", str(invalid), preserved_conflict_id=exc.conflict_id)
        return JSONResponse(status_code=409, content={"conflict_id": exc.conflict_id, "expected_revision": exc.expected_revision, "current_revision": exc.current_revision, "local": local, "external": external})
    except (journal.JournalFormatError, OSError) as exc:
        return _error(422, "projects_write_failed", str(exc))
    _etag(response, revision)
    return saved


@router.get("/projects/conflicts/{conflict_id}", response_model=DocumentConflict, responses={404: {"model": Error}})
def get_project_conflict(conflict_id: str, request: Request):
    try:
        return projects.read_project_conflict(_workspace(request), conflict_id)
    except (FileNotFoundError, ValueError) as exc:
        return _error(404, "conflict_not_found", str(exc))
    except journal.JournalFormatError as exc:
        return _error(422, "projects_invalid", str(exc))


@router.post("/projects/conflicts/{conflict_id}/resolve", response_model=list[Project], responses={404: {"model": Error}, 409: {"model": DocumentConflict}})
def resolve_project_conflict(conflict_id: str, value: list[Project], request: Request, response: Response, if_match: str = Header(..., alias="If-Match")):
    try:
        saved, revision = projects.resolve_project_conflict(_workspace(request), conflict_id, [item.model_dump(mode="json") for item in value], if_match)
    except journal.JournalConflictError as exc:
        return JSONResponse(status_code=409, content={"conflict_id": exc.conflict_id, "expected_revision": exc.expected_revision, "current_revision": exc.current_revision, "local": projects.parse_projects(exc.local), "external": projects.parse_projects(exc.external) if exc.external.strip() else []})
    except FileNotFoundError as exc:
        return _error(404, "conflict_not_found", str(exc))
    except (journal.JournalFormatError, OSError) as exc:
        return _error(422, "resolution_failed", str(exc))
    _etag(response, revision)
    return saved


@router.get("/projects/{project_id}/activity", response_model=ProjectActivity)
def project_activity(project_id: str, request: Request):
    try:
        return projects.activity(_workspace(request), project_id)
    except KeyError:
        return _error(404, "project_not_found", "Project not found")
    except (journal.JournalFormatError, ValueError) as exc:
        return _error(422, "activity_failed", str(exc))


@router.get("/backup/status", response_model=BackupStatus)
def backup_status(request: Request):
    return status_for(_workspace(request), request.app.state.config_dir, request.app.state.state_dir)


@router.put("/backup/configuration", response_model=BackupStatus, responses={422: {"model": Error}})
def configure_backup(value: BackupConfigurationInput, request: Request):
    try:
        config.update_backup_configuration(value.model_dump(), request.app.state.config_dir)
        return status_for(_workspace(request), request.app.state.config_dir, request.app.state.state_dir)
    except ValueError as exc:
        return _error(422, "backup_configuration_invalid", str(exc))


@router.get("/settings", response_model=Settings)
def get_user_settings(request: Request):
    try:
        return config.get_settings(request.app.state.config_dir, _workspace(request))
    except ValueError as exc:
        return _error(422, "settings_invalid", str(exc))


@router.patch("/settings", response_model=Settings, responses={422: {"model": Error}})
def patch_user_settings(value: SettingsPatch, request: Request):
    try:
        return config.update_settings(value.model_dump(exclude_unset=True), request.app.state.config_dir, _workspace(request))
    except ValueError as exc:
        return _error(422, "settings_invalid", str(exc))
