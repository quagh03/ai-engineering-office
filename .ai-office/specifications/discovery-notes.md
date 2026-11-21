---
id: DISC-0001
type: discovery-notes
title: Requirements analysis and discovery notes
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
---

# Requirements Analysis

Date: 2026-11-21. Source: the product brief (sections 1-18).

This document records what was verified before designing, how conflicts and gaps in the brief were resolved, the main risks, and the minimum viable implementation. Every resolution here is a decision the rest of the design depends on. The questions that needed the user's input were answered on 2026-11-21 and are recorded under [Resolved questions](#8-resolved-questions).

## 1. What is being built

A local application that takes a software idea through eight SDD stages (discovery, specification, architecture, planning, implementation, verification, review, delivery), using Cursor CLI and Claude Code CLI as the only AI execution environments, with cost control and human approval built into the engine and a dashboard plus 3D office as views over real engine state.

## 2. Verified facts

Checked on the development machine on 2026-11-21. Nothing in the provider design relies on a flag that is not in this list.

| Fact | Source |
|------|--------|
| Cursor CLI `2026.11.19-f005e9d` is installed as `cursor-agent` and `agent` | `cursor-agent --version` |
| Claude Code CLI `2.1.222` is installed as `claude` | `claude --version` |
| Cursor print mode: `-p`, `--output-format text\|json\|stream-json`, `--stream-partial-output`, `--mode plan\|ask`, `--model`, `--force`, `--sandbox enabled\|disabled`, `--trust`, `--workspace`, `--resume [chatId]`, `--worktree` | `cursor-agent --help` |
| Cursor health: `status --format json`, `about --format json`, `models` | subcommand `--help` |
| Claude print mode: `-p`, `--output-format text\|json\|stream-json`, `--include-partial-messages`, `--verbose`, `--model`, `--effort`, `--permission-mode`, `--allowedTools`, `--disallowedTools`, `--tools`, `--max-budget-usd`, `--json-schema`, `--session-id`, `--resume`, `--append-system-prompt`, `--bare`, `--setting-sources`, `--strict-mcp-config`, `--add-dir` | `claude --help` |
| Claude health: `auth status --json`, `doctor` | subcommand `--help` |
| `cursor-agent status --format json` exits `0` when unauthenticated; `claude auth status --json` exits `1` when not logged in | observed |
| Cursor `result` event carries `duration_ms`, `duration_api_ms`, `result`, `session_id`, `request_id`. No cost or token fields are documented | [Cursor output format](https://cursor.com/docs/cli/reference/output-format) |
| Cursor print mode edits workspace files even without `--force`; actions needing approval are rejected, not prompted | [Cursor headless](https://cursor.com/docs/cli/headless) |
| Cursor permissions are `allow` / `deny` token lists in `<project>/.cursor/cli.json` or `~/.cursor/cli-config.json`; deny wins | [Cursor permissions](https://cursor.com/docs/cli/reference/permissions) |
| Claude `result` carries `total_cost_usd` and a per-model breakdown, described as client-side estimates. With `--resume`, the figure is the cumulative conversation total | [Claude Code headless](https://code.claude.com/docs/en/headless) |
| Claude exits `143` on SIGTERM and leaves the turn unfinished; SIGINT ends the turn first | same |
| Claude `--bare` does not read OAuth or keychain credentials; it needs an API key | same |

Two consequences worth stating up front:

- **The published docs are ahead of the installed CLI.** The Claude docs describe `--permission-prompts none` (v2.1.259+), which the installed 2.1.222 does not have. Capabilities must be detected from the installed binary, never assumed from documentation.
- **Not yet verified:** the exact field names of Claude's token usage block, whether the installed Cursor CLI emits any undocumented usage fields, and Cursor's behavior on SIGINT/SIGTERM. These need one real authenticated run per provider, which is the first task of Phase 4. That run spends real usage, so it was not done during design.

## 3. Ambiguities and resolutions

| # | Issue in the brief | Resolution |
|---|--------------------|------------|
| A1 | The task state machine orders `REVIEW -> TESTING` (6.1), but the lifecycle orders Verification before Review (4.1). Reviewing code that fails its tests wastes an AI review. | Both are kept, at different levels. A task leaves `IN_PROGRESS` only after the engine's fast gate passes (lint, typecheck, targeted tests; no AI). `REVIEW` is the code review gate. `TESTING` is acceptance verification of the task's change integrated into the feature branch. Feature-level stages 6 and 7 then run in the brief's order. See [domain model](../architecture/design/domain-model.md#3-task-state-machine). |
| A2 | "Exact provider-reported cost" (5.10). Claude documents its figure as a client-side estimate, and under a subscription it is a notional API-equivalent amount, not money spent. | The level is named `provider_reported` and is shown with its billing basis (`metered` or `subscription`). The UI never calls it "exact". See [ADR-0009](../architecture/decisions/ADR-0009-cost-measurement-and-budget-meters.md). |
| A3 | Budgets are expressed in money, but Cursor reports no cost, so a USD budget cannot be enforced for it. | Budgets are multi-meter: USD, tokens, execution count, wall-clock duration. Count and duration are always measurable. An execution with unknown cost is never counted as zero silently. |
| A4 | Approvals "during" work (2.4, 11). In print mode neither CLI can pause for a human decision with the verified flags. | Approvals happen between executions. Each execution runs under a pre-approved permission envelope; anything outside it is denied by the provider, reported, turned into an approval request, and re-run or resumed if granted. See [ADR-0008](../architecture/decisions/ADR-0008-approvals-between-executions.md). |
| A5 | Nine agent avatars (9.2) versus "do not spawn a process per role" (3.4, 5.6). | A role is configuration. An execution is a provider process with exactly one acting role. Avatars reflect executions and task state; a role with no execution is shown idle. See [ADR-0004](../architecture/decisions/ADR-0004-agents-are-roles.md). |
| A6 | Agents must produce persistent artifacts, but only Claude has schema-validated output (`--json-schema`). | Authoring executions are read-only and return an artifact bundle as text. The engine validates it and is the only writer of `.ai-office/`. See [ADR-0005](../architecture/decisions/ADR-0005-engine-owned-artifact-writes.md). |
| A7 | "Docker Compose where beneficial" (12). Both CLIs authenticate with host credentials (keychain, OAuth), which a container cannot see. | The engine runs as a native local process. Docker is not used for the engine in v1. |
| A8 | "Desktop-oriented experience" (13). | A local web app served on `127.0.0.1` and opened in the browser. Confirmed by the user; no desktop shell. |
| A9 | Git worktrees are preferred (5.7), but a project may not be a git repository. | Git is required for parallel execution and for scope enforcement. On import of a non-git project the app offers `git init` (approval required). Without git a project runs sequentially with snapshot-based change detection. |
| A10 | "Model selection where supported" without assuming model availability. | The engine routes to tiers (`fast`, `standard`, `strong`). The user maps tiers to model names per provider; names are validated against what each CLI reports. No model name is hardcoded. |
| A11 | "Semantic search only where it provides measurable value" and no local LLM. | v1 uses SQLite FTS5 plus structural retrieval. Vector search is deferred until measured retrieval misses justify it. See [ADR-0010](../architecture/decisions/ADR-0010-pointer-first-context.md). |
| A12 | Provider fallback "where supported and explicitly configured". | Fallback is off by default and applies only to tasks routed with `auto`. A task pinned to a provider is blocked, never rerouted, when that provider is unavailable. |
| A13 | "Economical provider" when the two providers' costs are not comparable. | When one side's cost is unknown the router says so in its recorded rationale and falls back to configured preference, success rate, and duration. It does not invent a comparison. |

## 4. Principles derived from the brief

These follow from the cost rules (section 16) and shape every component:

1. **AI is used only where judgment is needed.** Running tests, git operations, indexing, impact analysis, context assembly, complexity classification, and delivery reports are engine code. See [ADR-0011](../architecture/decisions/ADR-0011-deterministic-work-stays-in-the-engine.md).
2. **The engine is the only writer of engineering knowledge.** Agents propose; the engine validates, versions, and records.
3. **Provider controls are a first line, not the boundary.** The engine verifies every execution's effects itself.
4. **Nothing is reported as measured unless it was measured.** This applies to cost, to acceptance criteria, and to avatar activity.

## 5. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| CLI output formats or flags change between versions | Adapter breaks silently | Capability detection per binary version; recorded-fixture contract tests; unknown events are preserved raw, never dropped |
| Cursor cost is unknown, so USD budgets under-count | Overspend not detected | Count and duration meters always enforced; user-configured accounting assumption, clearly labeled |
| An agent edits outside its declared scope | Conflicts, unreviewed changes | Worktree isolation, then a post-execution diff check against the declared write scope; violations are discarded or sent for approval |
| Process dies mid-execution | Lost work, unknown state | Detached runner with file-backed output; recovery never auto-restarts an execution that had write access |
| Artifact bundles fail validation | Wasted executions | Strict templates, one repair turn on the same session, then escalate to a human |
| The 3D office distorts the architecture | Fake activity, coupled state | The 3D scene only renders selectors over the shared store; it is built in Phase 8 |
| Ceremony for small changes costs more than the change | Poor cost efficiency | Workflow profiles scale the number of stages and executions to the change |
| Local server that can run commands is reachable by other local web pages | Remote code execution | Loopback bind, Origin check, per-session token. See [safety](../architecture/design/safety-and-governance.md) |

## 6. Scope

**Non-goals for v1:** additional providers, local model runtimes, vector search, multi-user or remote access, cloud sync, any platform other than macOS, production deployment automation beyond generating and running approved commands, a desktop shell.

**Minimum viable implementation (milestone M1, end of Phase 4):** create or import a project, write one task with acceptance criteria, execute it on a real CLI in a worktree, watch its events live, inspect the diff, approve the merge, and restart the app mid-run without losing state. Everything after M1 adds intelligence to a loop that already works end to end.

## 7. Coverage of the brief

| Brief section | Designed in |
|---------------|-------------|
| 2.1 SDD-first, 4 SDD engine | [SDD engine](../architecture/design/sdd-engine.md) |
| 2.2 Event-driven, 10 Observability | [Events, API, observability](../architecture/design/events-api-observability.md) |
| 2.3 Provider-agnostic, 7 Provider integration | [Provider integration](../architecture/design/provider-integration.md) |
| 2.4 Human-in-the-loop | [Orchestration, approvals](../architecture/design/orchestration-engine.md#5-approvals) |
| 2.5 Local-first, 12 Technical architecture | [System architecture](../architecture/system-design.md) |
| 3 Engineering organization | [Orchestration, roles](../architecture/design/orchestration-engine.md#1-agents-are-roles) |
| 5 Cost optimization, 16 Cost rules | [Cost and context](../architecture/design/cost-and-context.md) |
| 6 Orchestration engine | [Orchestration engine](../architecture/design/orchestration-engine.md), [domain model](../architecture/design/domain-model.md) |
| 8 Memory and context | [Cost and context](../architecture/design/cost-and-context.md#6-context-engineering) |
| 9 3D office, 13 User experience | [Frontend and 3D office](../architecture/design/frontend-and-3d-office.md) |
| 11 Safety and governance | [Safety and governance](../architecture/design/safety-and-governance.md) |
| 14 Roadmap, 15 Engineering rules, 17 Definition of success | [Roadmap](../plans/roadmap.md) |

## 8. Resolved questions

Answered by the user on 2026-11-21. Each answer is a product constraint in the [product requirements](product-requirements.md).

| # | Question | Answer | Effect on the design |
|---|----------|--------|----------------------|
| Q1 | Application shell | Browser-based local app | No desktop shell. [ADR-0012](../architecture/decisions/ADR-0012-local-web-app-3d-as-projection.md) stands as written (`CON-001`) |
| Q2 | Billing basis | Subscriptions for both Cursor and Claude Code, used through their CLIs with the user's login | Default billing basis is `subscription` for both. Dollar figures are notional. Budgets default to execution count, duration, and tokens. Claude `--bare` is not used, because it needs an API key (`CON-003`) |
| Q3 | Platforms | macOS only | Only macOS is built for and tested. Data lives in `~/Library/Application Support/`, secrets in the macOS Keychain (`CON-002`) |
| Q4 | Commits and merges | Commits are allowed. The engine has no permission to merge | The engine commits to branches it owns without asking. It never merges into the user's base branch, and never merges a pull request, on its own: that happens only by an explicit human decision for that specific merge, and no setting can change this (`CON-004`) |
| Q5 | How this platform itself is built | With SDD | This repository is the first SDD project. See [ADR-0013](../architecture/decisions/ADR-0013-bootstrap-with-sdd.md) (`CON-005`) |

## 9. Open questions

One item remains, and it does not block the foundation work: whether Claude Code's reported cost and its `--max-budget-usd` cap behave usefully under a subscription login. It is settled by the provider probe at the start of Phase 4.
