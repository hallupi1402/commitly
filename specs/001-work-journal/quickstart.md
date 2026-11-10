# Commitly Semantic Report Baseline: Setup and Validation

Semantic analysis requires a separately installed local llama.cpp CLI and GGUF
model. Commitly does not install or download model files.

## Prerequisites

- Linux desktop, Python 3.12+, `uv`, Node.js 22.12+, npm, and Git.
- Optional: `llama-cli` on `PATH` and a local GGUF model file. The Settings page
  stores their executable name and model path. Without them, Git source logs and
  Markdown reports remain available while semantic prose is marked unavailable.
- At least one local Git repository with a remote and repository-local `user.email`.

## Run

From the repository root:

```sh
uv sync --project backend --dev
npm ci --prefix frontend
uv run --project backend uvicorn commitly.app:app --host 127.0.0.1 --port 8000
```

In another terminal:

```sh
npm --prefix frontend run dev -- --host 127.0.0.1
```

Use the loopback address printed by Vite. Never bind to `0.0.0.0`.

## Automated Checks

Run the checks declared by the manifests:

```sh
uv run --project backend pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run build
```

The frontend build runs TypeScript checking. There are no separate lint or
typecheck scripts. Backend Git tests use disposable repositories and local bare
remotes; analyzer tests use an injected stub. No personal source code or reports
belong in tests or logs.

## Acceptance Walkthrough

Create a temporary repository and temporary bare remote. Configure a test author
identity locally in that repository. Add commits for: (a) a small behavior change
plus tests, (b) a paper with known text, and (c) a metadata-only change. Push them
to the disposable remote and register the repository.

1. Refresh the test date range. Confirm report output is in Vietnamese and has
   exactly **Tóm tắt**, **Điểm chính**, **Chi tiết**, and **Log nguồn**.
2. Confirm the code-change bullet explains the changed behavior and test coverage
   using the diff, not only the commit subject or line counts.
3. Confirm the paper bullet describes the file addition/update and summarizes
   extracted content; it must not claim the developer read it based only on the
   commit.
4. Confirm every claim points to evidence with repository name/path, commit ID,
   timestamp, changed paths, and line counts where known.
5. Confirm the metadata-only change does not become an invented accomplishment.
6. Add a one-line user context note for work not represented in Git. Confirm it
   appears as user-reported context and is not treated as Git evidence.
7. Refresh again and restart. Confirm no duplicate repository+commit evidence and
   report Markdown remains readable.
8. Disable network. Confirm cached refs and installed local analysis still produce
   reports; the UI shows the last verified remote time.
9. Make the remote unavailable. Confirm the prior source's evidence remains and
   its status is unverified; successful repositories can still update.
10. Add an unsupported or oversized changed document. Confirm its path remains in
   the log, its analysis is marked unavailable, and other report items succeed.
11. Modify a report externally and attempt a refresh. Confirm both report versions
    remain recoverable and a newer external edit creates another conflict.
12. Inspect network behavior. During analysis there must be no outbound request;
    refresh may contact only the explicitly selected Git remote and must never
    push.
13. Complete refresh, browse, and source inspection with keyboard-only input and
    dark mode; confirm visible focus and announced status.

Record only walkthroughs actually executed in `docs/verification-report.md`.
