# Feature Specification: Commitly — Work Journal First

**Feature Branch**: `001-work-journal` (spec identifier; no branch hook is configured)

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: Commitly — Work Journal First MVP, as described in the product overview, functional requirements, non-goals, and quality expectations.

## Clarifications

### Session 2026-11-10

- Q: After a user configures a Git backup destination, should scheduled backups automatically push to it only if the user confirms it is private? → A: Scheduled backups automatically push daily to the user-selected destination after the user confirms it is private.
- Q: When Commitly detects that a journal changed outside the app while the user also has unsaved edits, how should they resolve the conflict? → A: Show both versions, save neither automatically, and let the user compare, combine, or explicitly choose a version while both originals remain recoverable until the conflict is resolved.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture and Continue Work (Priority: P1)

As a developer, I want to record completed work with minimal effort and reopen my
journal later, so that I preserve useful technical context and can continue tomorrow.

**Why this priority**: Capturing and retaining completed work is the product's core
value. Without it, the rest of the journal has nothing to review.

**Independent Test**: Create a one-line entry without optional details, close and
reopen Commitly, and confirm the entry and its timestamp are still present.

**Acceptance Scenarios**:

1. **Given** the Today Dashboard is open, **When** the user enters a description and
   saves it, **Then** a Work entry appears in today's timeline with an ID and timestamp.
2. **Given** the user is composing an entry, **When** they press Ctrl+Enter or
   Cmd+Enter, **Then** the entry is saved without requiring another control.
3. **Given** a saved entry, **When** the user edits or deletes it, **Then** the
   timeline and saved journal reflect that action, an edited entry keeps its ID and
   creation timestamp, and unrelated entries remain intact.
4. **Given** Commitly is reopened after saving, **When** the user views that journal
   date, **Then** the entry, ID, timestamp, and optional details are preserved.
5. **Given** the journal is opened without network access, **When** the user creates,
   reads, edits, or deletes an entry, **Then** the operation completes offline.
6. **Given** the user is composing an entry, **When** they choose Note or Blocker and
   add any optional fields, **Then** the chosen type and supplied details are saved
   while omitted fields remain optional.
7. **Given** a journal changed outside Commitly while the user has unsaved edits,
   **When** the conflict is detected, **Then** both versions are shown, neither is
   saved over automatically, and both remain recoverable while the user compares,
   combines, or chooses a version and explicitly saves the resolution.

---

### User Story 2 - Review Today and Prior Context (Priority: P2)

As a developer, I want to see today's work and relevant previous context, so that I
can pick up ongoing work and reflect before ending the day.

**Why this priority**: Reviewing context turns individual captures into a continuing
work journal and supports the product vision.

**Independent Test**: Add entries on two dates, open today's dashboard, and confirm
the current local date, today's timeline, and clearly dated prior next steps and
blockers are available; add and edit a reflection without making it mandatory.

**Acceptance Scenarios**:

1. **Given** the Today Dashboard is open, **When** the user views it, **Then** it
   displays the current local date and today's entries in timestamp order.
2. **Given** prior journals contain entries, **When** the user opens today's
   dashboard, **Then** the dashboard shows prior next steps and blockers with their
   source dates.
3. **Given** the user wants to reflect, **When** they enter accomplishments,
   blockers, or next steps, **Then** the reflection is saved for that date and can
   be edited later.
4. **Given** the user has no reflection for today, **When** they view or leave the
   day, **Then** Commitly does not require a reflection or mark the day incomplete.
5. **Given** the local date changes, **When** the user opens the dashboard, **Then**
   it shows the new local date and that date's journal.

---

### User Story 3 - Find Work and Manage Projects (Priority: P3)

As a developer working across projects, I want to browse and search past entries and
see project activity, so that I can recover details without manually opening every
journal.

**Why this priority**: History and project context make accumulated entries useful
over time, after the basic capture and review journeys work.

**Independent Test**: Create dated entries across two projects and entry types, then
browse by date, search by keyword, filter by project and type, and review one
project's activity and current next steps/blockers.

**Acceptance Scenarios**:

1. **Given** entries exist on multiple dates, **When** the user browses dates and
   opens a prior journal, **Then** entries and reflection for the selected date are
   shown and prior entries can be edited.
2. **Given** journal text contains a search term, **When** the user searches for it,
   **Then** matching entries are shown with their dates; a search with no matches
   gives a clear empty state.
3. **Given** entries have projects and types, **When** the user applies project or
   entry-type filters, **Then** only matching entries are shown and filters can be
   cleared.
