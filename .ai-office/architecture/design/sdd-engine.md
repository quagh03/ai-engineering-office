---
id: DN-0002
type: design-note
title: SDD engine
version: 1
status: in_review
derives_from: [PRD, SYSTEM-DESIGN]
---

# SDD Engine

The SDD engine is the system's source of engineering truth. It stores artifacts, versions them, gates the lifecycle on their approval, and maintains the graph that links a requirement to the code and tests that satisfy it. It never starts an AI execution; the orchestration engine asks it what is approved, what is missing, and what a change affects.

## 1. Artifact repository

Documents live in the project. The database indexes them. ([ADR-0003](../decisions/ADR-0003-filesystem-artifacts-sqlite-index.md))

```text
<project>/.ai-office/
├── project.yaml                  # project config: policy, budgets, providers, commands
├── constitution.md               # non-negotiable project rules
├── agents/                       # optional role overrides
├── specifications/
│   ├── product-requirements.md
│   └── features/FEAT-0001-<slug>/spec.md
├── architecture/
│   ├── system-design.md
│   ├── architecture-diagram.md
│   └── decisions/ADR-0001-<slug>.md
├── plans/PLAN-0001-<slug>.md
├── tasks/TASK-0001-<slug>.md
├── contracts/                    # API and interface contracts
├── reviews/
├── test-reports/
├── memory/
├── cost-reports/
├── execution-history/            # compact per-execution summaries
└── .history/                     # immutable revision snapshots
```

This is the brief's structure with two additions: `agents/` for role overrides and `.history/` for revision snapshots.

### Document format

Every artifact is markdown with YAML front matter. The front matter is validated against a schema per artifact type; the body follows a template with required sections.

```markdown
---
id: FEAT-0001
type: feature-spec
title: Password reset by email
version: 3
status: approved
derives_from: [PRD#US-004]
---

## Functional requirements
- **FR-001** A user can request a reset link by email address.

## Acceptance criteria
- **AC-001** (verifies FR-001; method: automated_test) Requesting a reset for a
  known address sends exactly one email containing a single-use link.
```

Requirements, stories, and criteria are **items**: bullets with a stable bold key. The engine parses them into `artifact_items` with a content hash each. Item keys are never reused within an artifact, so a link to `FEAT-0001#AC-001` always means the same criterion.

Each acceptance criterion declares how it is verified: `automated_test`, `command`, `review`, or `manual`. This is what makes "does the project meet its acceptance criteria" answerable from data rather than from an agent's opinion.

## 2. Versioning

- The file at the artifact's path is the working copy. Each revision is also snapshotted to `.history/<artifact id>/v<N>.md` and recorded with its content hash.
- Approving a revision makes it immutable. Any later change creates revision N+1 in `draft`; the approved revision stays authoritative until the new one is approved.
- **Edits made outside the app** are detected by hash on file change and on startup. They become a new `draft` revision attributed to the user, and impact analysis runs. An external edit never silently replaces an approved revision.
- Agents never write to `.ai-office/`. An authoring execution returns an artifact bundle; the engine validates it and writes the files ([ADR-0005](../decisions/ADR-0005-engine-owned-artifact-writes.md)).

## 3. Lifecycle stages

Each stage has an owner role, inputs, outputs, and a gate. "AI" marks where a provider execution is used; everything else is engine code.

