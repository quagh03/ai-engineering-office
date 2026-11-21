---
id: ADR-0004
type: adr
title: Agents are roles; executions are the unit of AI work
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
derives_from: [SYSTEM-DESIGN]
---

# ADR-0004: Agents are roles; executions are the unit of AI work

## Context

The brief describes nine agents with avatars, and also requires that the platform not spawn a process per role, prefer logical delegation, and avoid unnecessary sessions.

## Decision

An agent is a **role**: a versioned configuration record (responsibilities, contracts, permissions, provider preference, context needs, budget, completion criteria, prompt template). An **execution** is one provider process acting as exactly one role for one unit of work. Roles have no process, no session, and no state between executions; continuity comes from artifacts, task records, and memory. Work that needs no judgment is done by the engine and attributed to the role that owns it without any execution.

## Rationale

- Cost follows executions, so making the execution the unit makes cost attributable and controllable.
- Stateless roles make restart recovery trivial: there is no agent state to restore.
- The number of executions for a task is set by its category, not by how many roles exist.

## Consequences

- An avatar's activity is derived from executions and task state. A role with nothing running is idle and is shown idle.
- Two parallel tasks of the same role are two executions of one role, shown as two workstations.
- "Agent memory" is stored data keyed by role, not a live conversation.
- A resumed provider session is an optimization within one task, never a standing agent.

## Alternatives rejected

- One long-lived session per role: nine idle contexts, growing history, and unclear cost attribution.
- One session playing several roles in a single run: saves a start-up but blurs attribution, permissions, and independent review.