4. **Given** a project is active, **When** the user creates, renames, or archives it,
   **Then** its activity history remains available and archiving does not delete
   associated entries.
5. **Given** a project has recorded next steps or blockers, **When** the user opens
   its activity history, **Then** the latest next steps and unresolved blockers are
   shown with their source entries and dates.
6. **Given** a blocker is no longer active, **When** the user marks it resolved,
   **Then** it is no longer listed as an unresolved blocker and remains in history.
7. **Given** the user creates an entry without choosing a project, **When** it is
   saved, **Then** it remains available as an unassigned entry.

---

### User Story 4 - Back Up and Configure the Journal (Priority: P4)

As a developer, I want a private, configurable Git backup and clear settings, so
that I can protect my journal and understand where it is stored and whether it is
backed up.

**Why this priority**: Backup and settings protect and explain the journal, while
depending on the capture and persistence journeys being useful first.

**Independent Test**: Configure a private backup destination, save journal changes,
and verify a scheduled backup reports its status; make the destination unavailable
and confirm pending commits remain available for a later retry.

**Acceptance Scenarios**:

1. **Given** journal changes exist and the user has selected and confirmed a private
   backup destination, **When** the daily backup runs, **Then** changes are committed
   locally and automatically pushed to that destination, and the status and result
   are visible.
2. **Given** there are no journal changes since the last backup, **When** the daily
   backup runs, **Then** no empty commit is created.
3. **Given** the backup destination is unavailable, **When** a backup or sync fails,
   **Then** the error is shown and local unpushed commits remain available for retry.
4. **Given** a backup destination is not configured, **When** the user opens backup
   settings, **Then** Commitly shows that backup is not configured and does not push
   journal data anywhere.
5. **Given** a backup destination is configured but not confirmed as private,
   **When** a scheduled backup runs, **Then** Commitly does not push journal data and
   asks the user to confirm the destination before the first push.
6. **Given** a destination is configured, **When** Commitly backs up journal data,
   **Then** it uses only the user-configured destination and never pushes to
   Commitly's public source repository.
7. **Given** the user opens Settings, **When** they review configuration, **Then**
   the local workspace location, basic preferences, and backup destination and status
   are displayed.

### Edge Cases

- A description containing only whitespace cannot be saved; the user receives a
  clear prompt and no empty entry is created.
- A save fails because the journal file changed outside Commitly: Commitly shows the
  user's unsaved changes and the external changes for comparison, preserves both
  originals, and requires an explicit choice or combined resolution before saving.
- A write is interrupted: the previously saved journal remains readable and intact.
- Two entries have the same timestamp: both remain distinct by stable ID and appear
  in a consistent order.
- An entry refers to an archived project: its historical association remains visible,
  but the archived project is not offered for new entries.
- A daily backup is due while Commitly is closed or its destination is unavailable:
  it is deferred until Commitly next runs or the destination is available; existing
  local commits are retained.
- The user has no entries, no search matches, or no project activity: the relevant
  screen provides a clear empty state and an appropriate next action.
- The user uses only a keyboard or enables dark mode: all primary workflows remain
  operable and readable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Today Dashboard MUST display the current local date, a prominent
  Quick Capture input, today's entries in a timeline, prior context, and optional
  end-of-day reflection.
- **FR-002**: Users MUST be able to save an entry with only a non-empty text
  description. New entries MUST default to Work type.
- **FR-003**: Users MUST be able to choose Work, Note, or Blocker as an entry type
  and optionally add a project, tags, result, blocker, next step, references, or
  detailed Markdown notes.
- **FR-004**: Each entry MUST receive a stable ID and creation timestamp
  automatically. Editing an entry MUST preserve its ID and creation timestamp.
  Users MUST be able to edit and delete entries, including entries on prior dates.
- **FR-005**: Users MUST be able to save from Quick Capture with Ctrl+Enter or
  Cmd+Enter.
- **FR-006**: Users MUST be able to browse journals by date, open prior daily
  journals, search entries by keyword, and filter entries by project and type.
- **FR-007**: Users MUST be able to create, rename, and archive projects, associate
  entries with projects, and leave entries unassigned. Archiving a project MUST NOT
  delete its entries.
- **FR-008**: Project activity MUST show associated history, latest next steps, and
  unresolved blockers. Users MUST be able to mark a blocker resolved; resolution
  MUST preserve the blocker in history.
