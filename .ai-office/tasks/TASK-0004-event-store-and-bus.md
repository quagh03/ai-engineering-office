---
id: TASK-0004
type: task
title: Event store and bus
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
state: BACKLOG
feature: FEAT-0001
plan: PLAN-0001
role: backend-developer
category: complex
depends_on: [TASK-0002, TASK-0003]
implements: [FEAT-0001#FR-004]
verifies: [FEAT-0001#AC-006, FEAT-0001#AC-007]
write_scope:
  - backend/alembic/versions/**
  - backend/src/aio/events/**
  - backend/src/aio/persistence/**
  - backend/tests/**
---

# TASK-0004: Event store and bus

## Objective

Make it impossible for a state change and its event to diverge. Events are appended inside the unit of work that changes state, and are published to subscribers only after that unit of work commits.

## Deliverables

- A migration for the `events` table with the columns and indexes in the design.
- An event store that appends within the current unit of work and reads by sequence number with filters.
- An in-process bus. Events recorded during a unit of work are held and published, in sequence order, only after a successful commit; a rollback discards them.
- A query for "events after sequence N", used by TASK-0005.

## Completion criteria

- AC-006 and AC-007 pass as automated tests, including a forced failure on each side of the transaction.
- A test shows that a failing subscriber does not affect the committed state or the other subscribers.
- `aio.events` depends only on `aio.domain` and `aio.persistence`.

## References

[ADR-0002](../architecture/decisions/ADR-0002-state-tables-plus-event-log.md), [events and API](../architecture/design/events-api-observability.md#1-event-model).
