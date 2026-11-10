# Implementation Plan: Commitly — Work Journal First

**Branch**: `001-work-journal` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification and user-approved stack in the planning request.

## Summary

Build a Linux-first, local web application for recording completed work in
human-readable Markdown. A Vite/React/TypeScript/Tailwind frontend talks to one
loopback-only FastAPI process. Daily journals and project records live in a user
workspace outside the source checkout; Python performs revision checks and atomic
file exchange on supported Linux filesystems. A short-lived systemd user service
makes daily local Git commits
and pushes only to a user-selected destination confirmed as private. There is no
database, remote application service, or resident backup daemon.

## Technical Context

**Language/Version**: Python 3.12+; TypeScript with Node.js 22.12+

**Primary Dependencies**: FastAPI, Pydantic, and Uvicorn; Vite, React, and Tailwind
CSS v4; npm for frontend packages; `react-markdown` for safe rendering of notes;
`uv` for Python dependencies; Git CLI and systemd user units for backup scheduling.
Use Vitest and React Testing Library for frontend tests. Use Python standard-library
JSON, filesystem, hashing, and subprocess facilities for the Markdown store, with a
small `ctypes` wrapper for Linux `renameat2` exchange operations.

**Storage**: One Markdown file per local calendar date plus a Markdown project
registry in the default user workspace. Settings and backup status are small JSON
files in the user's XDG config/state directories. The workspace is outside the
Commitly source checkout and becomes its own Git repository only when backup is
enabled. No database.

**Testing**: `pytest` with FastAPI's test client for API, persistence, editing,
search, conflict, and backup failure coverage; Vitest and React Testing Library for
frontend interactions, keyboard use, and dark mode. Contract tests compare the
generated FastAPI OpenAPI document with `contracts/openapi.yaml`.

**Target Platform**: Linux desktop with systemd user services; Node.js 22.12+ and
Python 3.12+ for development. The installed application runs locally in the user's
browser and does not require internet access for journal operations.

**Project Type**: Local-first web application with a Python API and static frontend.

**Performance Goals**: Keep capture and date browsing local and synchronous from the
user's perspective. Search correctness is validated against 1,000 seeded entries;
the MVP makes no response-time promise. Search scans the user's Markdown journal
directly; do not add an index or database before measurements show a need.

**Constraints**: Bind the API and development server to loopback only. Do not enable
wildcard CORS or expose the app on a LAN. Core journal operations make no network
calls. Git pushes require a configured, user-selected destination and explicit
private confirmation. Do not push to Commitly's public source repository. Preserve
data on write failures and external-edit conflicts; fail closed if the workspace
filesystem cannot perform safe atomic exchanges. No AI, task-board, analytics,
collaboration, cloud-authentication, or real-time-sync features.

**Scale/Scope**: One developer and one local workspace. Search and history operate
over that workspace's Markdown files; multi-user concurrency and hosted service
scale are out of scope.

## Constitution Check

**Initial gate — PASS**

- **Work Journal First**: Entry descriptions capture completed work; next steps and
  blockers remain separately labeled context.
- **Hybrid Capture**: Description-only entries are the minimal create path; optional
  details do not block saving.
- **Local First**: The API, frontend, persistence, search, projects, and reflections
  run on the local machine. Only an explicitly configured Git push needs network.
- **Markdown Native**: Markdown files remain the journal and project source of truth.
- **Data Safety**: Stable IDs, revision checks, same-directory temporary files,
  atomic exchange, and recoverable conflict copies protect saved content.
- **Lightweight Architecture**: No database or service dependency is introduced.
  The user-requested systemd timer runs a one-shot backup job, not a resident daemon.
- **Incremental Delivery**: The task plan will follow the four prioritized user
  stories and validate each independently.
- **Scope Discipline**: Only specified MVP capabilities are included.
- **Quality and Security**: Automated tests, actionable errors, keyboard access,
  dark mode, loopback binding, and private-by-confirmation backup are design gates.

