# Feature Specification: Commitly — Semantic Daily Work Report

**Feature Branch**: `001-work-journal`

**Created**: 2026-11-10

**Status**: Draft for user scope review

## Product Brief

Commitly is a personal, local-first developer work journal. Its main purpose is to
record what the developer actually accomplished and produce a useful daily report
in natural language, so they can review progress and resume tomorrow.

**Product vision**: Capture today. Continue tomorrow.

**Primary user**: An individual developer working across selected Git repositories.

The baseline reads commits already pushed to the selected repositories and analyzes
their code changes locally. It also reads the contents of newly added or changed
paper/document files where supported. It turns this evidence into a Vietnamese
daily report with three sections: a short overall summary, accomplishment bullets,
and a more detailed explanation. A source log records each repository, commit,
changed path, and change statistics.

The analysis must explain what the code changes do, not just repeat commit subjects
or count lines. It must keep claims tied to their source files and commits. Git alone
cannot prove that the developer read a paper or understood it: when a paper file is
added, the report must say that the file was added/updated and summarize its
contents, rather than assert that the user read it unless the commit evidence says
so.

## Baseline Scope

The baseline includes:

1. Explicit registration of local Git repositories.
2. User-triggered fetch of configured remote refs without pushing, then discovery
   of commits reachable from those refs for a selected local date range. Cached
   refs can be processed offline and are marked with their last verification time.
3. Local analysis of commit metadata, code diffs, and relevant changed files. For
   changed paper/document files, extract readable text locally and summarize its
   content where extraction is supported.
4. One Markdown report per local date, with exactly these report sections:
   - **Tóm tắt**: a short natural-language overview of the day's work.
   - **Điểm chính**: concise bullets for accomplishments such as a feature
     implemented or a paper/document added and its relevant subject.
   - **Chi tiết**: a clearer explanation of what changed and why, grouped by
     repository and work item.
5. A **Log nguồn** section attached to each report with repository name/path,
   commit ID/time/subject, changed paths, and additions/deletions where known.
6. Optional one-line context for work Git cannot prove. It appears in Điểm chính
   as user-reported, not Git-derived, context.
7. Browsing saved reports offline. Reports are stored as human-readable Markdown
   outside the public application checkout.

The baseline uses semantic analysis locally on the user's machine. It MUST NOT send
source code, diffs, paper contents, or report text to an AI/cloud service. The
specific local model/runtime is a plan-time research decision that must be settled
before implementation; it must not introduce a resident background service.

The baseline does not monitor the working tree, terminal, editor, or user activity;
it does not infer uncommitted work; it does not add structured journal fields,
projects, reflections, scheduled Git backup, or AI-generated personal reflections.

## User Scenarios & Testing

### User Story 1 — Generate a Natural-Language Daily Report (P1)

As a developer, I want Commitly to analyze the code and documents changed by my
pushed commits and explain my work in plain language, so I can receive a meaningful
daily report instead of a list of commit subjects and file counts.

**Why this priority**: A report that explains the work is the core product outcome.

**Independent Test**: Use disposable selected repositories with known commits:
implement a small behavior change with tests, add a paper with known content, and
make an unrelated metadata-only change. Refresh a known date range and verify the
Vietnamese report has the three requested sections, explains the behavior and paper
content accurately, does not invent an action, and links every work item to source
commit and file evidence.

**Acceptance Scenarios**:

1. **Given** the user has selected a repository with pushed commits, **When** they
   refresh a date range, **Then** Commitly fetches the configured remote without
   pushing and analyzes commits reachable from the remote refs.
2. **Given** a commit changes code behavior and tests, **When** its report is
   generated, **Then** the prose explains the behavior implemented and relevant
   tests using the changed code as evidence, rather than merely repeating the
   subject or line counts.
3. **Given** a commit adds or changes a readable paper/document, **When** it is
   analyzed, **Then** the report names the file and summarizes its main content
   from locally extracted text. It does not claim the user read or understood it
   based only on the file change.
4. **Given** a report is generated, **When** the user opens it, **Then** it has
   Tóm tắt, Điểm chính, and Chi tiết sections, followed by Log nguồn with source
   repository, commit, path, and change facts.
5. **Given** a report sentence describes an accomplishment, **When** the user
   follows its evidence, **Then** the sentence links to one or more source commits
   and changed paths that support it. Uncertain interpretation is labelled as
   uncertain or omitted.
