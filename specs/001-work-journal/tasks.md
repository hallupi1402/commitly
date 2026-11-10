---
description: "Executable implementation tasks for the Commitly MVP"
---

# Tasks: Commitly — Work Journal First

**Input**: Design documents in `/specs/001-work-journal/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml`, and `quickstart.md`

**Tests**: Included because automated tests are required by the specification and constitution.

**Organization**: Tasks are grouped by the four prioritized user stories. Story tests are written before story implementation; the shared storage safety layer is foundational.

## Pre-Implementation Review Gate (Required; Not a Coding Task)

Before starting T001 or any application code, review `spec.md`, `plan.md`, and
this task list. Resolve open requirements-quality findings in the source
artifacts, then have the reviewer confirm the criteria in
`checklists/mvp-quality.md`. Checklist markers are reviewer-owned and must only
be changed by the reviewer. This gate occurs before Phase 1 and must not be
deferred until after US1.

## Format: `[ID] [P?] [Story] Description`

- **[P]** marks tasks that can proceed in parallel because they touch separate files and have no unfinished dependency.
- **[Story]** maps implementation work to the corresponding specification user story; Setup, Foundational, and Polish tasks have no story label.
- Every task names its target file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create reproducible backend/frontend projects and runnable local app scaffolding.

- [ ] T001 Create the Python 3.12+ `uv` project, runtime/dev dependencies, and pytest configuration in `backend/pyproject.toml`.
- [ ] T002 Generate and commit the resolved Python dependency lockfile in `backend/uv.lock`.
- [ ] T003 [P] Create the React, TypeScript, Vite, Tailwind CSS v4, Vitest, and React Testing Library scripts/dependencies in `frontend/package.json`.
- [ ] T004 Generate and commit the frontend dependency lockfile in `frontend/package-lock.json`.
- [ ] T005 Configure Vite's React/Tailwind plugins, loopback dev host, `/api` proxy, and test environment in `frontend/vite.config.ts`.
- [ ] T006 Create the FastAPI app entry point, API router mount, static frontend serving, SPA fallback, and loopback-only run configuration in `backend/src/commitly/app.py`.
- [ ] T007 Configure XDG data, config, and state locations with home-directory fallbacks and reject a workspace inside the source checkout in `backend/src/commitly/config.py`.
- [ ] T008 Add pytest shared temporary-workspace fixtures and FastAPI test-client setup in `backend/tests/conftest.py`.
- [ ] T009 Add Vitest and Testing Library setup with accessible DOM matchers in `frontend/src/test/setup.ts`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared Markdown and safe-write primitives required by every story that mutates or reads journal data.

**Checkpoint**: No story work begins until schema parsing, revision checks, recoverable conflicts, common API errors, and foundational safety tests are in place.

- [ ] T010 [P] Add unit tests for Markdown schema v1 parsing/rendering, malformed/unsupported metadata, duplicate IDs, stable timestamp/UUID ordering, and optional fields in `backend/tests/unit/test_journal_markdown.py`.
- [ ] T011 [P] Add unit tests for atomic create/exchange, fsync/write failure preservation, unsupported `renameat2` fail-closed behavior, and external edit conflict recovery in `backend/tests/unit/test_atomic_store.py`.
- [ ] T012 Implement schema v1 journal/project metadata validation, Markdown parsing/rendering, and immutable entry identity rules in `backend/src/commitly/journal.py`.
- [ ] T013 Implement same-directory synced temporary writes, advisory writer locks, `renameat2(RENAME_EXCHANGE)`/`RENAME_NOREPLACE`, revision hashing, and recoverable conflict snapshots in `backend/src/commitly/journal.py`.
- [ ] T014 Add shared Pydantic request/response models and validation for journal entries, projects, reflections, conflicts, settings, and backup status in `backend/src/commitly/api/schemas.py`.
- [ ] T015 Add `/api/v1` router registration, consistent actionable error responses, request Host/Origin validation for writes, and ETag/If-Match handling in `backend/src/commitly/api/routes.py`.
- [ ] T016 [P] Add an OpenAPI contract test comparing FastAPI's generated schema with `specs/001-work-journal/contracts/openapi.yaml` in `backend/tests/contract/test_openapi_contract.py`.

---

## Phase 3: User Story 1 — Capture and Continue Work (Priority: P1) 🎯 MVP

**Goal**: Capture completed work with one line, preserve it in Markdown, and safely edit/delete entries across restarts.

**Independent Test**: Save a description-only entry, restart/reload the service, and confirm its Work type, ID, timestamp, and text persist; edit/delete it, exercise keyboard save, and verify an external edit conflict preserves both versions until explicit resolution.

