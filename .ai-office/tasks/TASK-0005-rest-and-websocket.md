---
id: TASK-0005
type: task
title: REST foundation and WebSocket gateway
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
state: BACKLOG
feature: FEAT-0001
plan: PLAN-0001
role: backend-developer
category: complex
depends_on: [TASK-0004]
implements: [FEAT-0001#FR-005, FEAT-0001#FR-006, FEAT-0001#NFR-005]
verifies: [FEAT-0001#AC-008, FEAT-0001#AC-009, FEAT-0001#AC-021]
write_scope:
  - backend/src/aio/api/**
  - backend/src/aio/main.py
  - backend/tests/**
---

# TASK-0005: REST foundation and WebSocket gateway

## Objective

Deliver events to clients reliably. A client subscribes from the last sequence number it saw, receives what it missed, then continues live, and is told to resynchronize when that is not possible.

## Deliverables

- The `/api/v1` router structure and the published OpenAPI description.
- `GET /api/v1/events` with paging and the filters available so far.
- The `/ws` endpoint with the `subscribe`, `event`, and `resync` messages of the design. Replay and live delivery are joined without a gap or a duplicate.
- A bounded send queue per connection. A client that falls behind is sent `resync`.
- REST responses that reflect state carry the sequence number they are consistent with.

## Completion criteria

- AC-008, AC-009, and AC-021 pass as automated tests.
- A test covers the slow-client edge case: the queue limit is reached and the client receives `resync`.
- A test covers events being committed while a replay is in progress: the client still receives each event exactly once and in order.
- `watch_execution` is not implemented; it belongs to FEAT-0004.

## References

[Events and API](../architecture/design/events-api-observability.md#2-real-time-transport).
