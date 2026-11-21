---
id: TASK-0006
type: task
title: Local API protection
version: 1
status: draft
state: BACKLOG
feature: FEAT-0001
plan: PLAN-0001
role: backend-developer
category: critical
depends_on: [TASK-0005]
implements: [FEAT-0001#FR-007, FEAT-0001#NFR-003]
verifies: [FEAT-0001#AC-010, FEAT-0001#AC-011]
write_scope:
  - backend/src/aio/governance/**
  - backend/src/aio/api/**
  - backend/src/aio/main.py
  - backend/tests/**
---

# TASK-0006: Local API protection

## Objective

Ensure that only the application's own UI can use the local API. A local server that will later start agents and run commands must not be drivable by another website open in the user's browser.

## Deliverables

- The server binds to `127.0.0.1` only, with no setting to change the interface.
- `Host` and `Origin` validation on every REST request and WebSocket upgrade.
- A per-installation token, generated on first start and stored with user-only file permissions in the data directory. It is required on every request and upgrade, and compared in constant time.
- A way for the UI served by the engine to obtain the token that a page from another origin cannot use. The mechanism is documented in the code and in the review request.
- No permissive CORS headers.

## Completion criteria

- AC-010 and AC-011 pass as automated tests. AC-010 covers each rejection case separately for REST and for WebSocket, and asserts that no state changed.
- The token never appears in a log line or in a URL that is logged; a test asserts this.
- Because this task is classified critical, it gets its own code review before TASK-0007 starts, and the user approves the result.

## References

[Safety and governance](../architecture/design/safety-and-governance.md#6-local-api-protection).
