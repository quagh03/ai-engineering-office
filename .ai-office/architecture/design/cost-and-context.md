---
id: DN-0005
type: design-note
title: Cost optimization, context, and memory
version: 1
status: in_review
derives_from: [PRD, SYSTEM-DESIGN]
---

# Cost Optimization, Context, and Memory

The objective is the brief's: the required engineering quality at the lowest reasonable cost, with no redundant work. This document covers how that is decided before an execution (classification, routing, budgets, context), controlled during it (caps, timeouts), and measured after it (cost records, analytics).

## 1. The three questions

Every execution request passes through a gate that records its answers. The gate can refuse.

| Question | How it is answered | Recorded as |
|----------|--------------------|-------------|
| Is this AI execution necessary? | Is the work deterministic (then the engine does it)? Is there a valid cached result? Is there already a stored answer? | `ExecutionAvoided` with the reason, or the request proceeds |
| What is the minimum context and capability needed? | Task category sets the tier floor; the context builder works within the role's token budget | Context manifest, routing rationale |
| What is the cheapest reliable way to complete and verify it? | Routing by expected cost including the risk of rework; verification by targeted checks with result reuse | `ProviderSelected`, verification plan |

`ExecutionAvoided` events are how the platform measures savings instead of claiming them: each one records what would have run.

## 2. Routing

### Classification

A task's category is decided by rules over data the plan already contains, with no AI call of its own:

| Signal | Source |
|--------|--------|
| Number and spread of files in the write scope | Plan |
| Touches contracts, schemas, migrations, auth, or security-tagged paths | Plan, project configuration |
| Number of linked acceptance criteria and dependencies | Trace graph |
| Role and kind of work | Plan |
| Planner's own complexity estimate | Planning output (part of the planning execution, not a separate call) |
| History of similar tasks in this project | Execution records |

Output: `simple`, `routine`, `complex`, or `critical`, plus a flag for whether the task is eligible for parallel execution. The user can override the category on any task; the rules and their result are shown.

### Tiers, not model names

The router chooses a provider and a tier: `fast`, `standard`, or `strong`. The user maps tiers to model names per provider in configuration, and the mapping is validated against what the CLI reports where it can list models. The design hardcodes no model name, because availability differs per account and changes over time.

### Selection

1. **Constraints first.** A pinned provider is used as-is. Otherwise candidates are filtered by health, required capabilities, role preference, and category preference.
2. **Tier floor.** `simple -> fast`, `routine -> standard`, `complex -> standard`, `critical -> strong`. The execution policy shifts this: `economy` uses the floor, `balanced` raises the floor one step for complex work, `quality_first` raises it for routine work as well.
3. **Expected cost.** For each candidate: `estimated cost / probability of success + rework penalty`. Probability comes from the smoothed success rate for the same provider, tier, role, and category in this project. This is what stops the router from picking a weaker option that is cheaper per attempt but more expensive per completed task.
4. **Choose** the lowest expected cost that fits the remaining budget.
5. **Record** the decision in `ProviderSelected` with every candidate, its score, and the reason.

When one provider's cost is unknown, candidates cannot be compared on cost. The router then says so in the rationale and decides on configured preference, success rate, and expected duration.

Fallback applies only to `auto`-routed tasks, only if enabled, and only for errors that are about the provider rather than the task (unavailable, rate limited). A fallback is its own recorded decision.

## 3. Cost measurement

Three levels, shown everywhere a figure appears ([ADR-0009](../decisions/ADR-0009-cost-measurement-and-budget-meters.md)):

| Level | Meaning | Example |
|-------|---------|---------|
| `provider_reported` | The provider stated a cost for this run | Claude Code `total_cost_usd` |
| `estimated` | Computed by the engine from reported usage and user-configured prices or rates | Tokens multiplied by a configured price table |
| `unknown` | No reliable basis | Cursor run with no usage data and no accounting assumption |

Each record also carries a **billing basis**, set per provider by the user:

- `metered`: usage is paid per unit. The amount approximates real marginal spend.
- `subscription` (the default for both providers): usage draws on a plan. The amount is notional. The user may enter a rate (per execution, per minute, or per million tokens) to make subscription usage comparable; it is always labeled as their assumption. Subscription usage is never treated as free.

Rules:

- A total that includes an `unknown` execution is shown as "at least" with the count of unmeasured executions beside it.
- Estimated and reported amounts are never summed into a figure labeled as reported.
- For resumed Claude sessions the recorded amount is the difference from the session's previous total.
- Price tables and rates are configuration with an effective date, so historical records keep the assumption they were computed with.

## 4. Budgets

A budget is a limit on one meter for one scope.

