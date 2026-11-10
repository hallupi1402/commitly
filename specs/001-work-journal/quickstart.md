# Commitly MVP Quickstart and Validation

This guide describes how to install, run, and validate the Commitly MVP. Journal
features work locally without network access after dependencies are installed.

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

To install the one-shot backup command and user timer after dependency setup:

```sh
uv tool install --editable ./backend
install -Dm644 systemd/commitly-backup.service ~/.config/systemd/user/commitly-backup.service
install -Dm644 systemd/commitly-backup.timer ~/.config/systemd/user/commitly-backup.timer
systemctl --user daemon-reload
systemctl --user enable --now commitly-backup.timer
```

The timer runs while the user manager is active, including with the UI closed.
`Persistent=true` catches up after the next login if the manager was stopped.
Linger remains disabled by default, and no credentials are placed in unit files.

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
3. **External file safety**: Edit a loaded daily journal and project registry outside
   the app, then attempt app saves. Confirm both conflicts preserve both versions and
   allow explicit resolution. Edit the journal again during resolution and confirm a
   new conflict preserves that edit. Confirm recovery copies are removed only after a
   successful resolution. Try malformed/unsupported Markdown; verify it stays intact
   and the error tells the user to copy and repair it manually.
4. **Search and projects**: Seed 1,000 entries across dates, entry types, and projects.
   Search and filter; verify every expected result and source date. Confirm Today shows
   up to five newest next steps and unresolved entry blockers across all dates, and
   project activity uses the same ordering. Rename and archive a project; verify old
   entries show its current name and archived label.
5. **Git backup success**: Use a disposable local bare Git repository configured as
   the test destination. In Settings, check “I confirm that this Git destination is
   private and appropriate for storing my personal journal.” This is a user assertion;
   Commitly does not verify remote privacy. Create journal changes,
   run the backup job, and confirm a local commit and remote push. Run it again
   without changes and confirm no empty commit appears.
6. **Git backup failure**: After making a local backup commit, make the remote
   unavailable or reject authentication. Confirm the commit remains locally, status
   exposes a sanitized error and pending count, and the next scheduled run pushes the
   retained commit without reset, cleanup, or force push. Confirm credentials are
   read from the Git credential helper and never stored in settings/service variables
   or logged.
7. **Scheduled backup**: Install the user timer and one-shot service, inspect the
   next run with `systemctl --user list-timers`, and confirm the timer catches up
   after a missed activation when the user manager next starts. Linger remains
   disabled by default.
8. **Private paths and accessibility**: Confirm the default journal workspace is
   under the user's data directory and outside the source checkout; Settings displays
   its read-only path. Confirm primary workflows have visible keyboard focus, named
   semantic controls, and announced save/error status. Confirm the app and development
   server bind only to loopback.
