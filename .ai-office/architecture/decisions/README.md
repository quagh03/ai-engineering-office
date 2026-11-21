# Architecture Decision Records

Each record states one decision, why it was made, and what it costs. A decision is changed by adding a new record that supersedes the old one, never by editing an accepted record.

Each record's `status` is in its front matter. ADR-0001 to ADR-0014 are `approved`.

| # | Decision |
|---|----------|
| [0001](ADR-0001-local-modular-monolith.md) | Local modular monolith on Python and FastAPI |
| [0002](ADR-0002-state-tables-plus-event-log.md) | State tables plus an append-only event log, written in one transaction |
| [0003](ADR-0003-filesystem-artifacts-sqlite-index.md) | Artifacts live on the filesystem; SQLite indexes them |
| [0004](ADR-0004-agents-are-roles.md) | Agents are roles; executions are the unit of AI work |
| [0005](ADR-0005-engine-owned-artifact-writes.md) | Authoring executions are read-only; the engine writes artifacts |
| [0006](ADR-0006-detached-execution-runner.md) | Detached execution runner with file-backed output |
| [0007](ADR-0007-engine-managed-worktrees.md) | The engine manages git worktrees and all git writes |
| [0008](ADR-0008-approvals-between-executions.md) | Approvals happen between executions, under permission envelopes |
| [0009](ADR-0009-cost-measurement-and-budget-meters.md) | Three cost measurement levels and multi-meter budgets |
| [0010](ADR-0010-pointer-first-context.md) | Pointer-first context packages; no vector search in v1 |
| [0011](ADR-0011-deterministic-work-stays-in-the-engine.md) | Deterministic work is never delegated to AI |
| [0012](ADR-0012-local-web-app-3d-as-projection.md) | Local web app; the 3D office is an optional projection of shared state |
| [0013](ADR-0013-bootstrap-with-sdd.md) | This platform is built with its own SDD process |
| [0014](ADR-0014-git-convention.md) | Git branching and commit convention |
