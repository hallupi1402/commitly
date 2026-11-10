# Implementation Plan: Commitly Semantic Daily Work Report

**Branch**: `001-work-journal` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

## Summary

Commitly will read pushed commits from explicitly selected repositories, analyze
their diffs and changed documents on the user's machine, and write one Markdown
report per date. Each report contains Tóm tắt, Điểm chính, Chi tiết, and a source
log that ties prose back to repositories, commits, and paths. The app remains
local-first: no source content is sent to an AI/cloud service and no resident
analysis or backup daemon is added.

## Technical Context

**Frontend**: Vite, React, TypeScript, Tailwind CSS.

**Backend**: Python FastAPI, managed with `uv`.

**Git access**: Git CLI with bounded subprocess execution.

**Report storage**: Human-readable Markdown, one dated report file.

**Analysis**: Local semantic analysis and local document text extraction; exact
runtime/model is a blocking research decision before implementation.

**Platform**: Linux desktop; API and UI bind to loopback.

**Offline**: Browsing reports and analyzing cached Git objects works without
network after local dependencies/model are installed; fetching newer remote refs
needs network.

**Testing**: pytest for Git, extraction, analysis boundaries, Markdown persistence,
conflicts, and APIs; Vitest/React Testing Library for report UI and accessibility.

## Architecture and Decisions

### Selected repositories and Git evidence

- Register only repositories explicitly selected by the user; do not scan the
  filesystem. Use `origin` by default, otherwise ask the user to select one
  configured remote.
- On explicit refresh, attempt `git fetch` without push or merge. Analyze commits
  reachable from the newest available remote-tracking refs. If fetch fails or the
  app is offline, use cached refs and display their last successful verification
  time.
- Include commits authored by repository-local `user.email`; when it is missing,
  show a setup error instead of including every contributor.
- Use canonical Git common-directory identity plus full commit object ID for
  deduplication. Preserve author timestamps and group by local calendar date.
- Keep fetch failures isolated per repository. Previously imported evidence for a
  failed source remains; successful repositories can still update.

### Local semantic analysis

- Backend prepares bounded evidence from each selected commit: subject, changed
  paths, numstat, diff hunks, and relevant changed-file context. For changed paper
  and document files, extract text locally only for supported formats.
- A local analysis runtime produces the three prose sections in Vietnamese and
  associates each claim with commit IDs and changed paths. It receives only
  user-selected repositories' changed content; it does not scan unrelated files.
- The generated prose is saved with its evidence log in the daily Markdown report.
  Unsupported files and analysis failures keep the factual log and mark prose
  analysis unavailable for the affected item.
- Never send content to a hosted model. Do not add a resident model server. The
  model/runtime must be chosen after a small feasibility study of Linux hardware,
  memory, latency, package/model size, license, and Vietnamese/code quality. If no
  compact local option meets acceptable quality, return with options for user
  review rather than quietly adding a cloud dependency.
- The analyzer must not state that a developer read a paper merely because the
  file was committed. Describe the observed file change and its extracted content.
  It must avoid claims not anchored in source evidence and label uncertain
  interpretation.

### Markdown storage and safe writes

- Store `reports/YYYY-MM-DD.md` under the user's XDG data workspace outside the
  source checkout. Use versioned metadata comments for item IDs, commit IDs, and
  evidence links; keep report prose readable as Markdown.
- Allow at most one simple user context line per date. Render it in Điểm chính
  with clear user attribution; it is not fed to the semantic analyzer as proof of
  Git activity.
- Reuse existing safe-write and conflict logic where it fits. Atomic writes and
  external modification detection protect a complete report; unsupported formats
  and failed safe writes preserve the original and candidate for recovery.
- Do not add a database, search index, remote backup, or structured manual-entry
  subsystem to this baseline. Date-based report browsing is local.

### API and UI

- The existing same-origin FastAPI app owns Git, local model, document extraction,
  and filesystem access. Vite/React presents Today report, its one-line context
  input, report history, and selected repositories.
- API operations: list/add/remove repositories, refresh a date range, list saved
  report dates, read a daily report and its evidence, and add/update/remove one
  context line with revision protection.
