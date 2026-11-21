---
id: FEAT-0001
type: feature-spec
title: Application foundation
version: 1
status: in_review
workflow_profile: full
derives_from: [PRD#US-001, PRD#US-002, PRD#PR-010, PRD#PR-011, PRD#PR-100, PRD#PR-101, PRD#PR-102, PRD#CON-001, PRD#CON-002]
---

# FEAT-0001: Application foundation

## Summary

A running local application with nothing intelligent in it yet: the engine starts, stores state in SQLite, records every state change as an event, streams events to a browser UI, and lets the user create or import a project. Every later feature is built on this. It corresponds to Phase 1 of the [roadmap](../../../plans/roadmap.md).

Design references: [system design](../../../architecture/system-design.md), [domain model](../../../architecture/design/domain-model.md), [events and API](../../../architecture/design/events-api-observability.md), [safety](../../../architecture/design/safety-and-governance.md#6-local-api-protection).

## User stories

- **US-001** As the user, I start the application with one command and see it running in my browser. (PRD#US-001)
- **US-002** As the user, I create a new project or import an existing directory and see it appear immediately. (PRD#US-002)
- **US-003** As the user, I can stop and restart the application without losing anything. (PRD#US-017, in part)

## Functional requirements

- **FR-001** One command starts the engine, which serves the web UI on a configurable loopback port. One command stops it cleanly.
- **FR-002** Configuration is layered: built-in defaults, then global configuration, then project configuration. The effective value of each setting and the layer it came from can be queried.
- **FR-003** State is stored in a SQLite database in the application data directory. The schema is created and upgraded by versioned migrations that run at startup.
- **FR-004** Every state change writes its event in the same transaction. Subscribers are notified only after the transaction commits.
- **FR-005** Clients receive events over a WebSocket. A client can subscribe from a given sequence number, receive what it missed in order, and then continue live. When the server cannot replay from that point it tells the client to resynchronize.
- **FR-006** A versioned REST API is exposed with a published OpenAPI description, a health endpoint, and one uniform error format.
- **FR-007** The local API accepts requests only from the application's own UI.
- **FR-008** The user can create a project in an empty or new directory, import an existing directory, and list and open projects. Creating or importing writes the `.ai-office/` scaffold without overwriting anything that already exists.
- **FR-009** The web UI provides an application shell: dark theme, navigation, a project list, project creation and import, and a connection indicator. It updates from events without a reload.
- **FR-010** The engine writes structured logs. Every request has a correlation ID that appears on each log line and each event it causes.
- **FR-011** One command runs every quality check: formatting, linting, type checking, module boundary rules, and tests for backend and frontend.

## Non-functional requirements

- **NFR-001** Type checking is strict in backend (mypy) and frontend (tsc), with no unexplained suppressions.
- **NFR-002** The module dependency rules in the system design are enforced by an automated check.
- **NFR-003** The engine listens on the loopback interface only, and this feature makes no outbound network connection.
- **NFR-004** Runs on macOS with Python 3.12 and Node.js 22.
- **NFR-005** A reconnecting client is consistent within two seconds of the engine becoming available on a database of 10,000 events.

## Acceptance criteria

- **AC-001** (verifies FR-001; method: command) From a clean checkout with dependencies installed, the start command brings the engine up, the health endpoint returns success with the application version and database schema revision, and the stop command ends the process with a zero exit code.
- **AC-002** (verifies FR-001; method: automated_test) When the configured port is in use, startup fails with a message naming the port and a non-zero exit code, and leaves no process behind.
- **AC-003** (verifies FR-002; method: automated_test) For a setting defined at all three layers, the project value wins over the global value, which wins over the default, and the effective-configuration query reports the winning layer.
- **AC-004** (verifies FR-003; method: automated_test) Starting against an empty data directory creates the database at the latest schema revision. Downgrading to the base revision and upgrading again succeeds.
- **AC-005** (verifies FR-003; method: automated_test) Starting against a database whose schema revision is newer than the code refuses to start, explains why, and leaves the database unchanged.
- **AC-006** (verifies FR-004; method: automated_test) If a state change fails, no event for it is stored. If storing the event fails, the state change is rolled back.
- **AC-007** (verifies FR-004; method: automated_test) A subscriber is never notified of an event whose transaction did not commit, and receives committed events in sequence order.
- **AC-008** (verifies FR-005; method: automated_test) A client that subscribes from sequence N receives every event after N exactly once and in order, followed by live events, with none missing.
- **AC-009** (verifies FR-005; method: automated_test) A client that subscribes from a sequence number the server cannot replay from receives a resynchronize message instead of events.
- **AC-010** (verifies FR-007; method: automated_test) A REST request or WebSocket upgrade with a foreign `Origin`, an unexpected `Host`, or a missing or wrong token is rejected and causes no state change.
- **AC-011** (verifies FR-007, NFR-003; method: automated_test) The engine's listening socket is bound to the loopback address only.
- **AC-012** (verifies FR-008; method: automated_test) Creating a project in an empty directory writes the scaffold, stores the project, and emits `ProjectCreated`.
- **AC-013** (verifies FR-008; method: automated_test) Importing a directory that already contains `.ai-office/` files leaves every existing file byte-for-byte unchanged, adds only what is missing, and emits `ProjectImported`.
- **AC-014** (verifies FR-008; method: automated_test) Each of these is rejected with a specific error and no change on disk or in the database: a path that does not exist and cannot be created, a path that is a file, a directory already registered, and a directory inside or containing a registered project, including through a symbolic link.
- **AC-015** (verifies FR-009, FR-005; method: automated_test) A project created in one browser tab appears in the project list of a second open tab without a reload.
- **AC-016** (verifies FR-009, US-003; method: automated_test) When the engine is stopped the UI shows that it is disconnected. When the engine restarts, the UI reconnects by itself and shows the same projects, including one created through the API while the UI was disconnected.
- **AC-017** (verifies FR-010, FR-006; method: automated_test) Log lines written while handling a request carry that request's correlation ID. An unhandled error returns the uniform error format without internal details and is logged with its stack trace.
- **AC-018** (verifies FR-006; method: command) The OpenAPI description is served, and the check command fails if the generated frontend client does not match it.
- **AC-019** (verifies FR-011, NFR-001, NFR-002; method: command) The check command passes on a clean checkout, and fails when a deliberate type error, boundary violation, or failing test is introduced.
- **AC-020** (verifies NFR-003; method: review) Review confirms that no code in this feature opens an outbound network connection.
- **AC-021** (verifies NFR-005; method: automated_test) With 10,000 stored events, a client reconnecting from the latest sequence number it saw is up to date within two seconds.
- **AC-022** (verifies NFR-004; method: command) On macOS with Python 3.12 and Node.js 22 the start and check commands run. Under a different Python or Node.js major version they refuse to run and name the version required.

## Edge cases

- The application data directory does not exist, or is not writable: created if possible; otherwise startup fails with the path named.
- Two engine instances started against the same data directory: the second refuses to start.
- A WebSocket client that reads too slowly: it is told to resynchronize rather than letting its queue grow without limit.
- A project directory that is moved or deleted after registration: the project is shown as unavailable; nothing is deleted from the database.
- An imported directory that is not a git repository: imported and marked as such. Offering `git init` belongs to FEAT-0004.

## Constraints

- The stack is fixed by PRD#PR-101 and the [system design](../../../architecture/system-design.md#6-technology-stack).
- Every third-party dependency is listed with its purpose in the plan and approved with it (constitution C-041).
- The scaffold written by FR-008 follows the layout in the [SDD engine design](../../../architecture/design/sdd-engine.md#1-artifact-repository). It contains directories, `project.yaml`, and a constitution template only; artifact management is FEAT-0002.

## Dependencies

None. This is the first feature.

## Out of scope

Artifact parsing, versioning, and approval (FEAT-0002). Tasks, roles, and scheduling (FEAT-0003). Providers and executions (FEAT-0004). Budgets and cost (FEAT-0005). The 3D office (FEAT-0008); the mode toggle is not shown until then.
