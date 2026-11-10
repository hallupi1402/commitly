# MVP Requirements Quality Checklist: Commitly — Work Journal First

**Purpose**: Review the MVP requirements for completeness, clarity, consistency, and readiness before task generation and implementation.
**Created**: 2026-11-10
**Feature**: [spec.md](../spec.md)

**Note**: This custom checklist reviews the written requirements and their alignment with the technical plan; it is not an implementation test plan.
**Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.
**Marker Semantics**: `[x]` means the criterion has been reviewed and satisfied for requirements quality. It does not mean implementation work is complete.

## Requirement Completeness

- [ ] CHK001 Are the Markdown record format, supported schema versions, and handling of future format changes defined consistently across the spec and design? [Completeness, Spec §FR-010, Data Model §Markdown Schema Version 1]
- [ ] CHK002 Are all optional entry fields represented in the entry model and covered by clear capture requirements? [Completeness, Spec §FR-003, Spec §Key Entities]
- [ ] CHK003 Are project identity, duplicate-name behavior, rename rules, and archive behavior specified consistently? [Completeness, Spec §FR-007, Data Model §Project]
- [ ] CHK004 Does the spec make clear whether Settings only displays the workspace location or lets the user change it? [Clarity, Spec §FR-015, OpenAPI §/settings]
- [ ] CHK005 Are safeguards against automatically pushing journal data to Commitly's public source repository explicit and testable? [Completeness, Spec §FR-014, Spec §Backup Configuration]

## Requirement Clarity

- [ ] CHK006 Are the date range, ordering, or selection rules for “relevant previous context” stated clearly enough to produce consistent dashboard results? [Ambiguity, Spec §FR-001, Spec §User Story 2]
- [ ] CHK007 Is “latest next steps” ordering defined, and is blocker resolution consistently defined for entry and reflection content? [Clarity, Spec §FR-008, Spec §Key Entities, Data Model §Journal Entry]
- [ ] CHK008 Does the spec define what the user must acknowledge when confirming a backup destination as private? [Clarity, Spec §FR-014, Spec §Clarifications]

## Requirement Consistency

- [ ] CHK009 Does the spec's assumption that a missed backup waits until Commitly next runs agree with the plan's timer running while the UI is closed and catching up after user-manager activation? [Conflict, Spec §Assumptions, Plan §Architecture and Flow, Research §Git Backup]
- [ ] CHK010 Are external edits to the project registry covered by the same user-facing conflict and recovery requirements as edits to daily journals? [Consistency, Spec §FR-012, Data Model §Write and Conflict Rules]
- [ ] CHK011 Is the fail-safe behavior for filesystems that cannot perform safe writes specified in the product requirements, including the user-facing error and preservation of the draft? [Gap, Spec §FR-012, Spec §FR-016, Plan §Constraints]

## Acceptance Criteria Quality

- [ ] CHK012 Can every functional requirement be traced to at least one acceptance scenario or measurable outcome, especially workspace settings and backup privacy? [Traceability, Spec §FR-014, Spec §FR-015, Spec §User Story 4]
- [ ] CHK013 Is search success measurable against a defined dataset size, result expectation, or response-time target? [Measurability, Spec §SC-005, Plan §Performance Goals]
- [ ] CHK014 Are the conditions for “two actions” in the Quick Capture success criterion explicit about the starting state and what counts as an action? [Clarity, Spec §SC-001, Spec §FR-005]

## Scenario Coverage

- [ ] CHK015 Are requirements complete for a second external edit arriving while the user is resolving an existing conflict? [Coverage, Spec §FR-012, Spec §User Story 1]
- [ ] CHK016 Are backup requirements clear for a missed timer run, an unavailable user manager, authentication failure, and a later retry? [Coverage, Spec §FR-013, Spec §FR-014, Spec §SC-007, Plan §Architecture and Flow]

## Edge Case Coverage

- [ ] CHK017 Are malformed Markdown and unsupported schema versions covered with a recovery path that preserves the original file? [Exception Flow, Spec §FR-010, Spec §FR-012, Data Model §Write and Conflict Rules]
- [ ] CHK018 Is the expected behavior clear when a project is renamed or archived while older entries still reference it? [Edge Case, Spec §FR-007, Data Model §Project]

## Non-Functional Requirements

- [ ] CHK019 Are expected journal volume and local search responsiveness bounded enough to judge whether file scanning remains acceptable? [Gap, Spec §SC-005, Plan §Performance Goals, Plan §Scale/Scope]
- [ ] CHK020 Are accessibility requirements specified beyond keyboard operation and dark-mode readability, including focus visibility and assistive-technology semantics? [Coverage, Spec §FR-016, Spec §SC-006, Constitution Principle IX]

## Dependencies & Assumptions

- [ ] CHK021 Are systemd user-session requirements and the effect of leaving linger disabled stated consistently for daily backup expectations? [Assumption, Spec §Assumptions, Research §Git Backup and Scheduling]
- [ ] CHK022 Are backup credentials and remote authentication expectations clear without storing secrets in Commitly settings or service configuration? [Dependency, Spec §FR-014, Research §Git Backup and Scheduling]

## Ambiguities & Conflicts

- [ ] CHK023 Does the specification distinguish “private by default” from any technical guarantee that a user-selected remote is actually private? [Ambiguity, Spec §FR-014, Spec §Clarifications]
- [ ] CHK024 Are the conflict requirements clear about when preserved local and external versions may be removed after a successful user resolution? [Clarity, Spec §FR-012, Data Model §Journal Conflict]

## Notes

- Mark items `[x]` only after review confirms the requirement-quality criterion is satisfied.
- Leave items unchecked when they still require clarification, correction, or reviewer evaluation.
- `$speckit-implement` reads checklist checkbox state as a gate and must not modify markers.
- `checklists/requirements.md` is the separate built-in specification-quality checklist maintained by `$speckit-specify` and `$speckit-clarify`.
- Findings may be recorded inline; items are numbered sequentially for easy reference.
