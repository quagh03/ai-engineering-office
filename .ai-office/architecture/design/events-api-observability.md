---
id: DN-0006
type: design-note
title: Events, API, and observability
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
derives_from: [PRD, SYSTEM-DESIGN]
---

# Events, API, and Observability

## 1. Event model

Every meaningful state change is written as an event **in the same SQLite transaction as the change itself**, then published to subscribers after commit. A state change without its event, or an event without its state change, cannot exist. State tables remain the source for queries; the event log is the history and the live feed. ([ADR-0002](../decisions/ADR-0002-state-tables-plus-event-log.md))

### Envelope

```json
{
  "seq": 18422,
  "id": "01JD8Z3K6Q...",
  "type": "TaskStarted",
  "ts": "2026-11-21T14:02:11.482Z",
  "schema_version": 1,
  "project_id": "PRJ-1",
  "feature_id": "FEAT-0001",
  "task_id": "TASK-0012",
  "execution_id": "01JD8Z3H...",
  "role_id": "backend-developer",
  "provider": "claude-code",
  "severity": "info",
  "correlation_id": "01JD8Y...",
  "causation_id": "01JD8Z3J...",
  "payload": {}
}
```

- `seq` is strictly increasing in commit order. Clients use it to resume.
- `correlation_id` groups everything caused by one user action or workflow step; `causation_id` is the event that directly led to this one. Together they let the inspector show why something happened.
- Each event type has a Pydantic payload model. TypeScript types are generated from the same definitions.

### Persisted and ephemeral

| Kind | Examples | Stored |
|------|----------|--------|
| Domain events | Everything in the catalog below | `events` table, kept |
| Stream events | Assistant text deltas, raw tool payloads | The execution's output file only; relayed live to clients subscribed to that execution |

Text deltas are high-volume and reconstructible from the output file, so writing each one to the database would cost write throughput and disk for no benefit.

### Catalog

| Group | Types |
|-------|-------|
| Project | `ProjectCreated`, `ProjectImported`, `ProjectAnalyzed`, `ProjectPaused`, `ProjectResumed` |
| Specification | `ArtifactDrafted`, `ArtifactRevised`, `ArtifactApproved`, `ArtifactRejected`, `SpecificationChanged`, `ImpactAnalysisCompleted`, `TraceLinkCreated`, `TraceLinkStale` |
| Workflow | `FeatureCreated`, `StageEntered`, `StageGatePassed`, `StageGateFailed`, `FeatureDelivered` |
| Agent | `AgentCreated`, `AgentStarted`, `AgentThinking`, `AgentActivityChanged`, `AgentIdle`, `AgentMessageSent` |
| Task | `TaskCreated`, `TaskReady`, `TaskAssigned`, `TaskStarted`, `TaskDeferred`, `TaskBlocked`, `TaskPaused`, `TaskResumed`, `TaskFailed`, `TaskCancelled`, `TaskCompleted`, `TaskNeedsReassessment` |
| Provider | `ProviderHealthChanged`, `ProviderSelected`, `ProviderExecutionStarted`, `ProviderExecutionCompleted`, `ProviderExecutionFailed`, `ProviderExecutionCancelled`, `ExecutionRetryScheduled`, `ExecutionAvoided` |
| Code | `CodeModified`, `ChangeSetRecorded`, `ScopeViolationDetected`, `CheckpointCommitted`, `BranchIntegrated`, `MergeConflictDetected` |
| Verification | `TestStarted`, `TestPassed`, `TestFailed`, `VerificationReused`, `CriterionVerified`, `CriterionFailed`, `CriterionWaived` |
| Review | `CodeReviewStarted`, `CodeReviewCompleted` |
| Approval | `ApprovalRequested`, `ApprovalGranted`, `ApprovalRejected`, `ApprovalExpired`, `PermissionDenied` |
| Cost | `CostRecorded`, `BudgetReserved`, `BudgetWarning`, `BudgetReassessment`, `BudgetExceeded`, `BudgetAdjusted` |
| Context | `ContextBuilt`, `ContextOptimized`, `CacheHit`, `MemoryProposed`, `MemoryAccepted`, `MemoryConflict` |
| System | `RecoveryStarted`, `RecoveryCompleted`, `PolicyViolation`, `ConfigurationChanged` |

This includes every event named in the brief. `AgentThinking` and `AgentActivityChanged` are derived from the provider's real stream (model output in progress; a read, write, or shell tool call open), never from a timer.

`ContextOptimized` reports the package's estimated size and what was excluded and why, which makes context savings observable.

## 2. Real-time transport

One WebSocket endpoint, `/ws`.

