---
id: ADR-0009
type: adr
title: Three cost measurement levels and multi-meter budgets
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
derives_from: [SYSTEM-DESIGN]
---

# ADR-0009: Three cost measurement levels and multi-meter budgets

## Context

The two providers report different things. Claude Code reports a cost per run, which its documentation describes as a client-side estimate, and which is a cumulative conversation total when a session is resumed. Cursor's documented output reports durations only. Users may pay per unit or through a subscription, where a per-run dollar figure is not money actually spent. The brief forbids fabricating costs and forbids exceeding budgets silently.

## Decision

1. Every cost record has a **measurement level**: `provider_reported`, `estimated` (computed by the engine from reported usage and user-configured prices or rates), or `unknown`.
2. Every record has a **billing basis** set per provider by the user: `metered` or `subscription`. Subscription amounts are notional and labeled so. The default is `subscription` for both providers, which is how they are used here.
3. Budgets are defined per **meter**: `usd`, `tokens`, `executions`, `duration_s`. Executions and duration are always measurable and are always enforceable.
4. Budget consumption uses **reservations**: an estimate is reserved before a run and replaced by the actual amount after it.
5. Aggregates never hide uncertainty: a total containing unknown values is shown as a lower bound with the number of unmeasured executions.

## Rationale

- The brief's first level is called "exact"; the only available figure is self-described as an estimate, so the honest name is `provider_reported`.
- A USD-only budget would silently fail to bound any provider that reports no cost.
- Reservations are the only way to stop parallel executions from jointly overshooting.

## Consequences

- Every cost shown in the UI carries a label, which adds visual weight but prevents false precision.
- The user must configure billing basis and, optionally, prices and rates; defaults leave unreported cost as `unknown` rather than guessing.
- Routing cannot always compare providers on cost and must say when it cannot.
- For resumed sessions, the recorded cost is the difference from the session's previous total.

## Alternatives rejected

- Estimating Cursor cost from duration or output length by default: a fabricated figure.
- Treating subscription usage as zero cost: contradicts the brief and hides consumption of a limited plan.
