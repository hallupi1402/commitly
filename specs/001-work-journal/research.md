# Research: Commitly — Work Journal First

**Date**: 2026-11-10
**Status**: Decisions resolved for Phase 1 design

## Decisions

### Local web application boundary

- **Decision**: Build the frontend with Vite, React, TypeScript, and Tailwind CSS.
  In development, Vite proxies `/api` to FastAPI. In normal use, one FastAPI process
  bound to loopback serves both the built frontend and `/api/v1` on the same origin.
- **Rationale**: This keeps browser data local, avoids a separate production web
  server and cross-origin configuration, and does not require network access after
  dependencies have been installed. Vite produces static production assets, and
  FastAPI documents serving those assets with SPA route fallback.
- **Alternatives considered**: Keep Vite running in production, or run separate
  frontend and API servers. Both add a long-running process and more origin/port
  configuration without adding MVP value.
- **Security constraint**: Bind the backend and Vite development server to
  `127.0.0.1`; do not enable wildcard CORS or LAN binding. Validate Host and Origin
  for write requests. No user authentication is added for this single-user local
  application.
- **Sources**: [FastAPI frontend serving](https://fastapi.tiangolo.com/tutorial/frontend/),
  [FastAPI OpenAPI generation](https://fastapi.tiangolo.com/tutorial/first-steps/),
  [Vite server options](https://vite.dev/config/server-options),
  [Vite guide](https://vite.dev/guide/),
  [Tailwind CSS Vite integration](https://tailwindcss.com/docs/installation/using-vite).

### Python and JavaScript toolchains

- **Decision**: Use `uv` for the Python project and lockfile, Uvicorn as the single
  local ASGI process runner, and npm with a
  committed lockfile for the Vite frontend. Target Python 3.12 or newer and Node.js
  22.12 or newer. Use current compatible FastAPI/Pydantic releases and Tailwind CSS
  v4; lock exact dependency versions when implementation begins.
- **Rationale**: `uv` manages project dependencies and a reproducible lockfile.
  Vite documents Node.js 22.12+ as a supported line. npm is the smallest default
  because no JavaScript package manager was specified.
- **Alternatives considered**: Adding a workspace manager or additional package
  manager would increase setup without improving the two-project MVP.
- **Sources**: [uv project guide](https://docs.astral.sh/uv/guides/projects/),
  [Vite compatibility](https://vite.dev/guide/),
  [Tailwind CSS Vite integration](https://tailwindcss.com/docs/installation/using-vite).

### Markdown schema and persistence

- **Decision**: Store one `journals/YYYY-MM-DD.md` file per local calendar date and
  a `projects.md` registry in the user's separate journal workspace. Use documented
  Markdown headings and delimited HTML comments containing JSON metadata for stable
  IDs, timestamps, type, project IDs, and schema version. User-authored descriptions,
  details, references, and reflections remain ordinary Markdown sections. Parse the
  comment metadata with Python's standard `json` module; do not add a database or a
  Markdown/YAML parsing dependency.
- **Rationale**: This keeps the source of truth human-readable and directly editable,
  while preserving stable machine fields without duplicating entry text. A version
  field allows the parser to reject unsupported formats with a clear recovery error.
- **Alternatives considered**: YAML front matter would add a parser dependency and
  put more of the journal's content into metadata; a database would create a second
  source of truth; raw Markdown headings without IDs cannot safely identify entries
  across edits.

### Atomic writes and external edits

- **Decision**: Serialize Commitly writers with a per-file advisory lock, write the
  full candidate to a same-directory temporary file, flush and `fsync` it, then use
  Linux `renameat2(RENAME_EXCHANGE)` to atomically exchange it with the existing
  journal. Hash the displaced file now held at the temporary path and compare that
  exact revision to the client's `If-Match`. If it differs, exchange the files back,
  save the local and external versions as Markdown conflict copies, and return a
  conflict without committing either version. For a new file, use
  `RENAME_NOREPLACE`. After a successful exchange, `fsync` the containing directory.
- **Rationale**: A check followed by ordinary replacement has a race: an external
  editor can save between them. Exchanging first lets Commitly inspect the exact file
  displaced by the atomic operation, including an edit by a process that ignores
  Commitly's lock. Same-directory temporary files keep the operation on one
  filesystem. The user-selected merged/kept resolution is written only after another
  revision check and exchange.
- **Alternatives considered**: In-place writes can truncate files on failure.
  Advisory locking plus a pre-write hash has a compare/replace race because Markdown
  editors do not take Commitly's lock. A database or immutable revision store would
  add a second source of truth and more complexity.
- **Fail-safe behavior**: `renameat2` exchange is available on supported Linux
  kernels/filesystems. If the call or filesystem flag is unsupported, Commitly keeps
  the candidate as a recovery Markdown file, reports that the workspace cannot be
  written safely, and does not fall back to an unguarded replacement.
- **Sources**: [Python `os`](https://docs.python.org/3/library/os.html),
  [Python `tempfile`](https://docs.python.org/3/library/tempfile.html),
  [Linux `renameat2(2)`](https://man7.org/linux/man-pages/man2/rename.2.html),
  [Linux `fsync(2)`](https://man7.org/linux/man-pages/man2/fsync.2.html),
  [Linux `flock(2)`](https://man7.org/linux/man-pages/man2/flock.2.html).

### Git backup and scheduling

- **Decision**: Keep the journal workspace outside the Commitly source checkout and
  initialize a separate Git repository there when backup is enabled. A systemd user
  timer activates a short-lived backup service daily with `OnCalendar=daily` and
  `Persistent=true`. The job detects changes using stable porcelain status output,
  commits locally only when files changed, then pushes an explicit branch/ref only
  to the configured remote after the user confirms that destination is private.
- **Rationale**: The separate repository prevents journal commits from entering the
  public source repository. A one-shot timer meets daily scheduling without a
  resident process. Local commits survive remote, authentication, or network errors
  and can be pushed on a later run. No force push, reset, automatic remote merge, or
  empty commit is used.
- **Scheduling assumption**: The persistent timer runs while the user's systemd
  manager is active even when the UI is closed. If the manager is stopped, a missed
  run is caught up when the user logs in again. Scheduling requires an active user
  manager; do not enable linger by default. Remote or credential failures retain
  local commits, report a sanitized error, and retry on the next scheduled run. The
  service runs the installed backup entry point and reads the same workspace
  configuration as the UI.
- **Credentials**: Reuse the user's configured Git credential helper; do not put
  tokens or passwords in systemd unit environment variables or Commitly settings.
  Report authentication failures without logging credentials.
- **Alternatives considered**: A resident application daemon is unnecessary.
  Pushing every keystroke would expose unfinished work and create excessive commits.
  Automatic pull/merge could rewrite or conflict with personal journals.
- **Sources**: [systemd timer units](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html),
  [systemd execution environment](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html),
  [Git status](https://git-scm.com/docs/git-status),
  [Git commit](https://git-scm.com/docs/git-commit),
  [Git push](https://git-scm.com/docs/git-push).

### API and verification

- **Decision**: Define `/api/v1` operations in `contracts/openapi.yaml`; model
  requests and responses with FastAPI/Pydantic and keep generated OpenAPI aligned
  with the checked-in contract. Use pytest and FastAPI's test client for persistence,
  API, search, conflict, and Git failure tests. Use Vitest and React Testing Library
  for frontend interaction and keyboard/dark-mode requirements. Render user Markdown
  with `react-markdown` using its safe defaults and without enabling raw HTML.
- **Rationale**: A checked-in contract makes the local API reviewable before code
  exists. The chosen test tools cover the requested behavior without an additional
  browser automation service.
- **Alternatives considered**: Duplicating generated client code would add a build
  step and drift risk; a full end-to-end browser stack is not needed for the first
  increment, though it can be added if component and API tests miss integration bugs.
- **Sources**: [FastAPI OpenAPI generation](https://fastapi.tiangolo.com/tutorial/first-steps/),
  [react-markdown safety and rendering](https://github.com/remarkjs/react-markdown).

## Resolved Planning Assumptions

- npm is the frontend package manager because none was specified.
- The app is Linux-only for the MVP because the requested scheduled backup uses a
  systemd user timer.
- The journal is single-user and local; no numeric concurrency or service-availability
  target is required.
- Search scans dated Markdown journals directly. No index or database is added
  unless measured personal journal sizes show that file scanning is insufficient.
  Acceptance uses 1,000 seeded entries and checks that every expected match and its
  source date are returned; no response-time promise is set.
- Missed daily backups are handled by the persistent user timer; the GUI does not
  need to remain open, but the user systemd manager must be active for a run.
