---
id: DN-0003
type: design-note
title: Orchestration engine
version: 1
status: in_review
derives_from: [PRD, SYSTEM-DESIGN]
---

# Orchestration Engine

The orchestration engine decides what runs, when, as which role, and under what limits. It drives features through their stages, schedules tasks, enforces the state machines, and manages approvals and recovery. It knows providers only as an interface.

## 1. Agents are roles

A role is a configuration record. An execution is a provider process acting as exactly one role. There is no process per role, and no role holds a long-lived session. ([ADR-0004](../decisions/ADR-0004-agents-are-roles.md))

### Built-in roles

| Role id | Team | Default permission profile | Typical execution kind |
|---------|------|----------------------------|------------------------|
| `product-owner` | Management | `read_only` | Authoring |
| `architect` | Management | `read_only` | Authoring |
| `engineering-manager` | Management | `read_only` | Authoring (planning only; scheduling is engine code) |
| `backend-developer` | Development | `workspace_write` | Implementation |
| `frontend-developer` | Development | `workspace_write` | Implementation |
| `devops-engineer` | Development | `workspace_write` | Implementation |
| `qa-engineer` | Quality | `workspace_write` (tests only) | Implementation of tests |
| `code-reviewer` | Quality | `read_only` | Review |
| `documentation` | Quality | `workspace_write` (docs only) | Implementation of docs |

Most of what the brief assigns to the Engineering Manager (assignment, dependency management, progress monitoring, parallelism control, budget monitoring) is deterministic and is done by the scheduler and cost service. The role's avatar reflects that engine activity; an AI execution as `engineering-manager` happens only for decomposition and replanning.

### Role definition

Roles ship as built-in YAML and can be overridden per project in `.ai-office/agents/`. Every field the brief requires is present:

```yaml
id: backend-developer                 # unique role identifier
name: Backend Developer
team: development
version: 1
responsibilities:
  - Implement APIs and business logic
  - Design database schemas
  - Write backend tests
input_contract:
  requires: [task, acceptance_criteria, write_scope]
  optional: [contracts, adrs, prior_attempts]
output_contract:
  deliverables: [code_changes]
  report: completion-report@1         # structured final message
allowed_tools:
  permission_profile: workspace_write
  commands: [test, lint, typecheck]   # named commands from project.yaml
permissions:
  write_scope: task                   # may write only the task's declared scope
  network: deny
  install_dependencies: approval
provider_preference:
  provider: auto                      # auto | cursor | claude-code
  fixed: false                        # true = never reroute
  min_tier: standard
context:
  sections: [objective, criteria, constraints, files, prior_attempts]
  token_budget: 6000
budget:
  per_execution: { usd: 1.50, duration_s: 1200 }
completion_criteria:
  - fast_gate_passed
  - all_linked_criteria_addressed
prompt_template: backend-developer@1
```

### Consolidation

The planner outputs, per task, the single role that executes it. Additional executions are added only by rule, according to category:

| Category | Executions for the task |
|----------|-------------------------|
| Simple | One implementation. Review is static checks only |
| Routine | One implementation. AI review once per feature, not per task |
| Complex | One implementation, one AI review |
| Critical | One implementation, one AI review at the strongest tier, on a different provider or model when one is configured, plus human approval |

A developer execution writes its own targeted tests as part of the task. A separate `qa-engineer` execution is created only when the plan contains a test task with its own scope (for example, an end-to-end suite). Independent solutions to the same problem are never requested unless a task is marked for independent verification.

## 2. Workflow driver

One coroutine per active feature reads the feature's stage and gate definition and asks, in order: are the stage's artifacts approved, are its checks passing, is anything waiting on a human? It then either starts the stage's next unit of work or waits on an event. It holds no state of its own; restarting the engine reconstructs every driver from the database.

## 3. Scheduler

A single loop, woken by events (task became ready, execution finished, approval decided, budget changed) rather than by polling.

For each `READY` task in priority order:

