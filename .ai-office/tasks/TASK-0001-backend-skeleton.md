---
id: TASK-0001
type: task
title: Backend skeleton
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
state: REVIEW
feature: FEAT-0001
plan: PLAN-0001
role: backend-developer
category: routine
depends_on: []
implements: [FEAT-0001#FR-002, FEAT-0001#FR-006, FEAT-0001#FR-010]
verifies: [FEAT-0001#AC-003, FEAT-0001#AC-017]
write_scope:
  - backend/pyproject.toml
  - backend/uv.lock
  - backend/src/aio/__init__.py
  - backend/src/aio/main.py
  - backend/src/aio/config/**
  - backend/src/aio/api/**
  - backend/tests/**
---

# TASK-0001: Backend skeleton

## Objective

Create the backend project and the smallest FastAPI application that every later task extends: an application factory, layered settings, structured logging with correlation IDs, a uniform error format, and a health endpoint.

## Deliverables

- A uv-managed Python 3.12 project in `backend/` with the package `aio` under `src/`.
- An application factory in `aio.main` so tests can build an app with their own settings.
- Layered settings (defaults, global configuration file, project configuration) and a function that returns each effective value with the layer it came from.
- Request middleware that assigns a correlation ID and puts it on every log line for that request. Logs are JSON, using the standard library.
- One error format for all API errors. Unhandled errors return it without internal details and are logged with the stack trace.
- `GET /api/v1/health` returning the application version. The schema revision is added by TASK-0002.

## Completion criteria

- AC-003 and AC-017 pass as automated tests.
- The application starts and the health endpoint responds.
- Tests are in the same change, and the task touches nothing outside its write scope.

## References

[System design](../architecture/system-design.md#9-configuration), [events and API](../architecture/design/events-api-observability.md#3-rest-api).
