# Data Model: Commitly Semantic Daily Work Report

## Storage Boundaries

- One `reports/YYYY-MM-DD.md` file per local report date, under the user's XDG data
  workspace and outside the public source checkout.
- Markdown is the source of truth. No database, cloud store, or search index.
- Selected repository configuration and refresh status are local application
  configuration; they contain no credentials.
- Analysis inputs/outputs remain local. Do not persist full patches or extracted
  full paper contents in report files; persist only explanations and provenance.

## Report Markdown Schema v1

```markdown
<!-- commitly:report v1 date=2026-11-10 -->
# Báo cáo công việc — 10/11/2026

## Tóm tắt
Hoàn thiện luồng xử lý xung đột khi file nhật ký bị sửa bên ngoài, đồng thời bổ
sung kiểm thử hồi quy cho API và giao diện. [evidence: <uuid>]

## Điểm chính
- Thêm bước so sánh và khôi phục khi file Markdown có chỉnh sửa bên ngoài.
  [evidence: <uuid>]
- Thêm `docs/example-paper.pdf`; nội dung trình bày về ... [evidence: <uuid>]
- Người dùng ghi: “Đọc paper X và ghi lại các ý chính.” [user-reported: <uuid>]

## Chi tiết
### Commitly
Luồng giải quyết xung đột giữ lại cả hai phiên bản và kiểm tra file lần nữa trước
khi lưu. Kiểm thử API và giao diện bao phủ đường đi này.

## Log nguồn
<!-- commitly:evidence {"id":"<uuid>","repo_id":"<stable-id>","commit_id":"<full-object-id>","authored_at":"<RFC3339 timestamp>"} -->
- Repo: commitly (`/home/user/src/commitly`)
- Commit: `abc123...` — Add conflict recovery · 14:32
- Thay đổi: `backend/store.py` (+12 / -3), `backend/tests/test_store.py` (+18 / -0)
<!-- /commitly:evidence <uuid> -->
<!-- commitly:context {"id":"<uuid>","created_at":"<RFC3339 timestamp>"} -->
- Ngữ cảnh do người dùng ghi: Đọc paper X và ghi lại các ý chính.
<!-- /commitly:context <uuid> -->
```

Report sections are always ordered Tóm tắt, Điểm chính, Chi tiết, Log nguồn. If
analysis is partially unavailable, its state appears in the relevant detail while
source logs remain complete.

## Entities

### Report

| Field | Type | Rule |
|---|---|---|
| `date` | Local date | Selects `reports/YYYY-MM-DD.md` |
| `summary` | Report Claim | Short Vietnamese overview linked to one or more evidence IDs |
| `highlights` | List of Report Claim | Concise accomplishment bullets, each linked to evidence |
| `details` | List of Report Detail | Explanation grouped by repository and work item |
| `evidence` | List of Evidence Log | Supporting commits, paths, and Git change facts |
| `user_context` | List of User Context | Optional one-line developer-provided additions |
| `analysis_status` | `complete` / `partial` / `unavailable` | Never imply complete when a changed item failed analysis |
| `schema_version` | Integer | Version 1 only until an explicit migration exists |

### Report Claim / Detail

| Field | Type | Rule |
|---|---|---|
| `id` | UUID | Stable across report rewrites for the same evidence item |
| `text` | Vietnamese Markdown text | Must be supported by one or more evidence IDs |
| `evidence_ids` | List of UUID | References evidence in this report |
| `certainty` | `supported` / `uncertain` | Uncertain claims are explicitly labelled or omitted |

### Evidence Log

| Field | Type | Rule |
|---|---|---|
| `id` | UUID | Stable report evidence identity |
| `repository_id` | String | Canonical local Git common-directory identity |
| `repository_name` | String | User-visible repository label |
| `repository_path` | String | Local path shown only in local report |
| `commit_id` | String | Full Git object ID; unique with repository ID |
| `subject` | String | Original commit subject, displayed verbatim as text |
| `authored_at` | RFC 3339 | Original Git author timestamp and offset |
| `changed_paths` | List of strings | Safe, exact local paths relative to repository root |
| `added_lines` / `deleted_lines` | Integer or null | Null for binary/unknown changes |
| `analysis_status` | `complete` / `partial` / `unsupported` / `failed` | Per-commit analysis outcome |
| `analysis_note` | String or null | Sanitized explanation when analysis was unavailable |

### User Context

| Field | Type | Rule |
|---|---|---|
| `id` | UUID | Stable identity for one user-provided line |
| `created_at` | RFC 3339 | Creation time, preserved on edit |
| `text` | String | Required after trimming; one line only |

### Selected Repository

| Field | Type | Rule |
|---|---|---|
| `id` | String | Stable identity derived from canonical Git common directory |
| `path` | String | Explicitly selected local path |
| `display_name` | String | Local label; does not affect identity |
| `remote_name` | String | Selected remote; defaults to `origin` when available |
| `author_email` | String | Repository-local `user.email` used for author filtering |
| `last_fetch_at` | RFC 3339 or null | Last successful remote check |
| `last_fetch_status` | `success` / `failed` / `never` | Last remote verification state |

## Evidence and Language Rules

- Include a Git report item only for commits reachable from the selected remote's
  latest available remote-tracking refs and authored by the configured identity.
- Deduplicate on repository identity plus full object ID.
- Group by local date derived from the Git author timestamp; preserve its original
  timestamp and zone.
- Every Git-derived prose claim stores one or more evidence IDs. Those IDs resolve
  to commit IDs and changed paths in the Log nguồn section. User context is
  separately attributed as user-reported and is not passed off as Git evidence.
- Analyze only changed code/documents and bounded context needed to explain them.
  Never scan unrelated repository files or execute repository code.
- Paper/document file changes are described as file changes. A commit does not
  prove the developer read or understood the document.
- Do not persist full source patches, full extracted paper text, model prompts,
  credential-bearing URLs, or credentials.

## Persistence and Conflicts

- Parse UTF-8 Markdown with supported v1 metadata. Malformed/unsupported files
  remain untouched and produce an actionable error.
- Keep a revision hash for each report. Mutations use the existing safe atomic
  write/external conflict mechanism. A conflict preserves both the external file
  and local generated draft until an explicit resolution succeeds.
- A failed fetch, extraction, or analysis cannot remove evidence already saved.
- A failed report write leaves the old report intact and preserves the candidate
  for recovery.
