# Commitly MVP Quickstart and Validation

This guide describes how the planned application will be built and validated. It
does not install or run application code; implementation starts only after the
specification, this plan, and the generated task list have been reviewed and the
pre-implementation review gate in `tasks.md` has passed. Do not defer that review
until after the MVP story has been implemented.

## Prerequisites

- Linux with a systemd user manager for scheduled backup validation.
- Python 3.12 or newer and `uv`.
- Node.js 22.12 or newer and npm.
- Git CLI.

## Install Development Dependencies

From the repository root:

```sh
uv sync --project backend --dev
npm ci --prefix frontend
```

Dependency installation may use the network. Once installed, all journal
development and runtime checks below are local; network access is only needed to
test an explicitly configured Git remote.

## Run in Development

In one terminal, start the loopback-only FastAPI service:

```sh
uv run --project backend uvicorn commitly.app:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, start Vite with its `/api` proxy:

```sh
npm --prefix frontend run dev -- --host 127.0.0.1
```

Open the loopback address printed by Vite. Neither server should bind to `0.0.0.0`
or expose the journal to the local network.

## Automated Checks

```sh
uv run --project backend pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run build
```

The backend suite covers Markdown round-trip and validation, stable IDs and
timestamps, atomic exchange failure, external-edit conflicts, CRUD, project and
reflection persistence, search/filter behavior, and backup commits/push failures.
The contract suite compares the FastAPI-generated OpenAPI document with
[`contracts/openapi.yaml`](contracts/openapi.yaml). Frontend checks cover Quick
Capture, keyboard submission, editing flows, empty/error states, keyboard access,
and dark mode.

## Acceptance Walkthroughs

1. **Capture and restart**: Save a one-line entry with the default Work type. Confirm
   it appears in today's timeline. Stop and restart the app, reopen the same date,
   and confirm its ID, creation timestamp, text, and optional fields remain.
2. **Keyboard and offline**: Save with Ctrl+Enter and Cmd+Enter on their respective
   platforms. Disable network access and create, browse, search, edit, and delete
   entries; all local operations must still complete.
3. **External Markdown conflict**: Open a daily Markdown file in a text editor and
   change it after the app loaded the same journal. Attempt an app edit. Confirm the
   API reports a conflict, preserves both versions, and the UI offers compare, choose,
   or combine before explicit save.
4. **Search and projects**: Seed entries across dates, entry types, and projects.
   Search by keyword, filter by project/type, open a past date, and confirm archived
   project history and unresolved blocker summaries are retained.
5. **Git backup success**: Use a disposable local bare Git repository configured as
   the private test destination. Confirm privacy in Settings, create journal changes,
   run the backup job, and confirm a local commit and remote push. Run it again
   without changes and confirm no empty commit appears.
6. **Git backup failure**: After making a local backup commit, make the remote
   unavailable or reject a push. Confirm the commit remains locally, status exposes
   a useful error and pending commit count, and a later successful run pushes the
   retained commit without reset, cleanup, or force push.
7. **Scheduled backup**: Install the user timer and one-shot service, inspect the
   next run with `systemctl --user list-timers`, and confirm the timer catches up
   after a missed activation when the user manager next starts. Linger remains
   disabled by default.
8. **Private paths and binding**: Confirm the default journal workspace is under the
   user's data directory and outside the source checkout; Settings displays the
   resolved workspace path. Confirm the app and development server bind only to
   loopback.