**Post-design consistency — PASS**: `data-model.md`, API contracts, test layers,
and `quickstart.md` preserve the same boundaries. No constitution exception is
required. The separate pre-implementation review gate below must still pass before
coding starts.

## Pre-Implementation Review Gate

Before Phase 1 or any application code begins, reviewers must review the
specification, this plan, and `tasks.md`. Resolve open requirements-quality
findings in the source artifacts, then have the reviewer confirm the checklist
criteria are satisfied. This review gate precedes all implementation phases; it
is not a checkpoint after US1.

## Architecture and Flow

1. The React client calls the same-origin `/api/v1` service. In development, Vite
   proxies API requests to FastAPI; normal use serves the static Vite build from
   FastAPI.
2. FastAPI validates requests, uses Pydantic response models, and delegates journal
   reads/writes to the Markdown store. All mutation requests carry the journal's
   current revision and full working copy. A stale revision is detected against the
   exact file displaced by atomic exchange; Commitly restores the current file,
   preserves both versions as Markdown recovery copies, returns `409 Conflict`, and
   waits for the user's explicit comparison/selection/merge.
3. Journal state lives under `$XDG_DATA_HOME/commitly/journal` (falling back to
   `~/.local/share/commitly/journal`). Preferences use `$XDG_CONFIG_HOME/commitly`;
   backup run status uses `$XDG_STATE_HOME/commitly`. These paths are outside the
   source checkout; Settings displays the resolved workspace location.
4. The timer activates a separate backup command, whether or not the UI is open.
   The command commits changed journal Markdown locally, then pushes an explicit
   branch only to the configured private-confirmed remote. Failures leave local
   commits intact and update backup status for the API to display.

## Delivery Phases

1. **Setup**: Establish the frontend/backend project layout, lockfiles, test
   commands, local configuration paths, and loopback-only application startup.
2. **Foundation**: Implement the Markdown schema/parser, atomic persistence,
   revision-aware conflict preservation, shared API models, and baseline tests.
3. **US1 — Capture and Continue Work (P1)**: Description-only capture, entry types
   and optional details, editing/deletion, timeline, keyboard save, restart
   persistence, and external-edit conflict resolution.
4. **US2 — Review Today and Prior Context (P2)**: Local date dashboard, prior
   context, and optional editable daily reflections.
5. **US3 — Find Work and Manage Projects (P3)**: Date history, search and filters,
   project lifecycle/activity, and resolved-blocker summaries.
6. **US4 — Back Up and Configure the Journal (P4)**: Settings, destination
   confirmation, user timer/service, status reporting, daily local commit, remote
   push, and offline/authentication failure handling.
7. **Polish**: Cross-story keyboard/accessibility review, dark mode, error/empty
   states, and acceptance validation against the spec.

## Project Structure

### Documentation

```text
specs/001-work-journal/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── openapi.yaml
```

### Source Code

```text
backend/
├── pyproject.toml
├── uv.lock
├── src/commitly/
│   ├── app.py                 # FastAPI app and static frontend mount
│   ├── api/
│   │   ├── routes.py          # /api/v1 routes
│   │   └── schemas.py         # Request/response models
│   ├── journal.py             # Markdown parser, renderer, revisions, atomic writes
│   ├── projects.py            # Project registry operations
│   ├── search.py              # Local Markdown search and filters
│   ├── backup.py              # Git backup command and status
│   └── config.py              # XDG paths and preferences
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── package.json
├── package-lock.json
├── vite.config.ts
└── src/
    ├── app/
    ├── features/
    │   ├── today/
    │   ├── capture/
    │   ├── journal/
    │   ├── projects/
    │   └── settings/
    ├── shared/
    └── test/

systemd/
├── commitly-backup.service
└── commitly-backup.timer
```

**Structure Decision**: Keep one frontend and one Python backend in the same
repository. The backend owns all file and Git access; the frontend receives only
validated API data. The systemd units invoke the backend's one-shot backup entry
point. The personal workspace is a separate path and Git repository, never the
application checkout.
