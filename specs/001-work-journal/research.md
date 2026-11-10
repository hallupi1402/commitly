# Research Plan: Local Semantic Report Generation

## User requirement

The report must explain code behavior changes and summarize relevant paper or
document content in natural Vietnamese prose. It must include a short summary,
accomplishment bullets, details, and a Git source log. A commit subject plus
changed paths and line counts alone does not satisfy this outcome.

## Evidence sources

- Selected Git commits: full object ID, author/time, subject, reachable remote refs.
- Code: commit diff hunks, changed source files, and bounded neighboring context
  only when needed to explain a change.
- Paper/documents: locally extracted text from supported changed files. A file
  being added/changed is evidence of a repository change, not proof the developer
  read or understood it.
- Source log: repository identity/name/path, commit, exact changed paths, and
  numstat when meaningful.

Do not scan unrelated files, execute repository code, persist full patches, or send
code/document contents to a hosted service.

## Local model/runtime decision — blocking before implementation

No model, runtime, or extraction library has been selected yet. T005–T007 in
`tasks.md` must compare viable local approaches on disposable fixtures before any
integration code begins. The comparison must measure:

- Correctness and evidence grounding for code changes and paper text.
- Unsupported-claim rate, including whether it invents developer intent.
- Vietnamese output quality and preservation of source names/identifiers.
- Peak memory, model/package size, latency, CPU/GPU expectations, and installation
  complexity on the target Linux desktop.
- Offline execution after installation and license/redistribution limits.
- Safe limits for diff context, document size, and malformed/untrusted input.

If no local option meets the privacy/offline constraints and acceptable quality,
stop and return with the measured trade-off. Do not silently fall back to remote AI.

## Document extraction

Begin with paper/document formats explicitly observed in the disposable fixture.
Prefer a platform tool or already installed dependency if it safely extracts text.
Bound file size and extracted text. For encrypted, malformed, oversized, scanned,
or unsupported documents, preserve the Git evidence and mark analysis unavailable;
do not add OCR to the baseline without separate scope approval.

## Report-grounding rules

- Each summary claim resolves to one or more evidence IDs, which resolve to commit
  IDs and changed paths.
- Describe code behavior from the diff and changed files. Distinguish implementation
  from tests, refactors, documentation, and metadata changes when evidence allows.
- Phrase document activity as “added/updated document X; its content covers Y.”
  Do not infer “read paper” from a file addition alone.
- Omit or label uncertain interpretations. If analysis fails for one commit/file,
  retain the source log and continue with other evidence.
- Never include detected secret values or credential-bearing URLs in generated
  prose or logs.

## Git behavior

- `git fetch` updates selected remote-tracking refs but does not push or merge.
- `git log` provides commit identity, subject, author, and dates; queried commits
  must be reachable from the selected remote's available refs.
- Git diff name/status and numstat output provide changed paths and text line
  counts. Binary changes may not have meaningful line counts.
- Fetch failures are isolated per repository; saved evidence for the failed source
  is retained and status is marked unverified.

## References

- [Git `fetch`](https://git-scm.com/docs/git-fetch) — fetch remote refs without
  pushing or merging.
- [Git `log`](https://git-scm.com/docs/git-log) — select commits and inspect
  author/time metadata.
- [Git `diff`](https://git-scm.com/docs/git-diff) — inspect changed content and
  statistics.
- [Git `diff-tree`](https://git-scm.com/docs/git-diff-tree) — inspect changes for
  individual commits.

## Remaining research outcomes

### Implementation-time environment check (2026-11-10)

- This host has no `llama-cli`, `llama-server`, or Ollama executable and no local
  model file. Registry access is unavailable, so a runtime/model could not be
  installed or evaluated here. Vietnamese quality, factual grounding, latency,
  memory use, model size, and license remain **unverified**. The product is not
  release-ready until the disposable-fixture model study is completed.
- The implementation provides a configurable `llama-cli` adapter. It invokes the
  CLI only for an explicit refresh and sends no content to a network service. The
  UI can save a model path and executable. Without those installed locally, it
  records Git evidence and clearly marks semantic analysis unavailable.
- Changed `.md`, `.markdown`, `.txt`, and `.rst` files are decoded as UTF-8. Changed
  `.pdf` files are extracted through `pdftotext` when installed. Extraction is
  limited to 2 MB per file, 20,000 characters per document, three documents per
  commit, and a 50,000-character model prompt. Malformed, encrypted, scanned,
  oversized, empty, or unsupported documents remain in the source log and receive
  an unavailable explanation. OCR is not included.
- Disposable Git tests validate selected-remote reachability, author filtering,
  local-only commit exclusion, cached refs after fetch failure, binary changes,
  changed paths, numstat, repeated refresh, and Markdown extraction. They do not
  validate real local-model prose quality or merge/rename/unusual filename cases.

No performance or analysis-quality claim is made from this environment check.