```text
client -> { "op": "subscribe", "since": 18400, "filter": { "project_id": "PRJ-1" } }
server -> { "op": "event", "event": { ...envelope... } }        # replay, then live
client -> { "op": "watch_execution", "execution_id": "01JD8Z3H..." }
server -> { "op": "stream", "execution_id": "...", "chunk": { ... } }   # ephemeral
server -> { "op": "resync", "reason": "gap" }
```

**Consistency.** The client loads a REST snapshot, which carries the `seq` it reflects, then subscribes with `since` set to that value. Events are applied in order through one reducer. On reconnect it subscribes from its last `seq`. If the server cannot replay from there, it sends `resync` and the client reloads the snapshot. Both UI modes use this one connection and one store, so they cannot disagree.

**Backpressure.** Each connection has a bounded queue. A client that falls behind is sent `resync` rather than allowed to grow the queue without limit.

## 3. REST API

Commands and queries under `/api/v1`. Types are published as OpenAPI and the frontend client is generated from it.

| Area | Endpoints (representative) |
|------|----------------------------|
| Projects | `POST /projects` (create or import), `GET /projects`, `GET /projects/{id}`, `POST /projects/{id}/pause`, `POST /projects/{id}/resume`, `POST /projects/{id}/analyze` |
| Features | `POST /projects/{id}/features` (describe an idea), `GET /features/{id}`, `POST /features/{id}/answers`, `POST /features/{id}/advance` |
| Artifacts | `GET /projects/{id}/artifacts`, `GET /artifacts/{id}`, `GET /artifacts/{id}/revisions/{v}`, `PUT /artifacts/{id}` (new draft), `GET /artifacts/{id}/impact` |
| Traceability | `GET /trace?node=...&direction=up\|down`, `GET /features/{id}/criteria` (verification matrix) |
| Tasks | `GET /features/{id}/tasks`, `POST /tasks`, `PATCH /tasks/{id}`, `POST /tasks/{id}/{pause\|resume\|cancel\|retry}`, `GET /tasks/{id}/dependencies` |
| Executions | `GET /executions?...`, `GET /executions/{id}`, `GET /executions/{id}/log`, `GET /executions/{id}/context`, `POST /executions/{id}/stop` |
| Agents | `GET /agents`, `GET /agents/{role}`, `PUT /agents/{role}` |
| Approvals | `GET /approvals?status=pending`, `POST /approvals/{id}/decision` |
| Providers | `GET /providers`, `POST /providers/{id}/check`, `PUT /providers/{id}/config` |
| Cost | `GET /budgets`, `PUT /budgets/{id}`, `GET /cost/summary`, `GET /cost/breakdown?by=task\|feature\|provider\|role` |
| Events | `GET /events` with all inspector filters, `GET /events/{id}` |
| Verification | `GET /features/{id}/verification`, `GET /verification-runs/{id}` |
| System | `GET /health`, `GET /config/effective`, `GET /recovery/summary` |

Commands return the resulting resource and the `seq` of the event they caused. Invalid state transitions return `409` with the current state and the allowed transitions.

## 4. Observability

Everything the UI shows is a query over state tables or the event log.

| View | Source |
|------|--------|
| Live agent status | Running executions joined with roles and tasks |
| Execution timeline | Events for a correlation id, ordered by `seq` |
| Task progress | Task states; completion-criteria status |
| Provider health | `provider_status` and `ProviderHealthChanged` |
| Token usage, cost | `cost_records`, with measurement level |
| Execution duration | `executions` |
| Error tracking | Failed executions by error class, with raw evidence |
| Retry history | Execution chains through `retry_of` |
| Test results | `verification_runs`, including which were reused |
| Approval notifications | Pending approvals |
| Budget alerts | Budget events and current ledger position |

### Event inspector

A filterable, virtualized list over `GET /events` that continues live.

- **Filters:** project, agent role, task, provider, event type, execution status, severity, date range. All filter columns are indexed.
- **Detail:** full envelope and payload; the causation chain upward and the events it caused; links to the task, execution, artifact revision, and context manifest.
- **Execution drill-down:** the normalized event stream beside the provider's raw output, the exact prompt sent, the context manifest with provenance, the diff produced, and the cost record.

This is the debugging tool for agent behavior: for any execution it shows what the agent was told, what it did, what it produced, and what it cost.

## 5. Logging

Structured JSON logs for the engine itself (separate from domain events), with the correlation id on every line, written to a rotating file in the app data directory. Secrets are redacted before anything is written to a log, an event, or an execution summary ([safety](safety-and-governance.md#4-secrets)).

## 6. Retention

Events are kept by default so history can be reconstructed. Raw execution output is the largest data set and has a configurable retention (age or total size); pruning it keeps the execution record, cost record, manifest, and summary.
