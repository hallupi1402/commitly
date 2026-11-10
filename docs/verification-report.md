# Commitly Report Baseline Verification

**Date:** 2026-11-10  
**Scope:** `specs/001-work-journal/spec.md`, `plan.md`, and `tasks.md`  
**Readiness:** **Not ready for MVP release.** The report workflow, Markdown store,
Git evidence collection, and UI are implemented. This host has no local model or
`llama-cli`, so the requested semantic code and paper analysis could not be run or
quality-checked. Full legacy backend integration tests also did not complete in
this sandbox.

## Implemented

- Select local Git repositories and their configured remote; fetch without push;
  filter remote-reachable commits by repository `user.email` and local date.
- Collect commit metadata, changed paths, numstat, bounded diffs, and text from
  changed UTF-8 Markdown/text files or PDFs when `pdftotext` is available.
- Write versioned daily Markdown reports with summary, highlights, details, source
  evidence, and one optional user-reported context line.
- Preserve stable evidence and claim IDs, use atomic writes, detect external edits,
  retain both versions, and expose an explicit keep-edited/keep-generated choice.
- Add Today, report history, repository selection, and local analyzer settings UI.
  The analyzer uses a configurable local `llama-cli`; no hosted model is called.

## Commands and Results

| Command/check | Result | What was verified |
|---|---|---|
| `npm --prefix frontend run build` | **Pass** | TypeScript build and Vite production build. |
| `npm --prefix frontend test -- --reporter=dot` | **Pass** | 7 test files, 11 tests. Today report, no-Git context, refresh, history, repository selection, settings, and existing component coverage. |
| `PYTHONPATH=backend/src:/tmp/commitly-test-site backend/.venv/bin/python -m pytest backend/tests/contract backend/tests/unit backend/tests/integration/test_report_api.py -q -ra` | **Pass** | 33 tests: OpenAPI operation coverage, Markdown persistence/edit/conflicts, Git reachability/cache/binary evidence, document limits, analyzer boundary and redaction, settings, and report API route functions using a disposable local bare remote. |
| `PYTHONPATH=backend/src:/tmp/commitly-test-site backend/.venv/bin/python -m pytest backend/tests --collect-only -q` | **Pass** | 53 backend tests discovered. |
| `timeout 10s env PYTHONPATH=backend/src:/tmp/commitly-test-site backend/.venv/bin/python -m pytest backend/tests -q` | **Timed out (124)** | The complete backend suite stopped after four tests. Existing Starlette `TestClient` based integration tests hang in this environment. A minimal FastAPI/TestClient reproduction also hung, so those tests are not claimed as passed. |
| `timeout 6s env PYTHONPATH=backend/src:/home/yennguyen/.cache/uv/archive-v0/Wu9f7PcRAtwKqaOQZfUa9 backend/.venv/bin/python` with a minimal `TestClient(FastAPI())` check | **Timed out** | Confirmed the TestClient hang is reproducible without Commitly routes. |
| `UV_CACHE_DIR=/tmp/commitly-uv-cache uv lock --offline` | **Blocked** | The local uv index cache did not contain the package metadata needed for an offline lock resolution. The project manifest was left with its existing test dependency. |
| Local model smoke | **Not available** | No local `llama-cli` or model file is installed. Stub analyzer tests pass; real Vietnamese analysis was not run. |
| Lint | **Not configured** | No lint script/tool configuration is declared. |
| Separate typecheck | **Not configured** | TypeScript checking is part of the successful production build. |
| Live browser/API server smoke | **Not verified** | The sandbox could not connect to a local uvicorn listener; API behavior was exercised through route functions and temporary Git fixtures instead. |

`/tmp/commitly-test-site/sitecustomize.py` supplies already-cached pytest runtime
packages because `uv` could not install from the registry in this restricted
environment. It is a temporary test helper, outside the repository.

## Git and Data Safety

- Git tests used disposable repositories and local bare remotes. Fixture setup
  pushed only fixture commits to the temporary bare remote. Commitly itself never
  invokes `git push` in the report workflow.
- No personal source code, report data, or secrets were used. No GitHub push or
  repository visibility change was performed.
- The default workspace remains under the user's XDG data directory outside the
  source checkout; selected repository settings are stored in the XDG config
  directory. Model file paths are local settings, not credentials.
- Reports do not persist diffs or extracted full document contents. Document and
  diff inputs are bounded before invoking the local analyzer.

## Remaining Gaps and Risks

1. **Semantic analysis is unverified and unavailable on this host.** Install a
   suitable local `llama-cli` and model, then complete the disposable-fixture
   quality, latency, memory, licensing, and offline evaluation in
   `specs/001-work-journal/research.md`. Until then the fallback report contains
   Git facts and an explicit unavailable-analysis status, not the user-requested
   prose explaining code behavior and paper content.
2. PDF extraction was implemented with `pdftotext`, but this run verified UTF-8
   Markdown/text extraction and rejection limits only; PDF, encrypted, malformed,
   and scanned-document cases remain unverified.
   External edits to report prose are read back from Markdown; edits that damage
   the structure or alter the source log are preserved with a recovery draft, but
   require manual repair rather than an in-app merge.
3. Git tests cover pushed reachability, author filtering, local-only commit
   exclusion, binary paths, cached refs after fetch failure, repeated refresh,
   numstat, and Markdown extraction. Merge commits, renames, unusual filenames,
   and partial multi-repository fetch failure remain unverified.
4. The full backend suite and real browser/server flows remain unverified because
   of the TestClient and local-listener sandbox limitations. Existing legacy
   Project/Reflection/backup modules remain in the repository but are removed from
   the report-first navigation; cleanup is deferred.
5. Keyboard focus and basic accessible labels are present, but a complete
   keyboard-only and dark-mode acceptance walkthrough has not been executed.

See `specs/001-work-journal/tasks.md` for remaining checklist items. Do not treat
this baseline as release-ready until the local model evaluation and remaining
acceptance checks pass.