| Stage | Owner | Work | Output artifacts | Gate |
|-------|-------|------|------------------|------|
| 1 Discovery | Product Owner | AI: read the request against project memory and existing specs; list gaps and questions. Engine: supply the project analysis from cache | Discovery notes, questions | Questions answered or explicitly deferred |
| 2 Specification | Product Owner | AI: write the feature spec | `spec.md` with FR, NFR, US, AC, edge cases, constraints, dependencies | Human approval |
| 3 Architecture | Architect | AI: design against the approved spec and existing ADRs | Design note, ADRs, contracts | Human approval |
| 4 Planning | Engineering Manager | AI: decompose into tasks with dependencies, write scope, and criteria. Engine: classify, estimate, route, check the dependency graph | Plan, task files, trace links | Plan valid; approval if policy or budget requires |
| 5 Implementation | Developers, DevOps | AI: implement each task in its worktree | Change sets, completion reports | Per task: scope check and fast gate |
| 6 Verification | QA | Engine: run the test commands, reuse unchanged results. AI: only to write missing tests or fix failures | Test reports, criterion statuses | All linked criteria verified or waived |
| 7 Review | Reviewer | Engine: static analysis. AI: review depth by task category | Review reports | No blocking findings; human approval where configured |
| 8 Delivery | Documentation | Engine: delivery report, cost report, memory updates. AI: only if documentation artifacts must change | Reports, updated docs | Human approval to merge |

Discovery and specification share one provider session: the Product Owner execution either returns questions or the spec, and answering the questions resumes the same session rather than starting a new one.

## 4. Traceability

The graph is the `trace_links` table. Nodes are artifact items, tasks, change sets, verification runs, reviews, and deliveries.

```text
PRD item --refines--> spec item (FR / AC) --constrained_by--> ADR
spec item --planned_by--> plan --decomposes_to--> task
task --implemented_by--> change set --touches--> file
AC --verified_by--> verification run / test
task --reviewed_by--> review
feature --delivered_by--> delivery report
```

Rules:

- **A task must link to at least one approved specification item.** The planner's output is rejected if any task has no origin. This is the mechanism behind "every implementation task has traceability to its originating specification".
- Links are **pinned to the revision** they were created against. That is what lets the engine tell "linked to AC-001 as written in v2" from "AC-001 has since changed".
- Links to code are created by the engine from the change set, not claimed by the agent.

The UI can walk the graph in both directions: from a requirement down to the commits and test results, or from a file up to the requirements that justify it.

## 5. Change impact analysis

When a new revision of a specification is approved (or drafted, as a preview):

1. Diff the two revisions at item level using item hashes: added, changed, removed.
2. Follow links from each changed or removed item to ADRs, plans, tasks, change sets, tests, and documentation.
3. Mark those links `stale`, and set `needs_reassessment` on affected tasks with the reason (which item, which revisions).
4. Affected tasks that have not started return to `BACKLOG`. Tasks in flight are paused for a decision. Completed tasks are flagged only.
5. Emit `SpecificationChanged` and `ImpactAnalysisCompleted` with the affected set.

This is engine code over hashes and links; it costs no AI usage. Because it works at item level, changing one acceptance criterion does not invalidate a whole feature. The Engineering Manager role is invoked only if the affected set needs replanning.

## 6. Workflow profiles

The full lifecycle is wasteful for a typo fix. A profile selects which stages run as separate executions. Every profile still produces a specification artifact with acceptance criteria and trace links, so SDD is never bypassed; only the ceremony scales.

| Profile | For | Authoring executions | Human gates |
|---------|-----|----------------------|-------------|
| `full` | New features, anything touching architecture | Product Owner, Architect, Engineering Manager | Spec, architecture, merge |
| `standard` | Features within existing architecture | Product Owner, Engineering Manager; Architect only if the spec flags architectural impact | Spec, merge |
| `quick` | Bug fixes and small changes | One: a change spec with criteria and a single task | Merge |
| `docs` | Documentation only | None beyond the documentation task itself | Merge |

The profile is proposed by a deterministic rule set (stated intent, files likely affected, whether contracts or ADRs are touched) and can be overridden by the user. If discovery shows a change is larger than its profile assumed, the feature is escalated to a heavier profile rather than proceeding under-specified.

## 7. Project constitution

`constitution.md` holds the rules every task must respect (conventions, forbidden dependencies, security requirements). It is itself an approved, versioned artifact. The context service includes only the clauses relevant to a task, selected by tags, not the whole document.
