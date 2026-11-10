---
description: "Tasks for Commitly's local semantic daily report baseline"
---

# Tasks: Commitly Semantic Daily Work Report

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`,
`contracts/openapi.yaml`, and `quickstart.md` in this directory.

**Pre-implementation gate**: The user must approve the report-first scope and
linked design artifacts before any application-code task starts. The earlier
manual-entry-first implementation must not be treated as completion evidence for
semantic report generation.

## Phase 0 — Scope and Design Review

- [X] T001 Review the three report sections, evidence log, Vietnamese output, local
  semantic analysis, paper/document behavior, and explicit non-goals in `spec.md`.
- [X] T002 Review data schema, API, privacy boundary, model research gate, phases,
  and acceptance walkthrough in the linked design artifacts.
- [X] T003 Record user approval before starting application code or model/runtime
  integration work.

## Phase 1 — Local Analysis Feasibility (After Approval; Blocking)

**Status note (2026-11-10):** User explicitly authorized implementation. The host
has no installed local model/runtime, so the code below provides a configurable
`llama-cli` adapter but does not complete T005's model-quality study. The MVP
remains not release-ready until T005–T007 are resolved against disposable fixtures.

- [ ] T004 Build a small disposable fixture with representative code diffs, tests,
  a paper/document with known contents, a binary/unsupported file, and a
  metadata-only change. Do not use personal/private source code.
- [ ] T005 Evaluate local model/runtime candidates for Vietnamese and code-change
  explanations against the fixture; measure factual grounding, unsupported claims,
  memory use, latency, model/package size, license, installation, and offline
  operation; record the result in `specs/001-work-journal/research.md`.
- [ ] T006 Evaluate local paper/document text extraction and limits for supported
  formats; record errors, maximum input policy, and the user-visible unsupported
  state in `specs/001-work-journal/research.md`.
- [ ] T007 If no local candidate can meet privacy, offline, and usable-quality
  constraints on the target Linux environment, stop before adding a cloud fallback
  and present concrete options for scope review.

## Phase 2 — Foundation

- [X] T008 Compare current app code with the approved design; record reusable
  modules and deferred old-scope screens in `docs/baseline-implementation-notes.md`.
- [X] T009 Define selected-repository config, canonical identity, remote selection,
  author matching, and sanitized Git errors in `backend/src/commitly/git_activity.py`.
- [X] T010 Define and test report Markdown v1, report/evidence/context IDs, source
  links, stable ordering, conflict preservation, and atomic writes in
  `backend/src/commitly/reports.py` and `backend/tests/unit/test_reports.py`.
- [ ] T011 Define bounded Git evidence extraction for commits, diffs, changed paths,
  and numstat in `backend/src/commitly/git_activity.py`; test roots, merges,
  renames, binary files, and unusual paths in
  `backend/tests/unit/test_git_activity.py`.
- [ ] T012 Define safe, bounded local document text extraction for the formats
  approved by T006 in `backend/src/commitly/document_text.py` and test malformed,
  oversized, and unsupported files in `backend/tests/unit/test_document_text.py`.
- [X] T013 Define and test the structured report-analysis input/output boundary
  with a stub analyzer in `backend/src/commitly/report_analysis.py` and
  `backend/tests/unit/test_report_analysis.py`; every generated claim carries
  evidence IDs.
- [X] T014 Add API models/routes for selected repositories, refresh status, report
  read/evidence, and one-line user context based on `contracts/openapi.yaml` in
  `backend/src/commitly/api/schemas.py` and `backend/src/commitly/api/routes.py`.
- [ ] T015 Align OpenAPI contract tests with response schemas and status behavior in
  `backend/tests/contract/test_openapi_contract.py`.

## Phase 3 — P1: Generate the Daily Report

### Tests first

- [ ] T016 [P] Add disposable Git remote tests for pushed reachability, author
  filtering, local-date grouping, cached offline refs, repeated refresh, partial
  fetch failure, and no-push behavior in
  `backend/tests/integration/test_git_activity.py`.
- [ ] T017 [P] Add deterministic analyzer tests using a stubbed local model for
  code behavior explanations, test changes, paper content, uncertain claims,
  evidence links, unsupported files, and secret exclusion in
  `backend/tests/integration/test_report_analysis.py`.
- [ ] T018 [P] Add API tests for report sections, source logs, one-line context
  create/edit/remove, partial repository failures, offline reads, and
  analysis-unavailable state in
  `backend/tests/integration/test_report_api.py`.
- [ ] T019 [P] Add UI tests for repository selection, refresh/progress/errors,
  three-section report rendering, one-line supplementary context, evidence
  navigation, and offline/stale status in
  `frontend/src/features/today/TodayPage.test.tsx`.

### Implementation

- [X] T020 Implement explicit repository registration and configured remote choice
  in `backend/src/commitly/git_activity.py`; do not scan outside selected paths.
- [X] T021 Implement fetch-without-push and query the latest available refs for
  matching author commits; fall back to cached refs and preserve last verification
  time when offline/fetch fails in `backend/src/commitly/git_activity.py`.
- [X] T022 Implement local diff and changed-file evidence collection and bounded
  document extraction for the formats established by T006 in
  `backend/src/commitly/git_activity.py` and
  `backend/src/commitly/document_text.py`.
- [X] T023 Implement grounded Vietnamese report generation with the three required
  sections, per-claim commit/path evidence, uncertainty handling, and graceful
  per-file analysis failures in `backend/src/commitly/report_analysis.py`.
- [X] T024 Persist deduplicated report content and source logs as versioned Markdown
  with atomic write and external-edit conflict protection in
  `backend/src/commitly/reports.py`.
- [X] T025 Implement repository, refresh, report, and source-evidence API routes
  with sanitized status and errors in `backend/src/commitly/api/routes.py`.
- [X] T026 Implement Today report UI and selected repository management with
  Tóm tắt, Điểm chính, Chi tiết, Log nguồn, optional one-line context, refresh
  status, keyboard access, and dark mode in `frontend/src/features/today/TodayPage.tsx` and
  `frontend/src/features/repositories/RepositoriesPage.tsx`.

**Checkpoint**: Known code and paper fixtures produce grounded Vietnamese report
prose and traceable source logs; no code or document content leaves the machine.

## Phase 4 — P2: Browse Previous Reports

- [ ] T027 [P] Add date browsing and report-content tests for prose and evidence
  paths across multiple dates in
  `backend/tests/integration/test_reports_history.py`.
- [ ] T028 [P] Add UI tests for prior-date browsing, source-log inspection,
  empty states, keyboard focus, and dark-mode readability in
  `frontend/src/features/journal/JournalPage.test.tsx`.
- [X] T029 Implement local report-date listing and report read APIs in
  `backend/src/commitly/api/routes.py` and `backend/src/commitly/reports.py`.
- [X] T030 Implement Journal history and source-log inspection UI in
  `frontend/src/features/journal/JournalPage.tsx`.

## Phase 5 — Acceptance

- [ ] T031 Run all declared backend/frontend tests, lint/type checks, and
  production builds; record only executed commands/results in
  `docs/verification-report.md`.
- [ ] T032 Complete quickstart walkthroughs for known code/paper fixtures, offline
  analysis, remote failure, unsupported document, restart persistence, external
  conflict, privacy boundary, keyboard use, and dark mode; record observed results
  in `docs/verification-report.md`.
- [ ] T033 Fix reproducible acceptance defects and rerun affected checks; list
  remaining gaps in `docs/verification-report.md`.

## Deferred Follow-up Branches

Uncommitted/worktree activity; terminal and IDE sources; report search; Projects;
Reflection; Git backup and systemd scheduling; remote AI; collaboration,
cloud sync, task boards, time tracking, analytics, and Idea Vault.