### Tests for User Story 1

> Write tests first and confirm they fail before implementing the corresponding behavior.

- [ ] T017 [P] [US1] Add API tests for description-only save, default Work type, optional-field validation, immutable ID/timestamp on edit, delete, persistence across reload, and stale ETag conflict in `backend/tests/integration/test_journal_entries.py`.
- [ ] T018 [P] [US1] Add conflict API tests proving both original Markdown versions remain recoverable and resolution requires a current external revision in `backend/tests/integration/test_journal_conflicts.py`.
- [ ] T019 [P] [US1] Add frontend tests for quick capture, optional detail disclosure, Ctrl+Enter/Cmd+Enter save, entry edit/delete, and conflict comparison/resolution in `frontend/src/features/capture/capture.test.tsx`.

### Implementation for User Story 1

- [ ] T020 [US1] Implement entry creation/update/delete over daily Markdown snapshots and enforce the schema constraints: `id` is “Generated once by the client at first save; unique across the workspace; never changes on edit”; `created_at` is “Generated automatically in UTC at first save; preserved on edit”; `date` is “Determined at creation; used to select the daily file”; `type` is “Defaults to `work`”; `description` is “Required after whitespace trimming”; `project_id` is “Optional; must reference a project, including archived historical projects”; `tags` are “Optional; normalized for duplicate comparison”; `result`, `blocker`, `next_step`, and `notes` are “Optional”; `blocker_resolved_at` is “Null means unresolved; resolution preserves the entry”; and `references` are “Optional user-provided URLs or labels” in `backend/src/commitly/journal.py`.
- [ ] T021 [US1] Implement GET/PUT `/journals/{date}`, conflict inspection/resolution, and ETag response handling per `contracts/openapi.yaml` in `backend/src/commitly/api/routes.py`.
- [ ] T022 [US1] Implement the Quick Capture form with required trimmed description, default Work type, and optional project/tags/result/blocker/next-step/references/Markdown notes in `frontend/src/features/capture/QuickCapture.tsx`.
- [ ] T023 [US1] Implement today's entry timeline with stable timestamp-then-ID ordering and inline edit/delete actions in `frontend/src/features/today/EntryTimeline.tsx`.
- [ ] T024 [US1] Implement journal API client calls with ETag retention and explicit 409 conflict draft handling in `frontend/src/shared/journalApi.ts`.
- [ ] T025 [US1] Assemble the capture-first Today screen, save feedback, and keyboard submission in `frontend/src/features/today/TodayPage.tsx`.
- [ ] T026 [US1] Implement conflict comparison and explicit keep-current/keep-draft/combined-resolution save while retaining recovery originals until success in `frontend/src/features/capture/ConflictResolution.tsx`.

**Checkpoint**: The P1 capture journey works offline, survives restart, and cannot silently overwrite an externally changed journal.

---

## Phase 4: User Story 2 — Review Today and Prior Context (Priority: P2)

**Goal**: Show the current local day, prior next steps/blockers with dates, and an optional editable reflection.

**Independent Test**: Seed entries on today and earlier dates; verify the current local date and today's order, dated prior context, and create/edit a reflection without requiring one to leave the day.

### Tests for User Story 2

- [ ] T027 [P] [US2] Add API tests for local-date `/today` data, dated prior next-step/blocker context, and optional reflection persistence/editing in `backend/tests/integration/test_today_reflection.py`.
- [ ] T028 [P] [US2] Add Today dashboard tests for date rollover, prior-context source dates, empty state, and optional reflection editing in `frontend/src/features/today/TodayPage.test.tsx`.

### Implementation for User Story 2

- [ ] T029 [US2] Implement local-date today aggregation, timestamp-ordered entries, and prior unresolved blockers/next steps with source dates in `backend/src/commitly/journal.py`.
- [ ] T030 [US2] Implement GET `/today` and reflection read/write through the revision-protected daily journal contract; `accomplishments`, `blockers`, and `next_steps` are each “Optional” in `backend/src/commitly/api/routes.py`.
- [ ] T031 [US2] Implement the optional accomplishments, blockers, and next-steps reflection editor with explicit save state in `frontend/src/features/today/DailyReflection.tsx`.
- [ ] T032 [US2] Integrate local date display, prior-context section, current-day refresh, and reflection editor in `frontend/src/features/today/TodayPage.tsx`.

**Checkpoint**: Current and prior-day context is readable, reflections are editable, and no completion gate requires reflection.

---

## Phase 5: User Story 3 — Find Work and Manage Projects (Priority: P3)