- Refresh returns per-repository fetch and analysis status. Errors are sanitized;
  credentials from remote URLs are never exposed.
- Do not include Projects, Reflection, journal Git backup, systemd timers, or
  structured editing flows from the earlier manual-entry-first scope in baseline
  navigation.

## Security and Data Safety

- Bind to loopback; validate origin/host for mutations.
- Use argument arrays, output/time limits, and no shell interpolation for Git.
- Treat repository content and documents as untrusted input. Bound files and
  excerpts sent to the local model; never evaluate repository code or execute
  hooks as part of analysis.
- Do not include obvious secret values or credential-bearing remote URLs in prose,
  logs, API errors, or report files. Keep private source data in local storage.
- A failed fetch or analysis cannot remove previously imported source evidence.
  A failed report write cannot destroy the saved report.
- The app may use network only to fetch explicitly selected Git remotes; it never
  pushes activity or report data.

## Delivery Phases

1. **Review gate**: Approve the new three-section semantic report scope and all
   linked design artifacts before modifying application code.
2. **Research spike (blocking)**: Evaluate local model/runtime and document text
   extraction against a small representative fixture of code and papers. Confirm
   quality, privacy, resource requirements, supported formats, and installation.
   If it cannot meet the local/offline constraints, return with a concrete
   constraint/options report before implementation.
3. **Foundation**: Define versioned report/evidence schema, selected repository
   configuration, local Git boundary, safe Markdown writes, and deterministic tests
   around model I/O using a stubbed analyzer.
4. **P1 — Generate reports**: Fetch/cached-ref discovery, diff and document
   extraction, local semantic analysis, evidence linkage, report rendering, and
   Today UI.
5. **P2 — Browse evidence**: Date history, report browsing, and source-log
   inspection; retain offline access. Search and rich manual editing are later scope.
6. **Acceptance**: Validate known code/document fixtures, unsupported file and
   fetch failures, offline generation, restart persistence, conflict safety, and
   keyboard/dark-mode behavior. Record only executed results.

## Project Structure

Reuse the existing `backend/` and `frontend/` layout. Candidate modules after the
research decision:

```text
backend/src/commitly/
├── git_activity.py       # selected repo validation, fetch, commit/diff evidence
├── document_text.py      # bounded local text extraction for supported formats
├── report_analysis.py    # local analyzer call and evidence-grounded output
├── reports.py            # Markdown report schema and safe persistence
└── api/                  # repository, refresh, and report contracts/routes
frontend/src/features/
├── today/                # narrative report and refresh status
├── journal/              # prior report browsing/search
└── repositories/         # explicit source selection
```

Exact module/runtime choices may change after the research spike, but no code work
starts before the review gate.

## Constitution Check

- **Work Journal First**: Report prose describes evidenced completed work.
- **Hybrid Capture**: Git is the automatic source; one short optional context line
  supplements activity Git cannot prove.
- **Local First / Markdown Native**: Analysis and reports stay local; the source
  of truth is readable Markdown; fetch is an explicit optional network update.
- **Data Safety**: Stable commit/report IDs, atomic writes, and external-edit
  protection are required.
- **Lightweight Architecture**: No database, remote AI service, resident analyzer,
  scheduled process, or feature outside report generation and review.
- **Incremental Delivery**: Research spike and P1 generation are separate gates;
  browsing follows independently.
- **Scope Discipline**: Local semantic analysis is included because the user
  explicitly requested prose explanations of code and document changes. AI
  reflections and cloud analysis remain out of scope.
- **Quality**: Use tests with known evidence fixtures, safe failure handling, and
  accessible report UI.

## Pre-Implementation Review Gate

Before any application code changes, the user must review and approve `spec.md`,
`plan.md`, `tasks.md`, `data-model.md`, `contracts/openapi.yaml`, `research.md`,
and `quickstart.md`. The current implementation reflects an earlier scope and is
not evidence that semantic reports already work. The local model/runtime research
spike is the first implementation-phase task after approval; it does not authorize
cloud processing.
