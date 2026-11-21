---
id: ADR-0008
type: adr
title: Approvals happen between executions, under permission envelopes
version: 1
status: in_review
derives_from: [SYSTEM-DESIGN]
---

# ADR-0008: Approvals happen between executions, under permission envelopes

## Context

High-impact operations need human approval. Both CLIs are run non-interactively. In that mode, with the flags verified on the installed versions, an action that would need approval is denied rather than held for an answer; there is no provider-neutral way to pause a run and wait for a human.

## Decision

Each execution runs under a **permission envelope** fixed before it starts. Anything outside the envelope is denied by the provider. The agent reports what it needed; the engine turns that into an approval request. If granted, the engine either performs the action itself (when it is a plain command) or resumes the provider session with a widened envelope for that task. Approvals are therefore decided at boundaries: before a stage, before an execution, or between two runs of the same session.

The engine also enforces the envelope independently after the run by inspecting the worktree diff.

## Rationale

- Works identically on both providers using only verified capabilities.
- An execution never sits idle holding a paid session open while waiting for a person.
- The envelope is built only by the engine, so an agent cannot widen its own permissions.

## Consequences

- A denied action costs a round trip: the run ends or continues without it, and a follow-up run is needed after approval. Envelopes should therefore be generous enough for the task's normal needs (declared commands, declared scope) and strict about everything else.
- Session resume is relied on to make the follow-up cheap.
- If a provider later exposes a supported way to route permission prompts to a host, mid-run approval can be added behind a capability flag without changing this model.

## Alternatives rejected

- Running with all permissions and reviewing afterwards: destructive actions would already have happened.
- Driving the CLIs interactively through a pseudo-terminal: fragile, unsupported, and provider-specific.
