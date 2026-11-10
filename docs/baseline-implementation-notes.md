# Baseline Implementation Notes

Commitly's baseline navigation now centers on Today’s report, saved report
history, selected repositories, and local settings. The earlier manual-entry
Today/Journal/Projects/Reflection/backup UI is no longer linked from the main
navigation; its modules and legacy API routes remain in the repository for now.
They should be removed only in a separately reviewed cleanup because other
working-tree changes also touch those files.

## Reused pieces

- FastAPI loopback app, XDG workspace/config paths, strict settings models, and
  private atomic JSON settings writes.
- The journal module's locked atomic replacement, file exchange, recovery-copy,
  and external-change conflict mechanism for Markdown reports.
- Existing Vite/React shell, accessible shared feedback components, theme
  preference handling, pytest, and Vitest setup.
- Git CLI already used by the isolated backup implementation; the report collector
  uses argument arrays, timeouts, selected repository roots, and does not push.

## New baseline path

- `git_activity.py`: explicitly registered repository and chosen remote, local
  author filter, remote-tracking reachability, commit facts, bounded diffs, and
  changed-document text.
- `document_text.py`: bounded UTF-8 Markdown/text extraction and optional local
  `pdftotext` extraction.
- `report_analysis.py`: local CLI boundary with claim-to-evidence validation and
  an explicit unavailable state when no model is installed.
- `reports.py`: versioned Markdown report, stable report/evidence/context IDs,
  read/list APIs, atomic writes, and conflict preservation/resolution.
- React Today and Reports pages show prose, source logs, one-line user context,
  refresh state, saved dates, and an explicit external-edit choice.

The current host has no llama.cpp runtime/model, so the report source and
unavailable-analysis path are testable here; natural-language code and paper
analysis quality is not yet verified. See `specs/001-work-journal/research.md` and
`docs/verification-report.md`.
