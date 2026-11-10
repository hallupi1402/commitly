from __future__ import annotations

from datetime import date as CalendarDate
from datetime import datetime, timezone
import hashlib
import os
import shutil
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from commitly import config, git_activity, journal, projects, reports, search
from commitly.report_analysis import AnalysisUnavailable, analyze, local_runner, redact_text
from commitly.api.schemas import (
    BackupConfigurationInput, BackupStatus, DailyJournal, DocumentConflict, Error,
    JournalConflict, Project, ProjectActivity, SearchResult, Settings, SettingsPatch,
    TodayResponse,
    RefreshInput, RepositoryInput, UserContextInput,
)
from commitly.backup import status_for

router = APIRouter(prefix="/api/v1")


def _repositories(request: Request) -> list[dict]:
    value = config._read(request.app.state.config_dir / "repositories.json", {"repositories": []})
    repositories = value.get("repositories")
    if not isinstance(repositories, list) or any(not isinstance(item, dict) for item in repositories):
        raise ValueError("Selected repository settings are malformed")
    return repositories


def _save_repositories(request: Request, value: list[dict]) -> None:
    config._write(request.app.state.config_dir / "repositories.json", {"repositories": value})


def _evidence_id(repository_id: str, commit_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"commitly:evidence:{repository_id}:{commit_id}"))


def _empty_revision() -> str:
    return f'"{hashlib.sha256(b"" ).hexdigest()}"'


def _build_report(day: str, repository_items: list[tuple[dict, dict]], runner) -> dict:
    evidence = []
    for repository, item in repository_items:
        evidence.append({
            "id": item["id"], "repository_id": repository["id"],
            "repository_name": redact_text(repository["display_name"]), "repository_path": redact_text(repository["path"]),
            "commit_id": item["commit_id"], "authored_at": item["authored_at"],
            "subject": redact_text(item["subject"]), "changed_paths": [redact_text(path) for path in item["changed_paths"]],
            "added_lines": item["added_lines"], "deleted_lines": item["deleted_lines"],
            "analysis_status": "partial" if item.get("document_errors") else "complete",
            "analysis_note": "; ".join(error["error"] for error in item.get("document_errors", [])) or None,
        })
    try:
        prose = analyze([{"id": item["id"], "commit_id": item["commit_id"], "subject": item["subject"], "changed_paths": item["changed_paths"], "diff": item["diff"], "documents": item.get("documents", []), "document_errors": item.get("document_errors", [])} for _, item in repository_items], runner)
        status = "partial" if any(item.get("document_errors") for _, item in repository_items) else "complete"
    except AnalysisUnavailable as exc:
        status = "unavailable"
        for item in evidence:
            item["analysis_status"] = "failed"
            item["analysis_note"] = str(exc)
        refs = [item["id"] for item in evidence]
        phrase = f"Git ghi nhận {len(evidence)} commit đã đẩy trong ngày; phân tích nội dung chưa khả dụng vì chưa cấu hình mô hình cục bộ."
        prose = {"summary": {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"summary:{day}:{','.join(refs)}")), "text": phrase, "evidence_ids": refs, "certainty": "supported"}, "highlights": [], "details": []}
    return {"date": day, **prose, "evidence": evidence, "user_context": [], "analysis_status": status}


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
    try:
        doc, _ = journal.read_journal(workspace, today_date)
        steps: list[dict] = []
        blockers: list[dict] = []
        root = workspace / "journals"
        for path in sorted(root.glob("*.md")) if root.exists() else []:
            try:
                path_date = CalendarDate.fromisoformat(path.stem)
            except ValueError as exc:
                raise journal.JournalFormatError("Journal filename must use YYYY-MM-DD", path) from exc
            if path_date >= today_date:
                continue
            try:
                raw = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise journal.JournalFormatError(f"Cannot read journal file: {exc}", path) from exc
            older = journal.parse_journal(raw, path_date, path)
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
    except (journal.JournalFormatError, OSError) as exc:
        return _error(422, "journal_invalid", str(exc))


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


@router.get("/repositories")
def get_repositories(request: Request):
    try:
        return _repositories(request)
    except ValueError as exc:
        return _error(422, "repositories_invalid", str(exc))


