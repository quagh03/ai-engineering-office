# AI Engineering Office

A local-first, cost-optimized, multi-agent software engineering and orchestration platform. Specifications drive the work, an orchestration engine coordinates logical agent roles, and Cursor CLI and Claude Code CLI execute the engineering tasks. A dashboard and a 3D office visualize what the engine is actually doing.

It runs on macOS as a browser-based local application.

## Status

**Specification, architecture, and the FEAT-0001 plan are approved.** No application code exists yet. The next unit of work is [TASK-0001](.ai-office/tasks/TASK-0001-backend-skeleton.md) (backend skeleton), which is `READY`.

| Stage | State |
|-------|-------|
| 1 Discovery | Done. Questions answered on 2026-11-21 |
| 2 Specification | Approved 2026-11-21 |
| 3 Architecture | Approved 2026-11-21 |
| 4 Planning | PLAN-0001 and its nine tasks approved 2026-11-21 |
| 5 Implementation | Next: TASK-0001 |
| 6 to 8 | Not started |

## How this project is built

All engineering artifacts live in [`.ai-office/`](.ai-office/), in the layout and format the platform itself will read. Work follows the [constitution](.ai-office/constitution.md): approved specifications before code, tasks that trace to requirements, completion only on verified acceptance criteria, and approval by the user only. [`AGENTS.md`](AGENTS.md) gives the same rules to every AI session. Why and how: [ADR-0013](.ai-office/architecture/decisions/ADR-0013-bootstrap-with-sdd.md).

## Artifacts

| Artifact | What it answers | Status |
|----------|-----------------|--------|
| [Constitution](.ai-office/constitution.md) | The rules all work must follow | Approved |
| [Product requirements](.ai-office/specifications/product-requirements.md) | What the product must do; the root of traceability | Approved |
| [Discovery notes](.ai-office/specifications/discovery-notes.md) | What was verified, how ambiguities were resolved, risks | Approved |
| [FEAT-0001 specification](.ai-office/specifications/features/FEAT-0001-foundation/spec.md) | Requirements and acceptance criteria for the first feature | Approved |
| [System design](.ai-office/architecture/system-design.md) | Components, boundaries, processes, flows, stack | Approved |
| [Design notes](.ai-office/architecture/design/) | Domain model, SDD engine, orchestration, providers, cost and context, events and API, frontend and 3D, safety | Approved |
| [Decision records](.ai-office/architecture/decisions/README.md) | The thirteen decisions the design depends on | Approved |
| [Roadmap](.ai-office/plans/roadmap.md) | Nine phases, one feature each, with exit criteria | Approved |
| [PLAN-0001](.ai-office/plans/PLAN-0001-foundation.md) and [tasks](.ai-office/tasks/) | How FEAT-0001 will be built | Approved; TASK-0001 ready |

## The design in one paragraph

A single local Python process (FastAPI) owns all state in SQLite and publishes an append-only event log over WebSockets. Engineering knowledge lives as versioned markdown artifacts in each project's `.ai-office/` directory. Agents are roles, not processes: the engine starts a provider execution only when a task needs AI judgment, gives it a compact task-specific context package, and runs it in an engine-managed git worktree under an explicit permission envelope. Tests, git operations, indexing, and reporting are done by the engine itself and cost no AI usage. Every execution is routed, budgeted, measured, and traced back to the specification that required it.