| Dimension | Values |
|-----------|--------|
| Scope | Execution, task, feature, project, day, month |
| Meter | `usd`, `tokens`, `executions`, `duration_s` |
| Thresholds | Default 70 %, 85 %, 100 %; configurable |
| On exceed | `ask` (default), `pause`, `stop` |

Count and duration meters exist because they are always measurable. A project whose provider reports no cost is still bounded. Because the default billing basis is `subscription`, a new project's default budgets are set on executions, duration, and tokens; a `usd` budget is opt-in and is labeled notional.

**Reservation.** Before an execution starts, its estimate is reserved against every budget that applies; consumption is settled amounts plus reservations. This prevents several parallel executions from each passing a check and jointly overshooting. On completion the reservation is replaced by the actual amount.

**Thresholds.**

| At | Event | Action |
|----|-------|--------|
| 70 % | `BudgetWarning` | Notify |
| 85 % | `BudgetReassessment` | The engine recomputes the remaining plan's estimate against what is left and proposes options: switch remaining work to `economy`, drop optional tasks, reduce review depth for non-critical tasks, or raise the budget. Rule-based; no AI call |
| 100 % | `BudgetExceeded` | Nothing new starts in that scope. Affected tasks move to `NEEDS_APPROVAL` with an authorization request, or follow the configured policy |

**During a run.** Claude Code runs carry `--max-budget-usd`. Cursor has no equivalent, so its runs are bounded by timeout only; the UI shows which kind of cap applies to each execution.