@router.post("/repositories", status_code=201)
def add_repository(value: RepositoryInput, request: Request):
    try:
        details = git_activity.inspect_repository(value.path, value.remote_name)
        current = _repositories(request)
        if any(item["id"] == details["id"] for item in current):
            return _error(409, "repository_exists", "This Git repository is already selected")
        details["display_name"] = value.display_name.strip() if value.display_name and value.display_name.strip() else details["display_name"]
        details.update(last_fetch_at=None, last_fetch_status="never", last_error=None)
        current.append(details)
        _save_repositories(request, current)
        return details
    except (git_activity.GitActivityError, ValueError, OSError) as exc:
        return _error(422, "repository_invalid", str(exc))


@router.delete("/repositories/{repository_id}", status_code=204)
def remove_repository(repository_id: str, request: Request):
    try:
        current = _repositories(request)
        updated = [item for item in current if item["id"] != repository_id]
        if len(updated) == len(current):
            return _error(404, "repository_not_found", "Selected repository was not found")
        _save_repositories(request, updated)
        return Response(status_code=204)
    except (ValueError, OSError) as exc:
        return _error(422, "repositories_invalid", str(exc))


@router.post("/activity/refresh")
def refresh_activity(value: RefreshInput, request: Request):
    if value.start > value.end:
        return _error(422, "invalid_date_range", "The start date must be on or before the end date")
    try:
        all_repositories = _repositories(request)
    except ValueError as exc:
        return _error(422, "repositories_invalid", str(exc))
    selected = [item for item in all_repositories if value.repository_ids is None or item["id"] in value.repository_ids]
    try:
        settings = config.get_settings(request.app.state.config_dir)
    except ValueError as exc:
        return _error(422, "settings_invalid", str(exc))
    runner = local_runner(settings.get("model_path"), settings.get("model_executable"))
    response_items = []
    by_day: dict[str, list[tuple[dict, dict]]] = {}
    for repository in selected:
        fetch_status, fetch_error = git_activity.fetch_remote(repository)
        if fetch_status == "success":
            repository["last_fetch_at"] = datetime.now(timezone.utc).isoformat()
            repository["last_fetch_status"] = "success"
            repository["last_error"] = None
        else:
            repository["last_fetch_status"] = "failed"
            repository["last_error"] = fetch_error
        try:
            activity = git_activity.read_remote_activity(repository, value.start, value.end, fetch=False)
        except git_activity.GitActivityError:
            activity = []
        for item in activity:
            item["id"] = _evidence_id(repository["id"], item["commit_id"])
            day = datetime.fromisoformat(item["authored_at"]).astimezone().date().isoformat()
            by_day.setdefault(day, []).append((repository, item))
        response_items.append({
            "repository_id": repository["id"], "fetch_status": fetch_status,
            "last_verified_at": repository.get("last_fetch_at"),
            "analysis_status": "unavailable" if not ((settings.get("model_path") or os.environ.get("COMMITLY_LLM_MODEL")) and shutil.which(os.environ.get("COMMITLY_LLM_EXECUTABLE", settings.get("model_executable", "llama-cli")))) else "complete",
            "report_dates": [], "error": fetch_error,
        })
    writing_day = None
    try:
        _save_repositories(request, all_repositories)
        for day, items in sorted(by_day.items()):
            writing_day = day
            report_items = sorted({(repo["id"], item["commit_id"]): (repo, item) for repo, item in items}.values(), key=lambda pair: pair[1]["authored_at"])
            path = request.app.state.workspace / "reports" / f"{day}.md"
            old, revision = reports.read_report(request.app.state.workspace, CalendarDate.fromisoformat(day)) if path.exists() else (None, _empty_revision())
            known = {(item["repository_id"], item["commit_id"]) for item in old["evidence"]} if old else set()
            new_items = [(repo, item) for repo, item in report_items if (repo["id"], item["commit_id"]) not in known]
            if not new_items:
                continue
            generated = _build_report(day, new_items, runner)
            if old:
                generated["evidence"] = [*old["evidence"], *generated["evidence"]]
                generated["highlights"] = [*old["highlights"], *generated["highlights"]]
                generated["details"] = [*old["details"], *generated["details"]]
                generated["user_context"] = old["user_context"]
            reports.write_report(request.app.state.workspace, generated, revision)
            for item in response_items:
                if any(repo["id"] == item["repository_id"] for repo, _ in new_items):
                    item["report_dates"].append(day)
                    if generated["analysis_status"] != "complete":
                        item["analysis_status"] = "unavailable"
        return {"from": value.start.isoformat(), "to": value.end.isoformat(), "repositories": response_items}
    except journal.JournalConflictError as exc:
        day = CalendarDate.fromisoformat(writing_day) if writing_day else value.start
        try:
            return JSONResponse(status_code=409, content=reports.read_report_conflict(request.app.state.workspace, day, exc.conflict_id))
        except (OSError, ValueError, FileNotFoundError):
            return _error(409, "report_conflict", str(exc), conflict_id=exc.conflict_id)
    except (OSError, ValueError, journal.SafeWriteError) as exc:
        return _error(422, "report_write_failed", str(exc))