1. **Pre-flight.** Dependencies complete, originating artifacts still approved, `needs_reassessment` clear.
2. **Route.** Ask the cost service for provider, tier, and estimate ([cost and context](cost-and-context.md#2-routing)).
3. **Provider check.** Health is fresh and the provider is installed and authenticated. If the task is pinned and the provider is unavailable, the task becomes `BLOCKED`; it is not rerouted.
4. **Admission.** Concurrency limits (global and per provider) and the parallelism rules below.
5. **Budget.** Reserve the estimate against every applicable budget. A refusal moves the task to `NEEDS_APPROVAL`.
6. **Start.** Build the context package, create the worktree, hand the request to the execution manager. `READY -> ASSIGNED -> IN_PROGRESS`.

### Parallel admission

A task may run alongside the tasks already in progress only if all of these hold:

| Check | Rule |
|-------|------|
| Dependencies | No dependency path between the tasks in either direction |
| Write scopes | Declared write globs are disjoint |
| Shared resources | No common exclusive resource (lockfile, migration sequence, port, generated code) |
| Isolation | The project is a git repository, so each task gets its own worktree |
| Benefit | Estimated duration of each task exceeds a configurable floor; very short tasks are not worth a worktree and an integration step |
| Budget | All concurrent estimates can be reserved together |
| Sequential decisions | Neither task is waiting on an architecture decision the other could change |

If any check fails the task waits; the reason is recorded in a `TaskDeferred` event so the user can see why something is not running in parallel. Default concurrency is 2 and is configurable.

Write scope is declared at planning time and enforced after execution: the engine diffs the worktree and compares changed paths to the declared scope. A change outside scope is a violation, which is either discarded or sent to the user as an approval to widen the scope.

### Worktrees and integration

- The engine creates worktrees itself (`git worktree add`) under its data directory, one branch per task: `aio/<feature>/<task>`. It does not use either CLI's own worktree flag, so behavior is identical across providers. ([ADR-0007](../decisions/ADR-0007-engine-managed-worktrees.md))
- **Checkpoint commit.** After a successful execution and scope check, the engine commits the task's changes on the task branch. Agents never run git write commands.
- **Integration checkpoint.** On entering `TESTING`, the task branch is merged into the feature's integration branch, one task at a time. A merge conflict moves the task to `BLOCKED` and creates a conflict-resolution task; nothing is force-resolved.
- **Delivery.** The engine has no permission to merge into the user's base branch. It prepares the integration branch and requests a decision; the merge happens only when the user explicitly approves that specific merge. Task and integration branches are the engine's own, which is why it may commit and integrate there without asking.

## 4. Agent communication

Agents do not converse. A message is a typed record that the engine routes, stores, and includes in the recipient's next context package only if relevant.

```json
{
  "id": "01JD...",
  "sender": "code-reviewer",
  "recipient": "backend-developer",
  "project_id": "PRJ-1",
  "task_id": "TASK-0012",
  "type": "changes_requested",
  "context_refs": ["REV-0004#F2", "FEAT-0001#AC-003"],
  "payload": { "summary": "Token is not invalidated after use", "blocking": true },
  "timestamp": "2026-11-21T14:02:11Z"
}
```

Message types: `handoff`, `question`, `answer`, `changes_requested`, `blocker`, `decision_needed`, `result`. Each has a payload schema and an explicit expected deliverable. A `question` to another role is answered from artifacts and memory when possible; it results in an AI execution only when no stored answer exists, and a `question` to the user becomes an approval-center item. There is no free-form multi-turn exchange between agents.

## 5. Approvals

Approval kinds, each mapped to a policy of `always`, `never`, or `when` (a condition):

| Kind | Default |
|------|---------|
| Specification, architecture | Always |
| Plan | When the estimate exceeds the feature budget or the plan contains critical tasks |
| Scope expansion, permission escalation | Always |
| Dependency installation | Always |
| Destructive file operation (delete or overwrite outside scope) | Always |
| Budget increase | Always |
| External service integration, network access | Always |
| Merge to base branch, merge of a pull request, push to a remote | Always. This is the one policy that cannot be relaxed |
| Deployment command | Always |
| Recovery of an interrupted write execution | Always |

Approvals are decided between executions, not during them ([ADR-0008](../decisions/ADR-0008-approvals-between-executions.md)). The flow when an agent needs something outside its envelope:

1. The provider denies the action. The agent reports it in its completion report (Claude also lists denials in its result).
2. The engine records `PermissionDenied`, moves the task to `NEEDS_APPROVAL`, and raises an approval showing the exact action requested.
3. If approved, the engine either performs the action itself when it is a plain command (for example, installing a dependency) or resumes the provider session with a widened envelope.
4. If rejected, the agent is resumed with the decision, or the task is blocked.

An agent cannot widen its own envelope: envelopes are built by the engine from role, task, and recorded approvals only.

## 6. Control operations

| Operation | Effect |
|-----------|--------|
| Pause task | No new execution starts. A running execution is allowed to finish its current run by default, or is interrupted if the user chooses "pause now" |
| Resume task | Returns to `resume_state`; an interrupted execution resumes its provider session where the provider supports it |
| Stop execution | Graceful interrupt, then terminate, then kill, on the process group. The worktree is kept for inspection |
| Cancel task | Stops any execution, releases reservations and claims; the worktree is removed after confirmation |
| Pause project | Stops scheduling for the project; running executions follow the pause rule |

## 7. Persistence and recovery

Everything the scheduler needs is in SQLite: task states, executions, reservations, claims, approvals, and retry counts. On startup the engine reconciles before scheduling anything:

| Found | Action |
|-------|--------|
| Execution `RUNNING`, runner alive (pid and start time match) | Reattach: continue tailing the output file from the stored offset |
| Execution `RUNNING`, runner gone, exit record present | Process the remaining output and settle normally |
| Execution `RUNNING`, runner gone, no exit record | Mark `INTERRUPTED` |
| `INTERRUPTED`, read-only execution | Retry automatically within the retry budget; it had no side effects |
| `INTERRUPTED`, execution with write access | Do not restart. Inspect the worktree, then ask the user: resume the provider session, keep the changes and continue, or discard and retry |
| Reservation with no live execution | Release |
| Worktree with no task, or task with a missing worktree | Report in a recovery summary; nothing is deleted automatically |
| Pending approvals | Restored as they were |

The engine emits `RecoveryStarted` and `RecoveryCompleted` with a summary the user sees on launch.