- **FR-009**: Users MUST be able to record and edit daily reflection fields for
  accomplishments, blockers, and next steps. A reflection MUST NOT be required to
  complete or leave a day.
- **FR-010**: Daily journals MUST be saved as human-readable Markdown files and
  preserve entry IDs, timestamps, and optional details across application restarts.
- **FR-011**: Capture, browse, search, edit, delete, project, and reflection
  operations MUST work without network access.
- **FR-012**: To prevent unintended overwrites, before saving over a journal changed
  outside Commitly, the product MUST detect the conflict and show both versions
  without saving either over the other. Both originals MUST remain recoverable until
  the user compares, combines, or explicitly chooses a version and saves the
  resolution. Interrupted or failed writes MUST NOT damage the last saved journal.
- **FR-013**: Commitly MUST support a scheduled daily Git backup of journal changes,
  MUST automatically push commits to the configured and privacy-confirmed
  destination, MUST skip empty commits, and MUST retain local unpushed commits after
  backup or sync failures.
- **FR-014**: Users MUST be able to configure a backup destination and view backup
  and sync status and errors. With no destination configured or before the user
  confirms the destination is private, Commitly MUST NOT push journal data. It MUST
  never automatically push journal data to Commitly's public source repository.
  Destinations MUST be user-selected and private by default.
- **FR-015**: Settings MUST display the local workspace location and allow users to
  configure basic preferences, including dark mode.
- **FR-016**: Empty states and errors MUST explain the current state and a useful next
  action. All primary workflows MUST be operable by keyboard and the interface MUST
  support dark mode.

### Key Entities *(include if feature involves data)*

- **Journal Entry**: A dated record of completed work, a note, or a blocker. Has a
  stable ID, timestamp, description, type, and optional project, tags, result,
  blocker, next step, references, and detailed Markdown notes.
- **Daily Journal**: The human-readable collection of entries and an optional
  reflection for one local calendar date.
- **Daily Reflection**: Optional accomplishments, blockers, and next steps associated
  with a journal date; editable after creation.
- **Project**: A user-created grouping for entries with a name and active or archived
  state. Archiving does not remove its history.
- **Blocker**: An entry or recorded blocker with unresolved or resolved state, used
  to show current blockers while preserving historical context.
- **Backup Configuration**: The user's selected backup destination and its visible
  configuration and sync status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In usability acceptance checks, a user can save a one-line Work entry
  from the Today Dashboard in no more than two actions after opening it.
- **SC-002**: 100% of saved entries in the persistence acceptance suite retain their
  IDs, timestamps, and content after closing and reopening the application.
- **SC-003**: All core journal operations in the acceptance suite complete with
  network access disabled.
- **SC-004**: In external-change and interrupted-write acceptance scenarios, zero
  previously saved or externally changed journal content is silently lost.
- **SC-005**: Users can find a seeded matching entry through keyword search and
  project/type filtering, and open a prior daily journal, without opening unrelated
  journal files manually.
- **SC-006**: In keyboard-only acceptance checks, users can complete capture, browse,
  edit, and reflection workflows; the same workflows remain readable in dark mode.
- **SC-007**: When a backup destination is unavailable, all local unpushed commits
  remain available and the user can see the failure status and error.

## Assumptions

- Dates and timestamps are displayed in the user's local time; a daily journal is
  associated with the local calendar date when the entry is created.
- A daily scheduled backup runs when Commitly is available. If Commitly is closed or
  the destination is unavailable at the scheduled time, the run is deferred until
  Commitly next runs or the destination becomes available; no always-on background
  process is required.
- A backup destination is not configured by default. Users select their destination
  and confirm it is private before the first automatic push; remote backup is limited
  to that configured destination.
- A blocker is unresolved until the user explicitly marks it resolved. Resolving it
  hides it from unresolved-blocker summaries but does not remove it from journal
  history.
- Keyword search covers entry descriptions and optional text fields. The product
  does not require searching reflection text or archived project names in the MVP.
- Archived projects remain available for viewing existing history but cannot be
  assigned to new entries.
- The MVP is for one individual using a local workspace; collaboration, cloud
  authentication, real-time synchronization, and the other listed non-goals are out
  of scope.

## Out of Scope

- AI assistant or AI-generated reflections
- Kanban boards or complex task management
- Time tracking
- Multi-user collaboration
- Cloud authentication or real-time synchronization
- Advanced analytics
- Full Idea Vault
- Automatic publishing or pushing of journal data to Commitly's public source
  repository
