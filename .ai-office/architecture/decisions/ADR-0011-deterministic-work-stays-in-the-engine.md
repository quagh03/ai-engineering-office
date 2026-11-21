---
id: ADR-0011
type: adr
title: Deterministic work is never delegated to AI
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
derives_from: [SYSTEM-DESIGN]
---

# ADR-0011: Deterministic work is never delegated to AI

## Context

Many activities in the brief are assigned to agent roles: running tests, managing dependencies between tasks, monitoring budgets, checking traceability, producing reports. An AI execution is the most expensive and least repeatable way to do anything that has a mechanical answer.

## Decision

If a piece of work can be done correctly by ordinary code, the engine does it. A provider execution is started only for work that needs judgment: understanding intent, writing specifications and designs, decomposing work, writing and fixing code, and reviewing it.

Done by the engine, with no execution:

- Running tests, linters, type checkers, and builds, and deciding pass or fail from their results
- All git operations
- Scheduling, dependency resolution, assignment, parallel admission
- Task classification, routing, estimation, budget enforcement and reassessment
- Specification diffing and impact analysis
- File and symbol indexing, context assembly
- Scope checks, quality gate evaluation, criterion status
- Delivery, cost, and execution reports
- Cache validation and result reuse

Every execution request passes a gate that checks for a deterministic path, a valid cached result, or an existing stored answer first, and records an `ExecutionAvoided` event when it finds one.

## Rationale

- These activities are cheaper, faster, and reproducible as code, and their results are evidence rather than an agent's claim.
- A task cannot be marked complete because an agent says tests pass; the engine ran them.
- Avoided executions are counted, which lets savings be measured.

## Consequences

- Roles such as Engineering Manager and QA Engineer do most of their listed duties through engine code; their avatars reflect that activity without an AI session behind it.
- The project must declare its commands (`test`, `lint`, and so on) so the engine can run them.
- Rule-based classification and profile selection will sometimes be wrong; the user can override, and misclassifications are visible in estimate-versus-actual data.

## Alternatives rejected

- Asking an agent to run and interpret tests: pays for tokens to do what an exit code states, and makes the result an unverifiable claim.
- A separate AI call to classify each task: an extra execution per task for a decision that rules and the planner's existing output can make.