6. **Given** the same commit is found through repeated refreshes or multiple refs,
   **When** reports are regenerated, **Then** it is represented once per canonical
   repository identity and full commit object ID.
7. **Given** a local analysis model is installed and the user is offline,
   **When** cached remote refs and Git objects are available, **Then** Commitly can
   generate and read reports without network access.
8. **Given** remote fetch fails, **When** the user refreshes, **Then** the report
   retains previously imported items for that repository, marks its remote state
   unverified, and reports a useful error.
9. **Given** Commitly cannot analyze a file type, **When** it builds a report,
   **Then** it still records factual Git activity, marks that file's explanation as
   unavailable, and does not fail the entire daily report.
10. **Given** work is not represented by Git, **When** the user adds an optional
    one-line context note, **Then** it appears in Điểm chính labelled as
    user-reported and persists with that date's report.

### User Story 2 — Browse Reports and Source Evidence (P2)

As a developer, I want to browse reports from previous dates and inspect their
source logs, so I can recover what changed and continue work later.

**Independent Test**: Generate reports on multiple dates and repositories, open a
prior report offline, and verify that summary, bullets, details, and log evidence
remain readable and traceable.

**Acceptance Scenarios**:

1. **Given** reports exist for multiple dates, **When** the user selects a date,
   **Then** the report and source logs for that local date are displayed.
2. **Given** a report item names a repository or file, **When** the user opens its
   source details, **Then** the commit ID, repository path, changed paths, and
   change counts are available.
3. **Given** no report exists for a date, **When** the user opens it, **Then** a
   clear empty state offers a refresh action.
4. **Given** the application is offline, **When** a saved report is opened,
   **Then** all three prose sections and source logs remain readable and no current
   remote check is claimed.

## Functional Requirements

- **FR-001**: The Today view MUST display the local date, the generated daily
  report's three prose sections, its source log, refresh status, and a refresh
  action.
- **FR-002**: Users MUST explicitly select local Git repositories. Commitly MUST
  NOT search the filesystem or register repositories without user action.
- **FR-003**: On explicit refresh, Commitly MUST attempt to fetch each selected
  repository's configured remote refs without pushing. It MUST analyze commits
  reachable from the latest available remote refs within the selected local date
  range and authored by the repository's configured `user.email`. Cached refs MUST
  remain usable offline and show their last successful remote verification time.
- **FR-004**: Commitly MUST analyze changed code locally, including relevant diff
  context and changed source files, and explain what behavior changed in plain
  Vietnamese, plus why where the source evidence supports that explanation.
  Repeating commit subjects and line counts alone does not satisfy this requirement.
- **FR-005**: For supported added or changed paper/document files, Commitly MUST
  extract text locally and include a concise content summary tied to the file.
  Commitly MUST distinguish a file being added or changed from evidence that the
  user read it.
- **FR-006**: Every report MUST contain the sections Tóm tắt, Điểm chính, Chi tiết,
  and Log nguồn. The first three provide natural-language report prose; Log nguồn
  records the repository, local path, commit ID, timestamp, subject, changed paths,
  and additions/deletions where available.
- **FR-007**: Each Git-derived statement in Tóm tắt, Điểm chính, and Chi tiết
  MUST link to supporting commit IDs and changed paths. User-provided context MUST
  be labelled as such. Unsupported claims MUST be omitted; uncertain
  interpretations MUST be labelled as uncertain.
- **FR-008**: Commitly MUST deduplicate report evidence by canonical repository
  identity and full commit object ID.
- **FR-009**: Daily reports MUST be stored as human-readable, versioned Markdown
  files outside the public source checkout and remain readable after restart.
- **FR-010**: Before replacing a report changed outside Commitly, the application
  MUST preserve both versions and require explicit resolution. If safe atomic
  writes are unavailable, the original MUST be left untouched and an actionable
  error shown.
- **FR-011**: Semantic analysis, document extraction, and report generation MUST
  run locally. Source code, diffs, paper content, and reports MUST NOT be sent to
  an AI/cloud service. The baseline MUST NOT install a resident background service.
- **FR-012**: Report browsing and analysis from locally cached Git refs and objects
  MUST work offline after local analysis dependencies are installed. Fetching newer
  remote refs requires a network connection.
- **FR-013**: A failed repository fetch MUST preserve that repository's previous
  report evidence, mark the repository unverified, identify the error, and allow
  successful repositories to refresh independently.