**Goal**: Browse dated journals, search/filter entries, and maintain project activity without losing archived history.

**Independent Test**: Seed dated entries for two projects and multiple types; browse prior dates, find a matching phrase, filter by project/type, archive a project, and verify its historical entries and current next steps/unresolved blockers remain available.

### Tests for User Story 3

- [ ] T033 [P] [US3] Add API tests for date browsing, keyword search across entry text fields, project/type filters, and no-match results in `backend/tests/integration/test_journal_search.py`.
- [ ] T034 [P] [US3] Add API tests for project create/rename/archive, active-name uniqueness, retained archived associations, blocker resolution, and latest activity summaries in `backend/tests/integration/test_projects.py`.
- [ ] T035 [P] [US3] Add frontend tests for date navigation, search/filter clearing, project lifecycle, archived history visibility, and empty states in `frontend/src/features/journal/JournalPage.test.tsx`.

### Implementation for User Story 3

- [ ] T036 [US3] Implement project Markdown registry parsing and revision-protected create/rename/archive; enforce project `id` as “Generated once by the client and stable”, `name` as “Required after whitespace trimming; unique among active projects, case-insensitive”, `created_at` as “Generated in UTC and immutable”, and `archived_at` as “Null means active; archiving preserves history”; retain historical ID/name lookup in `backend/src/commitly/projects.py`.
- [ ] T037 [US3] Implement direct Markdown search over descriptions and optional text fields plus date/project/type filters without an index in `backend/src/commitly/search.py`.
- [ ] T038 [US3] Implement GET/PUT `/projects`, project activity, and GET `/entries/search` routes including source dates and blocker resolution in `backend/src/commitly/api/routes.py`.
- [ ] T039 [US3] Implement date navigation and prior-day journal/reflection browsing with entry edit access in `frontend/src/features/journal/JournalPage.tsx`.
- [ ] T040 [US3] Implement keyword search, project/type filters, clear-filter controls, and no-match state in `frontend/src/features/journal/JournalSearch.tsx`.
- [ ] T041 [US3] Implement project create/rename/archive forms and per-project activity, latest next steps, and unresolved blocker summaries in `frontend/src/features/projects/ProjectsPage.tsx`.
- [ ] T042 [US3] Add project selection that excludes archived projects for new entries while showing archived associations on existing entries in `frontend/src/features/capture/ProjectSelect.tsx`.

**Checkpoint**: Search, history, project summaries, and blocker resolution work offline; archiving never removes entry history.

---

## Phase 6: User Story 4 — Back Up and Configure the Journal (Priority: P4)

**Goal**: Display settings and backup state, then schedule private-confirmed Git commits/pushes while retaining local commits on failure.

**Independent Test**: Configure and confirm a disposable private Git destination, run backup and verify commit/push/status; run unchanged backup and verify no empty commit; make push fail and verify the local commit remains pending with an actionable status.

### Tests for User Story 4

- [ ] T043 [P] [US4] Add backup integration tests for changed-file commit, empty-commit skip, private confirmation gate, destination isolation, push failure retention, retry, and sanitized errors in `backend/tests/integration/test_backup.py`.
- [ ] T044 [P] [US4] Add Settings UI tests for workspace display, backup configuration/confirmation, status/error display, and dark-mode preference in `frontend/src/features/settings/SettingsPage.test.tsx`.

### Implementation for User Story 4

- [ ] T045 [US4] Implement separate-workspace Git initialization, changed-file detection, non-empty local commits, explicit configured-remote/branch push, failure status, and pending commit count in `backend/src/commitly/backup.py`.
- [ ] T046 [US4] Implement GET backup status, PUT backup configuration, and GET/PATCH basic settings with private-confirmation state and atomic status/config persistence in `backend/src/commitly/api/routes.py`.
- [ ] T047 [US4] Add a one-shot backup command entry point that reads workspace configuration and exits with a useful status in `backend/src/commitly/backup.py`.
- [ ] T048 [P] [US4] Add the systemd user backup service that invokes the installed one-shot command without embedding credentials in `systemd/commitly-backup.service`.
- [ ] T049 [P] [US4] Add the persistent daily systemd user timer without enabling linger by default in `systemd/commitly-backup.timer`.
- [ ] T050 [US4] Implement Settings UI displaying resolved local workspace path, basic preferences, private destination confirmation, and backup/sync errors in `frontend/src/features/settings/SettingsPage.tsx`.

**Checkpoint**: Scheduled backup commits only journal workspace changes, pushes only to the configured confirmed-private destination, and preserves unpushed commits after failures.

---

