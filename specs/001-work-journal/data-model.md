# Data Model: Commitly — Work Journal First

## Storage Boundaries

- The journal workspace is `$XDG_DATA_HOME/commitly/journal`, or
  `~/.local/share/commitly/journal` when `XDG_DATA_HOME` is unset. Settings are kept
  under `$XDG_CONFIG_HOME/commitly` and backup run status under
  `$XDG_STATE_HOME/commitly`, each falling back to the corresponding `~/.config` or
  `~/.local/state` path.
- The journal workspace is outside the application source checkout. When Git backup
  is enabled, this workspace has its own Git metadata; Commitly does not use the
  source checkout's repository or remote.
- Journal and project records are Markdown. Settings and operational backup status
  are JSON and are not journal source data. No database or search index is used.

## Markdown Schema Version 1

The parser accepts UTF-8 Markdown with a journal header, delimited entry blocks,
optional reflection sections, and a trailing schema version. Metadata comments use
JSON so the parser can use Python's standard library; user content remains ordinary
Markdown.

```markdown
<!-- commitly:journal v1 date=2026-11-10 -->
# Daily Journal — 2026-11-10

<!-- commitly:entry {"id":"<uuid>","created_at":"<RFC3339 timestamp>","type":"work","project_id":null,"blocker_resolved_at":null} -->
### Description
Fixed the parser error on startup.

### Tags
- parser

### Result
The journal now opens with the saved entries.

### Next step
Add a regression case for an empty journal.

### References
- https://example.invalid/issue/123

### Notes
Additional Markdown notes.
<!-- /commitly:entry <uuid> -->

## Reflection
### Accomplishments
...
### Blockers
...
### Next steps
...
```

Rules:

- The filename is `journals/YYYY-MM-DD.md`; its date must match the header and every
  entry's assigned local calendar date. A date-specific entry cannot be moved by
  editing its timestamp.
- Each entry start comment contains a stable UUID, immutable RFC 3339 UTC creation
  timestamp, lowercase type (`work`, `note`, or `blocker`), and optional project UUID.
  The Markdown body contains the required description and optional tags, result,
  blocker, next step, references, and detailed notes. A blocker resolution timestamp
  is stored in the JSON metadata when present.
- Entry blocks are ordered by creation timestamp, then UUID for a stable tie-break.
  Missing, duplicate, malformed, or unsupported metadata is a read error; the
  application does not silently rewrite the file or generate replacement IDs.
- Reflection is optional and belongs to one local journal date. Its three fields are
  independently optional Markdown sections.
- An archived project's name and ID remain available to render existing entries.
  New entries cannot select archived projects.

## Entities

### Journal Entry

| Field | Type | Rule |
|---|---|---|
| `id` | UUID | Generated once by the client at first save; unique across the workspace; never changes on edit |
| `created_at` | RFC 3339 timestamp | Generated automatically in UTC at first save; preserved on edit |
| `date` | Local calendar date | Determined at creation; used to select the daily file |
| `type` | `work` / `note` / `blocker` | Defaults to `work` |
| `description` | Markdown text | Required after whitespace trimming |
| `project_id` | UUID or null | Optional; must reference a project, including archived historical projects |
| `tags` | List of strings | Optional; normalized for duplicate comparison |
| `result` | Markdown text or null | Optional |
| `blocker` | Markdown text or null | Optional |
| `blocker_resolved_at` | RFC 3339 timestamp or null | Null means unresolved; resolution preserves the entry |
| `next_step` | Markdown text or null | Optional |
| `references` | List of strings | Optional user-provided URLs or labels |
| `notes` | Markdown text or null | Optional detailed notes |

### Daily Journal

One `journals/YYYY-MM-DD.md` file, containing the entries for that local date and
one optional reflection. The file's exact bytes have a SHA-256 revision used for
optimistic concurrency checks and ETags.

### Daily Reflection

| Field | Type | Rule |
|---|---|---|
| `date` | Local calendar date | One reflection per date |
| `accomplishments` | Markdown text or null | Optional |
| `blockers` | Markdown text or null | Optional |
| `next_steps` | Markdown text or null | Optional |

### Project

Projects are stored in `projects.md` as Markdown blocks with JSON metadata:

```markdown
<!-- commitly:projects v1 -->
# Projects

<!-- commitly:project {"id":"<uuid>","created_at":"<RFC3339 timestamp>","archived_at":null} -->
## Commitly
<!-- /commitly:project <uuid> -->
```

| Field | Type | Rule |
|---|---|---|
| `id` | UUID | Generated once by the client and stable |
| `name` | String | Required after whitespace trimming; unique among active projects, case-insensitive |
| `created_at` | RFC 3339 timestamp | Generated in UTC and immutable |
| `archived_at` | RFC 3339 timestamp or null | Null means active; archiving preserves history |

### Journal Conflict

A conflict contains the expected revision, current external Markdown, submitted
local draft, and a generated conflict ID. Before returning `409`, the backend saves
both versions as Markdown under `.commitly/conflicts/YYYY-MM-DD/<conflict-id>/`.
The client may compare, choose, or combine content; the backend writes the chosen
resolution only when the current external revision still matches. Recovery copies
remain until the resolution succeeds.

### Backup Configuration and Status

Configuration is stored separately from journal Markdown and contains the optional
remote URL, explicit private-destination confirmation, and configured branch/ref.
It contains no Git credentials. Status records last attempt, last
successful push, pending local commits, and a sanitized last error. The systemd
service and API read/write the same status file using atomic replacement.

## Write and Conflict Rules

1. Reads return the journal revision as a quoted SHA-256 `ETag`.
2. Every mutation sends `If-Match` for the revision the user edited. A stale revision
   triggers `409 Conflict`; the submitted draft and current file are saved before
   the conflict is shown.
3. Commitly serializes its own writers with a per-file advisory lock and writes a
   uniquely named, synced temporary file beside the target. For an existing file,
   it uses Linux `renameat2(RENAME_EXCHANGE)` to atomically exchange the temporary
   file and target, then hashes the displaced file. If that hash differs from the
   expected revision, it exchanges back, saves both copies, and returns a conflict.
   For a missing file, it uses `RENAME_NOREPLACE` so an externally created file is
   never silently replaced. It syncs the containing directory after a successful
   write.
4. The app does not overwrite malformed or unsupported Markdown. It leaves the file
   untouched and returns an actionable recovery error.
5. Project registry edits use the same revision and conflict protections as daily
   journal edits.
6. If the Linux filesystem does not support the required atomic exchange/create
   operation, the app preserves the candidate as a recovery file and reports an
   actionable error. It does not fall back to an unguarded replacement.
