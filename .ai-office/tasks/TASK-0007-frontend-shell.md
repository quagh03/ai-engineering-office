---
id: TASK-0007
type: task
title: Frontend shell
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
state: BACKLOG
feature: FEAT-0001
plan: PLAN-0001
role: frontend-developer
category: routine
depends_on: [TASK-0005, TASK-0006, TASK-0008]
implements: [FEAT-0001#FR-009, FEAT-0001#FR-006, FEAT-0001#FR-011]
verifies: [FEAT-0001#AC-015, FEAT-0001#AC-016, FEAT-0001#AC-018]
write_scope:
  - frontend/**
  - scripts/**
  - backend/src/aio/main.py
  - backend/src/aio/api/static.py
  - backend/tests/**
---

# TASK-0007: Frontend shell

## Objective

Give the application its browser UI: a shell that connects to the engine, shows projects, lets the user create or import one, and stays correct through disconnects, driven by events rather than reloads.

## Deliverables

- A Vite, React, and TypeScript project in `frontend/` with Tailwind CSS and the dark theme tokens.
- API types generated from the engine's OpenAPI description, and a check that fails when they are out of date.
- A WebSocket client that subscribes from the last sequence number, reconnects with backoff, and handles `resync` by reloading the snapshot.
- The store and the single event reducer, `applyEvent`, covering the project events.
- The shell: navigation, project list, create and import forms with the server's validation errors shown, and a connection indicator.
- The engine serves the built frontend, so the start command gives the user one URL.
- The check command runs the frontend linting, type checking, and tests.

## Completion criteria

- AC-015 and AC-016 pass as browser tests, and AC-018 passes as a command.
- The reducer has unit tests against recorded event sequences, including a duplicate and an out-of-date event.
- Keyboard navigation and visible focus work across the shell.
- The 3D mode toggle is not shown; no three.js dependency is added.

## References

[Frontend design](../architecture/design/frontend-and-3d-office.md#1-structure), [events and API](../architecture/design/events-api-observability.md#2-real-time-transport).
