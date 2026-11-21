---
id: ADR-0001
type: adr
title: Local modular monolith on Python and FastAPI
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
derives_from: [SYSTEM-DESIGN]
---

# ADR-0001: Local modular monolith on Python and FastAPI

## Context

The platform runs on one user's machine, coordinates a handful of subprocesses, and must be easy to start and stop. The brief lists many services (project management, SDD, orchestration, scheduler, event bus, memory, context, execution, cost, observability, approvals) and prefers Python with FastAPI unless evaluation shows a compelling reason otherwise.

## Decision

Build one backend process, a modular monolith with hexagonal boundaries. The brief's "services" are modules with typed interfaces inside that process, communicating by direct calls and an in-process event bus. Use Python 3.12, FastAPI, and a single uvicorn worker. Enforce module boundaries with import-linter in CI.

## Rationale

- One local user and a few concurrent executions do not need horizontal scale; separate services would add processes, ports, and failure modes with no benefit.
- The scheduler, budget ledger, and state machines are far simpler and safer with a single writer.
- Evaluation of the alternative stack: a TypeScript backend would share types with the frontend, but that is solved by generating the client from OpenAPI. Neither CLI offers a reason to prefer one language, since both are driven as subprocesses. No compelling reason to depart from the brief's preference was found.

## Consequences

- Startup is one process and one database file.
- A long CPU-bound task in the engine would block the event loop; indexing and hashing run in a worker thread pool.
- If a module ever needs to become a separate process, its interface already exists.

## Alternatives rejected

- Multiple services with a message broker: operational weight without a need.
- Multiple uvicorn workers: breaks the single-writer assumption.
- Docker Compose for the engine: the CLIs authenticate through host credentials that a container cannot reach.
