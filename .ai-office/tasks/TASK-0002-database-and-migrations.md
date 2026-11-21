---
id: TASK-0002
type: task
title: Database and migrations
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
state: BACKLOG
feature: FEAT-0001
plan: PLAN-0001
role: backend-developer
category: routine
depends_on: [TASK-0001]
implements: [FEAT-0001#FR-003]
verifies: [FEAT-0001#AC-004, FEAT-0001#AC-005]
write_scope:
  - backend/pyproject.toml
  - backend/uv.lock
  - backend/alembic.ini
  - backend/alembic/**
  - backend/src/aio/persistence/**
  - backend/src/aio/main.py
  - backend/src/aio/api/health.py
  - backend/tests/**
---

# TASK-0002: Database and migrations

## Objective

Give the engine its SQLite database: created in the application data directory, opened in WAL mode with foreign keys enforced, upgraded by versioned migrations at startup, and accessed through a unit of work.

## Deliverables

- Database engine setup and a unit-of-work abstraction in `aio.persistence`. All writes go through it.
- Alembic configured, with a first migration that creates only what this feature needs so far.
- Startup: create the data directory if missing, apply pending migrations, refuse to start on a newer schema.
- A single-instance lock on the data directory.
- The health endpoint reports the schema revision.

## Completion criteria

- AC-004 and AC-005 pass as automated tests.
- Tests cover these edge cases from the specification: the data directory is missing (created), the data directory is not writable (startup fails naming the path), and a second instance on the same data directory refuses to start.
- Tests use a temporary data directory and never the real one.

## References

[Domain model](../architecture/design/domain-model.md#2-schema), [ADR-0001](../architecture/decisions/ADR-0001-local-modular-monolith.md).