**Unknown cost.** A `usd` budget cannot see executions with unknown cost. The project setting `unknown_cost_policy` decides what happens: `warn` (default; the budget view states how many executions it could not measure), `assume` (apply the user's rate), or `block` (do not run unmeasurable executions against a USD budget).

## 5. Estimation

Estimates are produced per task at planning time and refined before execution.

1. With enough history: the median actual of comparable executions (same role, category, provider, tier) in this project.
2. Otherwise: configurable priors per category, labeled as priors.

Every estimate carries its basis and sample size. The cost dashboard reports estimate against actual so the user can see how far to trust it.

## 6. Context engineering

An agent receives a context package built for its task and nothing else. Conversation history is not a context source.

### Pointer-first packages

Both CLIs can read files themselves. Inlining file contents pays for tokens the agent may not need and goes stale. The package therefore inlines only what must be authoritative and compact, and points at the rest ([ADR-0010](../decisions/ADR-0010-pointer-first-context.md)):

| Section | Content | Form |
|---------|---------|------|
| Role card | Who the agent is acting as, in a few lines | Inline, versioned, stable |
| Objective and deliverable | The task, the expected output, the output format | Inline |
| Acceptance criteria | The linked criteria, verbatim from the approved revision, with keys | Inline |
| Constraints | Relevant constitution clauses; one-paragraph summaries of relevant ADRs | Inline, with a path to the full text |
| Files | Paths, why each matters, symbol names and line ranges | Pointers |
| Interfaces | Signatures the task must conform to | Inline excerpts |
| Prior attempts | A digest of previous failures on this task | Inline, short |
| Assumptions | Anything not from an approved artifact | Inline, labeled |

### Build steps

1. Read the task objective, role, and write scope.
2. Follow trace links to the approved specification items and ADRs.
3. Collect candidate files: the write scope, files referenced by linked items, then their importers and imports from the file index.
4. Rank candidates by link distance and keyword match (FTS5); add symbols and line ranges when the symbol index is available.
5. Add prior-attempt digests and relevant memory entries.
6. Fit to the role's token budget by dropping the lowest-ranked pointers first. Criteria and constraints are never dropped; if they alone exceed the budget, the task is too large and is returned to planning.
7. Write the **context manifest**.

### Manifest and provenance

The manifest lists every item given to the agent: its reference, revision or content hash, provenance, the reason it was included, and its estimated size.

Provenance is one of `approved` (an approved artifact revision), `draft`, `derived` (computed by the engine, such as an index or summary), `memory`, or `assumption`. It is printed in the package itself, so an agent can tell an approved requirement from a working assumption, and it is stored, so a reviewer can see exactly what an agent knew.

Token sizes are estimated from character counts and labeled as estimates; where the provider reports actual input tokens, the difference is recorded and used to calibrate.

### Incremental context

A follow-up on the same task (a repair turn, changes requested, an answered question) resumes the provider session and sends only what changed: the new information and the diff since the last turn. If the manifest fingerprint is unchanged, the rendered package is reused.

### Retrieval

Structured links first, keywords second, structure third. No embeddings and no model in the retrieval path. Retrieval quality is measured (did the agent open files that were not in the package; did it miss a file it later needed) and that data decides whether vector search is ever worth adding.

## 7. Prompts

- One versioned template per role and execution kind, stored as files: `resources/prompts/<role>/<kind>@<version>.md`. Projects can override them.
- A prompt is the role card plus the context package plus the output contract. The organization chart and other roles' duties are not included.
- The stable part (role card, output contract) comes first and the task-specific part last, so any provider-side caching can apply. The design does not depend on such caching and reports no savings from it unless the provider reports cached tokens.
- The template id and version are recorded on each execution, so outcomes can be compared across template versions.

### Output contracts

| Execution kind | Output | Validation |
|----------------|--------|------------|
| Authoring | An artifact bundle: one or more documents with front matter, separated by a fixed marker | Front matter schema, required sections, item keys, trace links |
| Implementation | Changes in the worktree plus a completion report (status, criteria addressed, files changed, commands run, blockers, permissions needed, memory proposals) | Report schema; the claims are checked against the actual diff and gate results |
| Review | A review report: findings with severity, location, and the criterion or ADR concerned | Schema |

Where the provider supports schema-validated output, the adapter uses it for the report. Otherwise the report is a fenced block parsed strictly. A failed validation gets one repair turn on the same session listing the specific errors.

## 8. Memory

| Layer | Content | Stored as |
|-------|---------|-----------|
| Project | Overview, stack, conventions, architecture summary, constraints | Artifacts in `memory/` plus entries |
| Feature | Specifications, decisions, history, related tasks | Trace graph and feature entries |
| Task | Objective, relevant files, previous attempts, results | Task records, execution summaries |
| Agent | Lessons and outcomes per role | Entries keyed by role |

- **Project analysis is done once** and refreshed incrementally by file hash. An agent is not asked to rediscover the stack or layout.
- Agents propose memory in their completion reports. The engine records each proposal with its source execution. Low-risk kinds (lessons, file notes) can be auto-accepted by policy; conventions and constraints require approval.
- Memory never overrides an approved artifact. An entry that contradicts one is flagged as a conflict for the user. Entries are superseded, not edited, so the history is auditable.
- Entries are tied to the content hashes they describe and are marked stale when those files change.

## 9. Caching and reuse

| Result | Fingerprint inputs |
|--------|--------------------|
| Project and dependency analysis | Manifest and lockfile hashes, file index hash |
| File and symbol index | Per-file content hash |
| Architecture summaries | Approved revision hashes of the source artifacts |
| Context packages | Manifest fingerprint |
| Test results | Command, tree hash of the worktree, lockfile hash, relevant configuration |
| Static analysis results | Tool version, configuration hash, hashes of the files analyzed |
| Approved specifications | Revision content hash |

A cached value is used only when its fingerprint matches exactly; any difference is a miss. Reused test results are recorded as reused, with a link to the run they came from, and are shown that way. Test reuse starts conservatively (any change to the tree invalidates) and is narrowed to per-target dependencies only once the dependency index is proven accurate.

## 10. Retries

| Rule | Mechanism |
|------|-----------|
| Classify before retrying | The error class decides whether a retry is allowed at all ([provider errors](provider-integration.md#7-errors)) |
| Bounded | Per-class limits; default two attempts for transient errors, one for task failures |
| No identical retries | Each failure gets a signature (class, normalized message, failing checks). A second failure with the same signature under the same configuration stops retrying |
| Keep failure context | The next attempt receives a digest of what failed |
| Do not repeat finished work | Retries resume the session or start from the task branch's last checkpoint; passed checks with unchanged inputs are reused |
| Escalate only when justified | After the same-tier retry fails, one step up in tier is allowed if policy permits and the budget covers it |
| Budget authorization | A retry that would exceed a budget becomes an approval request |
| Separate accounting | Retries are separate executions flagged `is_retry` |

## 11. Analytics

All views are queries over `cost_records`, `executions`, and `tasks`, each figure labeled with its measurement level.

| View | Definition |
|------|------------|
| Estimated versus actual | Per task and feature, with the estimate's basis |
| Cost per task, feature, project | Sum of execution records in scope |
| Cost per provider and per role | Grouped sums |
| Token usage | Where reported; coverage shown as "N of M executions reported tokens" |
| Average execution duration | By role, category, provider |
| Retry cost | Records flagged `is_retry` |
| Cost of failed executions | Records where the execution did not succeed |
| Cost per successfully completed task | Total cost in scope divided by completed tasks |
| Avoided executions | Count and kind of `ExecutionAvoided`, and reused verification runs |

A cost report per feature is written to `.ai-office/cost-reports/` at delivery.
