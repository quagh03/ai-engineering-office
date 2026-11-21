---
id: TASK-0003
type: task
title: Domain core
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
state: BACKLOG
feature: FEAT-0001
plan: PLAN-0001
role: backend-developer
category: simple
depends_on: [TASK-0001]
implements: [FEAT-0001#FR-004]
verifies: []
write_scope:
  - backend/pyproject.toml
  - backend/uv.lock
  - backend/src/aio/domain/**
  - backend/tests/unit/domain/**
---

# TASK-0003: Domain core

## Objective

Create the pure `domain` package that the rest of the engine builds on: identifiers, the event envelope, and the first event types. It performs no I/O and imports no other module of the application.

## Deliverables

- Identifier types: ULIDs for runtime records, and readable keys for projects.
- The event envelope as a Pydantic model, matching the design, with `schema_version`.
- A registry that maps an event type name to its payload model, and the payload models for `ProjectCreated` and `ProjectImported`.

## Completion criteria

- This task verifies no acceptance criterion by itself; it supports AC-006 to AC-008, which TASK-0004 and TASK-0005 verify. Its own checks are unit tests showing that identifiers are unique and sort by creation time, that an envelope with an unknown type or an invalid payload is rejected, and that an envelope survives a round trip through JSON unchanged.
- The package imports nothing from the application outside `aio.domain`.

## References

[Events and API](../architecture/design/events-api-observability.md#1-event-model), [domain model](../architecture/design/domain-model.md#1-entities).