- **FR-014**: Unsupported file types or analysis errors MUST leave factual source
  logs available, mark the affected explanation as unavailable, and MUST NOT
  prevent other commits from being reported.
- **FR-015**: Empty states, repository errors, parsing errors, model-unavailable
  states, and persistence failures MUST explain the issue and a useful next step.
- **FR-016**: The report and source-log flows MUST be keyboard operable with visible
  focus, accessible names, announced status, and dark-mode support.
- **FR-017**: Users MUST be able to add, edit, or delete an optional one-line
  context note without filling structured fields. The report MUST visibly mark it
  as user-reported and keep it distinct from Git-derived evidence.

## Edge Cases

- A repository is invalid, lacks a remote, or has no configured author email:
  report the configuration problem without scanning more paths or including all
  authors by default.
- A repository has multiple remotes: choose `origin` if present; otherwise require
  an explicit selection and display the selected remote name.
- A fetch fails for one repository while others succeed: preserve that source's
  existing items and status, while allowing successful repositories to update.
- A changed document is a PDF or another binary format: use local extraction only
  when supported; otherwise show its path and unavailable-analysis state.
- A code change is ambiguous or its surrounding context is insufficient: omit a
  strong claim or mark the interpretation uncertain; retain exact source evidence.
- A commit contains secrets or large generated/vendor files: do not include obvious
  secret values or unbounded generated contents in prose; keep paths and factual
  metadata in the source log and mark content analysis skipped where needed.
- A root commit has no parent: analyze its added files as the initial tree.
- A renamed/deleted/binary/unusually named file is changed: preserve the path
  accurately and do not report misleading line counts.
- A report is opened offline or its local analysis runtime is unavailable: saved
  report text remains readable; a new analysis is marked unavailable rather than
  silently replaced by an empty report.
- A report file is externally edited, malformed, or a write is interrupted:
  preserve existing content and the candidate report and provide a recovery error.

## Out of Scope and Later Branches

- Reading uncommitted working-tree changes, terminal history, IDE/editor events,
  shell history, issue trackers, or other activity sources.
- Remote AI/cloud analysis, cloud authentication, multi-user collaboration, and
  real-time synchronization.
- Structured manual journal fields, rich projects, project activity, daily reflections,
  scheduled Git backup of journal data, systemd timer, time tracking, task boards,
  advanced analytics, and a full Idea Vault.
- AI-generated reflections or unsupported claims about developer intent.
- Automatic background monitoring or remote fetching.

## Success Criteria

- **SC-001**: In a fixture with known code behavior changes, report bullets explain
  the implemented behavior and cite the relevant commit and changed paths; they do
  not merely repeat commit subjects or diff statistics.
- **SC-002**: In a fixture containing a known paper/document, the report names the
  changed file and correctly summarizes its key content without claiming the user
  read it based solely on the Git change.
- **SC-003**: 100% of accomplishment bullets in the acceptance fixture link to a
  source commit and one or more changed paths; uncertain items are labelled or
  omitted.
- **SC-004**: Repeating refresh and restarting produces one report item per
  repository+commit ID and preserves all four report sections in Markdown.
- **SC-005**: With local analysis dependencies installed, cached Git activity can
  be analyzed and existing reports read while offline; the UI shows last verified
  remote time and never claims an offline fetch succeeded.
- **SC-006**: A failed fetch, unsupported file, or analysis failure leaves
  previously saved evidence readable and does not prevent other source items from
  appearing.
- **SC-007**: External-edit and interrupted-write acceptance tests lose zero
  previously saved report content.
- **SC-008**: In keyboard-only and dark-mode checks, users can refresh, browse a
  report, inspect its evidence, and understand success, stale, and error states.
- **SC-009**: A one-line user context note can be added in one input and one save
  action, remains after restart, and is labelled user-reported in the report.

## Assumptions

- The default report language is Vietnamese; commit subjects and paths remain in
  their original form.
- “Daily” grouping uses the user's local calendar date derived from each commit's
  author timestamp; the source timestamp and offset are retained.
- A report is a grounded analysis of changed code and documents, not proof of every
  activity the user performed. Git cannot prove reading, reviewing, or intent.
- Semantic processing is local-only to satisfy the local-first principle and
  protect private source code. Local model/runtime and supported document formats
  must be researched before implementation.
- A user explicitly refreshes selected repositories. Commitly fetches but never
  pushes to activity-source remotes.