@router.get("/reports")
def get_report_dates(request: Request):
    return reports.list_report_dates(request.app.state.workspace)


@router.get("/reports/{date}")
def get_report(date: CalendarDate, request: Request, response: Response):
    try:
        report, revision = reports.read_report(request.app.state.workspace, date)
    except FileNotFoundError:
        return _error(404, "report_not_found", "No report exists for this date")
    except (OSError, ValueError) as exc:
        return _error(422, "report_invalid", str(exc))
    _etag(response, revision)
    return report


@router.put("/reports/{date}/context")
def put_report_context(date: CalendarDate, value: UserContextInput, request: Request, response: Response, if_match: str = Header(..., alias="If-Match")):
    try:
        try:
            report, _ = reports.read_report(request.app.state.workspace, date)
        except FileNotFoundError:
            if not value.text or not value.text.strip():
                return _error(404, "report_not_found", "There is no saved context to remove")
            report = {
                "date": date.isoformat(),
                "summary": {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"empty-day:{date.isoformat()}")), "text": "Chưa có hoạt động Git được ghi nhận cho ngày này.", "evidence_ids": [], "certainty": "supported"},
                "highlights": [], "details": [], "evidence": [], "user_context": [], "analysis_status": "unavailable",
            }
        context = report["user_context"]
        if value.text is None or not value.text.strip():
            context.clear()
        elif "\n" in value.text or "\r" in value.text:
            return _error(422, "context_invalid", "Context must be one line")
        elif context:
            context[0]["text"] = redact_text(value.text.strip())
        else:
            context.append({"id": str(uuid.uuid4()), "created_at": datetime.now(timezone.utc).isoformat(), "text": redact_text(value.text.strip())})
        saved, revision = reports.write_report(request.app.state.workspace, report, if_match)
    except FileNotFoundError:
        return _error(404, "report_not_found", "No report exists for this date")
    except journal.JournalConflictError as exc:
        try:
            return JSONResponse(status_code=409, content=reports.read_report_conflict(request.app.state.workspace, date, exc.conflict_id))
        except (OSError, ValueError, FileNotFoundError):
            return _error(409, "report_conflict", str(exc), conflict_id=exc.conflict_id)
    except (OSError, ValueError, journal.SafeWriteError) as exc:
        return _error(422, "context_save_failed", str(exc))
    _etag(response, revision)
    return saved


@router.get("/reports/{date}/conflicts/{conflict_id}")
def get_report_conflict(date: CalendarDate, conflict_id: str, request: Request):
    try:
        return reports.read_report_conflict(request.app.state.workspace, date, conflict_id)
    except (FileNotFoundError, ValueError, OSError) as exc:
        return _error(404, "conflict_not_found", str(exc))


@router.post("/reports/{date}/conflicts/{conflict_id}/resolve")
def resolve_report(date: CalendarDate, conflict_id: str, value: dict, request: Request, response: Response, if_match: str = Header(..., alias="If-Match")):
    if value.get("date") != date.isoformat():
        return _error(422, "date_mismatch", "Report date must match the requested date")
    try:
        if value.get("keep_external") is True:
            saved, revision = reports.keep_external_report_conflict(request.app.state.workspace, date, conflict_id, if_match)
        else:
            saved, revision = reports.resolve_report_conflict(request.app.state.workspace, date, conflict_id, value, if_match)
    except journal.JournalConflictError as exc:
        try:
            return JSONResponse(status_code=409, content=reports.read_report_conflict(request.app.state.workspace, date, exc.conflict_id))
        except (OSError, ValueError, FileNotFoundError):
            return _error(409, "report_conflict", str(exc), conflict_id=exc.conflict_id)
    except FileNotFoundError as exc:
        return _error(404, "conflict_not_found", str(exc))
    except (OSError, ValueError, journal.SafeWriteError) as exc:
        return _error(422, "resolution_failed", str(exc))
    _etag(response, revision)
    return saved


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
