---
id: ROADMAP
type: roadmap
title: Roadmap
version: 1
status: in_review
derives_from: [PRD, SYSTEM-DESIGN]
---

# Roadmap

Phases follow the brief's dependency order. Each phase ends with the application runnable and a set of exit criteria that are checked, not asserted. The 3D office is Phase 8 because it visualizes a system that must already work.

## How the roadmap is executed

The platform is built with its own SDD process ([ADR-0013](../architecture/decisions/ADR-0013-bootstrap-with-sdd.md)). Each phase is one feature, FEAT-0001 for Phase 1 through FEAT-0009 for Phase 9, listed in the [product requirements](../specifications/product-requirements.md#features).

A phase's task table below is an outline. Before any of its work starts, the feature goes through the stages: a specification with acceptance criteria is written and approved, any design change is recorded, and a plan turns the outline into task files with trace links. The exit criteria below become acceptance criteria in that specification. Specifications are written when a feature's turn comes, not in advance.

| Feature | Stage | Artifacts |
|---------|-------|-----------|
| FEAT-0001 Application foundation | Specification, awaiting approval | [Specification](../specifications/features/FEAT-0001-foundation/spec.md), [draft plan](PLAN-0001-foundation.md) |
| FEAT-0002 to FEAT-0009 | Not started | - |

## Working rules

- Every task is small enough to verify on its own, ships with its tests, and leaves the application runnable.
- A phase is done when its exit criteria pass. Producing the code is not the criterion.
- Tests that call a real provider spend real usage. They are opt-in, run deliberately, and their cost is recorded in the phase notes.
- No product code path simulates a provider. Recorded-output replay exists in the test suite only.
- Architectural changes are made by adding or superseding an ADR, not by drifting from one.

## Milestones

| Milestone | After | Meaning |
|-----------|-------|---------|
| M1 Walking skeleton | Phase 4 | A real task runs on a real CLI in a worktree, is observed live, reviewed as a diff, merged on approval, and survives a restart |
| M2 Budget-aware | Phase 5 | Executions are routed, budgeted, and measured |
| M3 Engineering team | Phase 6 | An idea goes through all eight stages to an approved merge |
| M4 Observable | Phase 7 | Everything is inspectable and recoverable |
| M5 Office | Phase 8 | The 3D office shows and controls the real system |

## Phase 1: Architecture and foundation

| # | Task | Depends on |
|---|------|------------|
| 1.1 | Backend project: uv, FastAPI app, layered settings, structured logging, error model | - |
| 1.2 | SQLite setup (WAL, foreign keys), unit of work, Alembic with the first migration | 1.1 |
| 1.3 | Domain package: IDs, base entities, event envelope | 1.1 |
| 1.4 | Event store and in-process bus with transactional write and post-commit publish | 1.2, 1.3 |
| 1.5 | REST skeleton, OpenAPI, WebSocket gateway with subscribe, replay, and resync | 1.4 |
| 1.6 | Local API protection: loopback bind, Host and Origin checks, session token | 1.5 |
| 1.7 | Frontend shell: Vite, Tailwind theme, routing, generated client, store, event reducer, connection status | 1.5, 1.6, 1.8 |
| 1.8 | Project service: create and import, boundary validation, `.ai-office/` scaffold | 1.4, 1.5 |
| 1.9 | Tooling: ruff, mypy strict, import-linter contracts, eslint, tsc, test runners, start and stop scripts | 1.1 |

**Exit criteria**

- One command starts the application; the UI loads and shows a live connection.
- Creating a project writes the scaffold, persists the project, and the UI updates from the event without a reload.
- Restarting the engine preserves projects; a reconnecting client replays missed events by `seq`.
- A request with a foreign `Origin` or without the token is rejected.
- Migrations apply to an empty database and are reversible; import-linter contracts pass.

These are specified in full as AC-001 to AC-022 of [FEAT-0001](../specifications/features/FEAT-0001-foundation/spec.md), and tasks 1.1 to 1.9 are TASK-0001 to TASK-0009 in [PLAN-0001](PLAN-0001-foundation.md).

## Phase 2: SDD engine

| # | Task | Depends on |
|---|------|------------|
| 2.1 | Artifact types, front matter schemas, templates, parser for items | 1.3 |
| 2.2 | Artifact repository: read, write, hash, revision snapshots, index | 2.1, 1.8 |
| 2.3 | Revision lifecycle and approval (the first approval kind) | 2.2, 1.4 |
| 2.4 | External edit detection and reconciliation | 2.2 |
| 2.5 | Trace links and graph queries | 2.2 |
| 2.6 | Item-level diff and impact analysis | 2.3, 2.5 |
| 2.7 | Feature stages and gate definitions; workflow profiles | 2.3 |
| 2.8 | UI: artifact tree, document view, revision diff, approve and reject, trace view, criteria matrix | 2.3, 2.5, 1.7 |

**Exit criteria**

- A specification written by hand can be drafted, approved, revised, and diffed, with snapshots on disk.
- Editing an approved file outside the app produces a draft revision and leaves the approved one authoritative.
- Changing one acceptance criterion marks exactly the links and tasks that depend on it as stale, and nothing else.
- A task with no link to an approved specification item is rejected.
- This repository, imported as a project, is indexed without error: every hand-written artifact, item, and trace link in its `.ai-office/` is parsed, and each approval recorded in front matter is preserved.

## Phase 3: Orchestration engine

| # | Task | Depends on |
|---|------|------------|
| 3.1 | Task state machine with the transition table and events | 1.4 |
| 3.2 | Agent registry: built-in role definitions, project overrides, validation | 1.8 |
| 3.3 | Dependency graph: cycle detection, readiness | 3.1 |
| 3.4 | Resource claims and parallel admission rules | 3.3 |
| 3.5 | Scheduler loop, event-driven, with concurrency limits | 3.1 to 3.4 |
| 3.6 | Approval service: kinds, policies, snapshots, expiry | 2.3 |
| 3.7 | Structured agent messages | 3.2 |
| 3.8 | Workflow driver per feature | 2.7, 3.5 |
| 3.9 | Execution records and the execution state machine, with a manual execution path | 3.1 |
| 3.10 | UI: task board, dependency view, approval center, agent list | 3.1, 3.6, 1.7 |

In this phase a task's work is completed by a person through the UI (the "manual execution path"), which exercises scheduling, states, approvals, and events before any provider is connected. The path remains in the product as a supported way to do a task by hand.

**Exit criteria**

- Every transition not in the table is rejected, verified by a test that enumerates all state pairs.
- A set of tasks with dependencies and overlapping scopes is scheduled in a valid order, with overlapping tasks serialized and the deferral reason recorded.
- Pending approvals and task states survive a restart.

## Phase 4: Cursor and Claude Code integrations

| # | Task | Depends on |
|---|------|------------|
| 4.1 | **Provider probe.** One small recorded run per CLI: stream format, result fields, usage fields, denied action, cancel by signal, resume. Record fixtures. Update [provider integration](../architecture/design/provider-integration.md) with findings | - |
| 4.2 | Provider contract, capability and health models | 4.1 |
| 4.3 | Discovery, version detection, capability detection from help output, health checks | 4.2 |
| 4.4 | Detached runner: spawn, file-backed output, timeout, exit record, signals | 1.1 |
| 4.5 | Execution manager: tail, normalize, persist, reattach | 4.4, 3.9 |
| 4.6 | Cursor adapter: invocation, parsing, outcome, errors | 4.2, 4.1 |
| 4.7 | Claude Code adapter: invocation, parsing, outcome, errors, usage | 4.2, 4.1 |
| 4.8 | Permission envelopes and their translation per provider | 4.6, 4.7 |
| 4.9 | Worktree manager, change sets, scope check, checkpoint commit, approved merge | 3.4 |
| 4.10 | Recovery reconciliation on startup | 4.5, 4.9 |
| 4.11 | UI: provider settings and health, live execution view, diff view, stop | 4.5, 1.7 |

Task 4.1 comes first because it turns every *validate* item in the provider design into a recorded fact. It needs both CLIs authenticated and spends a small amount of real usage.

**Exit criteria (M1)**

- Health correctly reports installed, version, and authenticated for both CLIs, including the unauthenticated case.
- The same task executes on Cursor and on Claude Code in a worktree, with live normalized events and the raw stream both visible.
- Stop ends the process group within the grace period. A timeout is enforced with the engine stopped.
- Killing the engine mid-execution and restarting either reattaches to the running execution or settles the finished one; a write execution found interrupted is not restarted without a decision.
- A change outside the declared scope is detected and blocked from merging.
- Fixture replay tests pass for the recorded CLI versions with no network access.

## Phase 5: Cost optimization engine

| # | Task | Depends on |
|---|------|------------|
| 5.1 | Cost records with measurement level and billing basis; cumulative-session handling | 4.7 |
| 5.2 | Pricing and accounting configuration with effective dates | 5.1 |
| 5.3 | Budgets, ledger, reservation and settlement, thresholds | 5.1 |
| 5.4 | Classification rules | 3.1 |
| 5.5 | Tier mapping and router with recorded rationale; pin and fallback rules | 5.4, 4.3 |
| 5.6 | Estimation from priors and history | 5.1 |
| 5.7 | Context builder (file-level), manifests, provenance, prompt templates | 2.5 |
| 5.8 | Execution gate and `ExecutionAvoided`; cache entries with fingerprints | 5.7 |
| 5.9 | Retry policy: classes, signatures, bounded escalation | 4.6, 4.7 |
| 5.10 | Cost dashboard and budget UI | 5.1, 5.3 |

**Exit criteria (M2)**

- Every execution has a cost record whose level is correct for its provider; no total presents unknown as zero.
- A budget set below a task's estimate prevents the start and raises an approval. Thresholds fire at the configured percentages. Parallel reservations cannot jointly exceed a budget.
- A pinned provider is never changed; an unavailable pinned provider blocks the task.
- The same failure signature is not retried twice under the same configuration.
- Each execution's manifest lists what was included and why, and the package fits the role's budget.

## Phase 6: Complete engineering workflow

| # | Task | Depends on |
|---|------|------------|
| 6.1 | Artifact bundle format, validation, and repair turn | 5.7 |
| 6.2 | Authoring executions: Product Owner (with questions and resume), Architect, Engineering Manager | 6.1 |
| 6.3 | Plan ingestion: tasks, dependencies, scopes, trace links, validation | 6.2, 3.3 |
| 6.4 | Implementation flow with completion reports checked against the diff | 4.9, 6.1 |
| 6.5 | Verification runner: declared commands, fast gate, acceptance checks, result reuse | 5.8 |
| 6.6 | Review: static checks, AI review by category, changes-requested loop | 6.4 |
| 6.7 | Integration branch, sequential integration, conflict handling | 4.9 |
| 6.8 | Quality gates per task and per stage; criterion verification and waivers | 6.5, 6.6 |
| 6.9 | Delivery: reports, cost report, documentation task, approved merge | 6.8 |
| 6.10 | Workflow profiles end to end | 6.9 |

**Exit criteria (M3)**

- From a described feature, the system produces an approved specification, design, and plan, implements the tasks, verifies and reviews them, and requests approval to merge, on a sample project.
- No task reaches `COMPLETED` with an unverified, unwaived linked criterion or a failed required check.
- A `quick` change completes with one authoring execution and one implementation execution.
- Two independent tasks run in parallel in separate worktrees and integrate cleanly; two overlapping tasks run in sequence.
- The delivery report states what was completed, what remains, and what it cost, with measurement levels.

## Phase 7: Project memory and observability

| # | Task | Depends on |
|---|------|------------|
| 7.1 | Incremental file index and project analysis cache | 5.8 |
| 7.2 | Symbol index (tree-sitter) and import graph; symbol-level pointers in context | 7.1 |
| 7.3 | FTS5 search over items, memory, and symbols | 7.1 |
| 7.4 | Memory entries, proposals, acceptance policy, conflicts, staleness | 6.4 |
| 7.5 | Retrieval measurement (files opened outside the package, later-needed misses) | 7.2 |
| 7.6 | Event inspector with filters and causation chains | 1.5 |
| 7.7 | Execution timeline and drill-down; provider health history; live cost monitoring | 7.6 |
| 7.8 | Retention and pruning | 4.5 |

**Exit criteria (M4)**

- A second task on the same project triggers no repeated project analysis when files are unchanged.
- Any execution can be opened to show prompt, manifest with provenance, normalized and raw stream, diff, and cost.
- The inspector filters by every dimension in the brief, over history and live.
- A memory entry that contradicts an approved artifact is flagged, not applied.

## Phase 8: 3D virtual office

| # | Task | Depends on |
|---|------|------------|
| 8.1 | `derivePresence` and its tests against recorded event sequences | 7.6 |
| 8.2 | Lazy-loaded scene: layout data, zones, instanced furniture, camera | 1.7 |
| 8.3 | Avatars, presence transitions along waypoints, provider indication | 8.1, 8.2 |
| 8.4 | Interaction through the shared inspector and existing commands | 8.3 |
| 8.5 | Approvals, blockers, budget, and messages in the scene | 8.3 |
| 8.6 | Quality presets, reduced motion, disable switch, WebGL fallback | 8.2 |
| 8.7 | Performance measurement and tuning | 8.3 |

**Exit criteria (M5)**

- Replaying a recorded event sequence produces the expected presence for every role at every step; with no events, no avatar shows activity.
- Reloading mid-execution shows the correct scene without replaying animations.
- Every action available in the scene produces the same command as the dashboard.
- With 3D disabled the three.js bundle is not loaded and the dashboard is unaffected.
- An idle scene renders no frames; measured idle CPU and memory are within the targets set in 8.7.

## Phase 9: Advanced capabilities

Ordered by expected value; each needs its own specification before work starts.

1. Dynamic delegation: roles requesting sub-tasks through structured messages, subject to the same admission and budget rules.
2. Advanced parallel execution: per-target test reuse, finer file ownership, speculative integration.
3. Context optimization driven by the retrieval measurements from 7.5; vector search only if those measurements justify it.
4. Project analytics: throughput, rework rate, estimate accuracy over time.
5. Workflow customization: user-defined profiles, stages, and gates.
6. Extension points: role packs, artifact types, verification commands, dashboard panels. The provider contract already permits further adapters; none is planned.

## Verification strategy

| Level | Scope |
|-------|-------|
| Unit | State machines, classification, routing, budgets and ledger, impact analysis, context fitting, event reducer, `derivePresence` |
| Integration | Repositories and migrations, artifact repository on a real filesystem, worktrees on a real git repository, scheduler with the manual execution path |
| Contract | Provider adapters against recorded output; invocation snapshots |
| Live | Opt-in runs against real CLIs |
| End to end | Playwright over the dashboard against a running engine |
| Recovery | Kill and restart at each execution phase |
