---
id: TASK-0008
type: task
title: Project service
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
state: BACKLOG
feature: FEAT-0001
plan: PLAN-0001
role: backend-developer
category: routine
depends_on: [TASK-0004, TASK-0005]
implements: [FEAT-0001#FR-008]
verifies: [FEAT-0001#AC-012, FEAT-0001#AC-013, FEAT-0001#AC-014]
write_scope:
  - backend/alembic/versions/**
  - backend/src/aio/projects/**
  - backend/src/aio/governance/boundary.py
  - backend/src/aio/resources/scaffold/**
  - backend/src/aio/api/**
  - backend/src/aio/domain/**
  - backend/tests/**
---

# TASK-0008: Project service

## Objective

Let the user create a project or import an existing directory, safely. The project's root becomes its workspace boundary, and the `.ai-office/` scaffold is written without ever overwriting an existing file.

## Deliverables

- A migration for the `projects` table.
- Path validation in `aio.governance`: resolve symbolic links, then reject a path that is a file, is already registered, or lies inside or contains a registered project.
- The scaffold: the directory layout of the design, a `project.yaml`, and a constitution template. Only missing items are written.
- Create, import, list, and get, exposed under `/api/v1/projects`. Create and import emit `ProjectCreated` and `ProjectImported` in the same transaction as the project row.
- Whether the directory is a git repository is detected and stored.

## Completion criteria

- AC-012, AC-013, and AC-014 pass as automated tests. AC-013 compares file contents byte for byte before and after.
- A test covers the edge case of a project whose directory was moved or deleted after registration: it is reported as unavailable and nothing is removed from the database.
- If writing the scaffold fails partway, the project is not registered; a test asserts this.

## References

[SDD engine](../architecture/design/sdd-engine.md#1-artifact-repository), [safety and governance](../architecture/design/safety-and-governance.md#2-workspace-boundary).
