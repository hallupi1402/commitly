from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


EntryType = Literal["work", "note", "blocker"]


class JournalEntry(StrictModel):
    id: UUID
    created_at: datetime
    date: date
    type: EntryType = "work"
    description: str = Field(min_length=1)
    project_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    result: str | None = None
    blocker: str | None = None
    blocker_resolved_at: datetime | None = None
    next_step: str | None = None
    references: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Description must contain a non-whitespace character")
        return value


class DailyReflection(StrictModel):
    accomplishments: str | None = None
    blockers: str | None = None
    next_steps: str | None = None


class DailyJournal(StrictModel):
    date: date
    entries: list[JournalEntry]
    reflection: DailyReflection | None = None


class Project(StrictModel):
    id: UUID
    name: str = Field(min_length=1)
    created_at: datetime
    archived_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Project name must contain a non-whitespace character")
        return value


class SearchResult(StrictModel):
    date: date
    entry: JournalEntry


class PreviousContext(StrictModel):
    source_date: date
    next_steps: list[JournalEntry] = Field(max_length=5)
    blockers: list[JournalEntry] = Field(max_length=5)


class TodayResponse(StrictModel):
    date: date
    journal: DailyJournal
    previous_context: list[PreviousContext]


class JournalConflict(StrictModel):
    conflict_id: UUID
    date: date
    expected_revision: str
    current_revision: str
    local: DailyJournal
    external: DailyJournal


class DocumentConflict(StrictModel):
    conflict_id: UUID
    expected_revision: str
    current_revision: str
    local: list[Project]
    external: list[Project]


class ProjectActivity(StrictModel):
    project: Project
    entries: list[SearchResult]
    latest_next_steps: list[SearchResult] = Field(max_length=5)
    unresolved_blockers: list[SearchResult] = Field(max_length=5)


class BackupConfigurationInput(StrictModel):
    enabled: bool
    remote_url: str | None = None
    branch: str = "main"
    private_confirmed: bool


class BackupStatus(StrictModel):
    enabled: bool
    configured: bool
    destination_label: str | None = None
    private_confirmed: bool
    branch: str = "main"
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    pending_commits: int = Field(ge=0)
    last_error: str | None = None


class Settings(StrictModel):
    workspace_path: str
    theme: Literal["system", "light", "dark"]
    model_path: str | None = None
    model_executable: str = "llama-cli"


class SettingsPatch(StrictModel):
    theme: Literal["system", "light", "dark"] | None = None
    model_path: str | None = None
    model_executable: str | None = None


class Error(StrictModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class RepositoryInput(StrictModel):
    path: str = Field(min_length=1)
    remote_name: str | None = None
    display_name: str | None = None


class RefreshInput(StrictModel):
    start: date = Field(alias="from")
    end: date = Field(alias="to")
    repository_ids: list[str] | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class UserContextInput(StrictModel):
    text: str | None = Field(default=None, max_length=500)