## Phase 7: Polish & Cross-Cutting Acceptance

**Purpose**: Verify the finished MVP against its cross-story safety, accessibility, offline, and quickstart expectations.

- [ ] T051 [P] Add shared accessible loading, error, confirmation, and empty-state components for user-facing workflows in `frontend/src/shared/Feedback.tsx`.
- [ ] T052 [P] Implement and test keyboard-visible focus, semantic labels, and dark-mode tokens across the app shell in `frontend/src/app/App.tsx`.
- [ ] T053 Verify loopback binding, no external requests for core workflows, and safe Markdown rendering without raw HTML in `backend/tests/integration/test_local_security.py`.
- [ ] T054 Run the complete backend/frontend test suites and production frontend build; record/fix failures against the commands in `specs/001-work-journal/quickstart.md`.
- [ ] T055 Validate all seven acceptance walkthroughs and map results to the user stories in `specs/001-work-journal/quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately. Backend and frontend setup tasks can proceed in parallel once their manifests are created.
- **Foundational (Phase 2)**: Depends on Setup; blocks all stories because every story uses the shared schemas, API handling, Markdown parser, and safe persistence.
- **US1 (Phase 3)**: Depends on Foundational and delivers the MVP capture/persistence path.
- **US2 (Phase 4)**: Depends on US1 journal read/write behavior for dated entries and reflections.
- **US3 (Phase 5)**: Depends on US1 entries and US2 date/reflection navigation; it extends these with project/history views.
- **US4 (Phase 6)**: Depends on the workspace persistence and settings infrastructure; backup uses the completed Markdown workspace. It may proceed after US1 and shared settings foundations, but final integration follows US3.
- **Polish (Phase 7)**: Depends on all four stories.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2; no dependency on another story.
- **US2 (P2)**: Uses US1's daily journal storage and timeline.
- **US3 (P3)**: Uses saved entries and date navigation from US1/US2; project/search behavior can be tested against seeded Markdown independently.
- **US4 (P4)**: Requires the user workspace and persisted Markdown from US1; backup tests use isolated temporary Git repositories.

### Parallel Opportunities

- Setup frontend tasks T003–T005 and backend project tasks T001–T002 can proceed in parallel after their target directories exist.
- Foundational tests T010–T011 and contract test T016 touch separate test files; write them alongside schema/API work, but do not begin story implementation until shared foundation is ready.
- Within each story, test files marked [P] are independent. Story UI components on different paths can be implemented independently after their API behavior is fixed.
- Systemd units T048–T049 are independent files and can be authored in parallel with backup UI work after the command/config contract is stable.
- Stories are delivered in priority order for the MVP; do not parallelize changes to shared `routes.py`, `TodayPage.tsx`, or `journal.py` without coordination.

### Parallel Example: User Story 1

```text
Task: T017 backend journal entry API tests in backend/tests/integration/test_journal_entries.py
Task: T018 backend conflict tests in backend/tests/integration/test_journal_conflicts.py
Task: T019 frontend capture tests in frontend/src/features/capture/capture.test.tsx
```

## Implementation Strategy

### MVP First

1. Pass the pre-implementation review gate above.
2. Complete Setup and Foundational phases.
3. Complete US1 and validate description-only capture, restart persistence, edit/delete, keyboard save, and conflict recovery against its independent test criteria before moving on.

### Incremental Delivery

1. Deliver US1 capture and safe persistence.
2. Add US2 daily context and optional reflection; retest earlier stories.
3. Add US3 history, search, and project activity; retest earlier stories.
4. Add US4 private Git backup and Settings; retest all core workflows offline and through backup failure scenarios.
5. Complete cross-cutting acceptance and quickstart checks.

## Notes

- Each story has independent acceptance criteria and automated tests.
- Schema constraints to preserve: entry `id` is a UUID unique across the workspace and never changes on edit; `created_at` is an immutable RFC 3339 UTC timestamp; `date` is fixed at creation; `type` is `work` / `note` / `blocker` and defaults to `work`; `description` is required after whitespace trimming; `project_id` is optional; blocker resolution is null until explicitly resolved.
- Project constraints to preserve: project IDs are stable UUIDs; names are non-empty after trimming and unique among active projects case-insensitively; `archived_at` is null while active; archived associations remain readable but cannot be newly assigned.
- Daily reflection fields `accomplishments`, `blockers`, and `next_steps` are independently optional.
- Do not introduce a database, search index, cloud service, AI behavior, task board, analytics, or real-time synchronization.
- Never use ordinary replacement if atomic exchange/create is unavailable; preserve recovery data and report the failure.
