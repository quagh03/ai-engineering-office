---
id: ADR-0002
type: adr
title: State tables plus an append-only event log, written in one transaction
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
derives_from: [SYSTEM-DESIGN]
---

# ADR-0002: State tables plus an append-only event log, written in one transaction

## Context

All meaningful activity must produce structured events that update state, drive the UI in real time, and allow history to be reconstructed after a restart. The state must also be queryable for a task board, analytics, and scheduling.

## Decision

Keep normal relational state tables as the source for queries and decisions. Every state change also inserts its event into an append-only `events` table **in the same transaction**. Events are published to in-process subscribers and WebSocket clients only after the transaction commits. High-volume stream output (text deltas) is not stored as events; it stays in the execution's output file.

## Rationale

- One transaction guarantees state and history never diverge, without a separate outbox relay.
- Queries stay simple SQL over current state rather than folds over an event stream.
- A strictly increasing `seq` gives clients exact resume and replay.

## Consequences

- The event log is a complete history but is not the mechanism for rebuilding state; state tables are authoritative. Rebuilding state from events is not supported.
- Event payload schemas are versioned, because old events remain readable forever.
- If the engine stops between commit and publish, the event is in the log but was not delivered live. Clients receive it on replay by `seq`; in-process consumers such as the scheduler recover by reconciling from state tables at startup rather than from missed notifications.

## Alternatives rejected

- Full event sourcing: stronger guarantees than needed, at the cost of projections, snapshots, and schema migration for every event, for a single-user local application.
- Events published without persistence: history would not survive a restart.
