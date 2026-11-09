<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0 (MINOR: substantial expansion of project-specific principles and workflow)
- Modified principles:
  - I. User Value and Simplicity → I. Work Journal First; II. Hybrid Capture; VI. Lightweight Architecture; VIII. Scope Discipline
  - II. Correctness and Data Integrity → V. Data Safety
  - III. Security and Privacy by Default → retained in Security and Data Handling
  - IV. Verification Proportional to Risk → IX. Quality
  - V. Maintainability and Diagnosability → IX. Quality
- Added principles: III. Local First; IV. Markdown Native; VII. Incremental Delivery
- Added sections: Product Vision and Scope
- Modified sections: Delivery and Quality → Development Workflow
- Removed sections: none
- Follow-up TODOs: confirm the original ratification date
-->

# Commitly Constitution

Product vision: **Capture today. Continue tomorrow.**

## Core Principles

### I. Work Journal First
Commitly records work the developer actually accomplished. Journal entries MUST
describe completed work and outcomes; plans and intended work MUST NOT be presented
as accomplishments.

### II. Hybrid Capture
A single line of text MUST be enough to create a useful journal entry. Structured
details MAY enrich an entry but MUST remain optional for capture and later use.

### III. Local First
Every core feature MUST work completely offline. Core workflows MUST NOT depend on
network access or a remote service.

### IV. Markdown Native
Human-readable Markdown files are the source of truth for journal data. The product
MUST preserve data in Markdown that people can read and edit without Commitly.

### V. Data Safety
Entries MUST have stable IDs. Writes MUST be atomic, and the product MUST protect
existing entries from unintended overwrites. Failed writes MUST leave existing data
intact and report an actionable error.

### VI. Lightweight Architecture
The implementation MUST avoid unnecessary services, dependencies, and background
processes. New architectural components MUST directly support an approved product
requirement.

### VII. Incremental Delivery
Work MUST be delivered in small phases that can be tested independently. Each phase
MUST have clear acceptance criteria and be validated against them before it is
considered complete.

### VIII. Scope Discipline
Work MUST stay within the approved MVP. Task boards, AI features, analytics, and
cloud services MUST NOT be introduced unless they are explicitly approved as part of
the product scope.

### IX. Quality
Code MUST remain maintainable, behavior-changing work MUST have automated tests,
failures MUST be handled and reported clearly, and user-facing interfaces MUST be
accessible.

## Product Vision and Scope

Commitly is a personal, local-first developer work journal. Its purpose is to capture
completed work today in a form that helps the developer continue tomorrow. The MVP
scope is defined by its reviewed specification; additions MUST follow the scope
approval rule in Principle VIII.

## Security and Data Handling

Dependencies and permissions MUST be limited to what the product requires. External
input MUST be treated as untrusted. Secrets MUST NOT be stored in source control or
ordinary logs, and personal data MUST NOT be collected or retained without a product
need. Data format or access changes MUST preserve existing data or provide a safe
migration path.

## Development Workflow

Development MUST follow specification-driven development. Before implementation
begins, the specification, technical plan, and task list MUST be reviewed. Each
delivery phase MUST be validated against its acceptance criteria. Teams MUST prefer
simple, proven solutions over unnecessary abstractions.

## Governance

This constitution governs project decisions and takes precedence over conflicting
local guidance. A proposed amendment MUST state its rationale and affected
principles or sections, and MUST be reviewed before adoption. Plans and reviews MUST
identify material conflicts with this constitution and resolve or explicitly
document them before release.

The version uses semantic versioning: MAJOR for backward-incompatible governance
changes, including removal or redefinition of requirements; MINOR for new principles
or materially expanded guidance; and PATCH for clarifications that do not change
requirements. Every adopted amendment MUST update the version and last-amended
date. Compliance MUST be reviewed during planning and before release; any exception
MUST state its reason and scope.

**Version**: 1.1.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-11-10
