# MVP Requirements Quality Checklist: Commitly Semantic Daily Work Report

**Purpose**: Check scope, report shape, data safety, and artifact consistency before
implementation.
**Created**: 2026-11-10
**Feature**: [spec.md](../spec.md)

**Review ownership**: Checked items mean the requirements were reviewed; they do
not mean implementation is complete. User approval is a separate final gate.

## Core Outcome and Report Shape

- [x] CHK001 Is the product's main output a prose report about completed work, not
  a manual-entry journal? [Spec §Product Brief, §US1]
- [x] CHK002 Are the three report sections explicitly defined as Tóm tắt, Điểm
  chính, and Chi tiết? [Spec §Baseline Scope, §FR-006]
- [x] CHK003 Is Log nguồn defined with repository name/path, commit ID/time,
  changed paths, and line counts where available? [Spec §FR-006]
- [x] CHK004 Does the specification require explanation of code behavior rather
  than restating commit messages/statistics? [Spec §FR-004]
- [x] CHK005 Does the paper/document example distinguish a file change from proof
  that the user read or understood it? [Spec §US1/AC3, §FR-005]

## Grounding, Privacy, and Failure

- [x] CHK006 Are generated claims linked to commit/path evidence, with uncertainty
  handled explicitly? [Spec §FR-007]
- [x] CHK007 Is semantic analysis local-only, with no hosted AI fallback and no
  source upload? [Spec §FR-011, Plan §Local semantic analysis]
- [x] CHK008 Are local model/runtime selection and document format support explicit
  blocking research tasks before implementation? [Plan §Delivery Phases, Tasks
  Phase 1]
- [x] CHK009 Are unsupported files, model failures, fetch failures, and partial
  refreshes specified to preserve factual source logs? [Spec §FR-013–015]
- [x] CHK010 Are Markdown schema, stable evidence identity, atomic writes, and
  external-edit conflict behavior consistent across design artifacts? [Spec
  §FR-009–010, Data Model, API]

## Scope and Acceptance

- [x] CHK011 Are structured manual entries, Projects, Reflection, journal backup,
  and other activity sources deferred while a single-line supplement is retained?
  [Spec §Baseline Scope, §Out of Scope, §FR-017]
- [x] CHK012 Do tasks deliver local semantic report generation before history
  browsing and include known code/document fixtures? [Tasks Phase 3–4]
- [x] CHK013 Are offline behavior, safe report persistence, keyboard access, and
  dark mode verifiable? [Spec §SC-005–008]
- [ ] CHK014 Has the user approved this revised semantic report baseline before
  application-code changes? [Plan §Pre-Implementation Review Gate]

## Notes

- CHK001–013 reflect document review only; CHK014 remains unchecked until the user
  approves the scope and artifact set.
- Local model feasibility is intentionally not claimed as solved. The research
  spike must report an actual local option or identify the measured blocker before
  implementation proceeds.
