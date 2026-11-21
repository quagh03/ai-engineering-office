---
id: DN-0004
type: design-note
title: Provider integration
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
derives_from: [PRD, SYSTEM-DESIGN]
---

# Provider Integration

Two adapters, Cursor CLI and Claude Code CLI, behind one contract. The contract is designed so a third could be added without touching the engine, but none is implemented or planned.

Flags used here were verified against the installed binaries ([requirements, section 2](../../specifications/discovery-notes.md#2-verified-facts)). Each mapping marked *validate* is a design intent that must be confirmed by a recorded real run before the adapter is considered done.

## 1. Contract

```python
ProviderId = Literal["cursor", "claude-code"]

class AgentProvider(Protocol):
    id: ProviderId
    name: str

    async def check_health(self, *, deep: bool = False) -> ProviderHealth: ...
    async def get_capabilities(self) -> ProviderCapabilities: ...
    def build_invocation(self, request: ExecutionRequest) -> Invocation: ...
    def parse_event(self, line: str, state: ParseState) -> list[ExecutionEvent]: ...
    def finalize(self, exit: ExitRecord, state: ParseState) -> ExecutionOutcome: ...
    def cancel_plan(self) -> CancelPlan: ...
```

This differs from the brief's conceptual `execute()` / `cancel()` pair on purpose. The process is owned by the execution manager's detached runner, not by the adapter, so that executions survive an engine restart ([ADR-0006](../decisions/ADR-0006-detached-execution-runner.md)). The adapter is therefore pure translation: request to command line, output line to normalized events, exit to outcome, and which signals to send to cancel. The execution manager composes these into the streaming `execute` and `cancel` operations the engine calls. Pure adapters are also testable against recorded output with no process and no cost.

```python
@dataclass(frozen=True)
class ExecutionRequest:
    execution_id: str
    workspace: Path                       # worktree or project root
    prompt: str
    system_append: str | None             # compact role card
    permission_profile: PermissionProfile # read_only | workspace_write | elevated
    envelope: PermissionEnvelope          # allowed commands, write globs, denied reads
    model: str | None                     # resolved from tier by configuration
    effort: str | None
    timeout_s: int
    max_cost_usd: float | None            # hard cap, where the provider supports one
    resume_session_id: str | None
    output_schema: dict | None            # used only if the provider supports it

@dataclass(frozen=True)
class Invocation:
    argv: list[str]
    cwd: Path
    env: dict[str, str]                   # allowlisted
    stdin: str | None
    files: dict[Path, str]                # config the adapter needs written, e.g. permissions

@dataclass(frozen=True)
class ExecutionEvent:
    kind: EventKind
    provider: ProviderId
    data: dict                            # normalized fields
    raw: dict | None                      # the provider's original event, untouched
```

`EventKind`: `session_started`, `assistant_text`, `assistant_delta`, `tool_started`, `tool_completed`, `permission_denied`, `provider_retry`, `warning`, `result`, `unknown`.

Normalization never discards information: every event keeps the provider's original payload in `raw`, and anything unrecognized becomes `unknown` and is still stored. The execution inspector can show the raw stream.

```python
@dataclass(frozen=True)
class ExecutionOutcome:
    status: Literal["succeeded", "failed", "cancelled", "timed_out"]
    result_text: str | None
    session_id: str | None
    error: ProviderError | None           # class, message, retryable, raw
    usage: UsageReport                    # see section 6
    permission_denials: list[dict]
```

## 2. Capabilities

Capabilities are detected from the installed binary, not assumed from documentation, because the documentation can be ahead of the installed version. Detection runs `--version` and `--help`, checks for each flag the adapter may use, and caches the result by binary path and version.

| Capability | Cursor CLI | Claude Code CLI |
|------------|-----------|-----------------|
| Structured event stream | `--output-format stream-json` | `--output-format stream-json --verbose` |
| Partial text streaming | `--stream-partial-output` | `--include-partial-messages` |
| Model selection | `--model` | `--model`, `--effort` |
| List available models | `models` subcommand | Not available as a subcommand; aliases configured by the user |
| Session resume | `--resume <chatId>` | `--resume <id>`; `--session-id <uuid>` lets the engine choose the id |
| Read-only mode | `--mode ask` or `plan` | `--tools` restricted to read tools (*validate*) |
| Command and path rules | `permissions.allow` / `deny` in `.cursor/cli.json` | `--allowedTools`, `--disallowedTools` |
| Sandbox toggle | `--sandbox enabled` | Not used |
| Hard cost cap | None | `--max-budget-usd` |
| Schema-validated output | None | `--json-schema` |
| Reported cost | Not documented | `total_cost_usd` (client-side estimate) |
| Reported tokens | Not documented | Reported in the result (*validate field names*) |
| Workspace selection | `--workspace <path>` | Process working directory; `--add-dir` for extras |

The engine reads this table as data. Routing can require a capability (for example, a hard cost cap for an unattended critical task), and the UI shows exactly what each provider can and cannot report.

## 3. Discovery and health

| Step | Cursor CLI | Claude Code CLI |
|------|-----------|-----------------|
| Locate | Configured path, else `cursor-agent`, else `agent` on `PATH` | Configured path, else `claude` on `PATH` |
| Identify | `--version`; `about --format json` confirms it is the Cursor CLI, since `agent` is a generic name | `--version` |
| Authentication | `status --format json`, read `isAuthenticated` | `auth status --json`, read `loggedIn` and `authMethod` |
| Models | `models` | - |

- Health is decided from the JSON body, not the exit code: the two CLIs disagree (Cursor exits `0` when unauthenticated, Claude exits `1`).
- These checks are free. An end-to-end check that actually calls the model costs usage, so it runs only as an explicit "deep check" the user triggers.
- Health is cached briefly and refreshed before an execution if stale. A failing provider emits `ProviderHealthChanged`, and tasks routed to it are blocked with that reason.
- Health reflects the environment the engine runs in. A CLI that is logged in for the user can still report unauthenticated to a process that cannot reach the user's keychain; the health panel shows the CLI's own message to make this diagnosable.

## 4. Invocation mapping

### Cursor CLI

```text
cursor-agent -p --output-format stream-json [--stream-partial-output]
             --workspace <worktree> --trust
             [--model <model>] [--mode ask] [--sandbox enabled] [--resume <chatId>]
             "<prompt>"
```

- The prompt is the positional argument. The context service keeps packages far below argument-length limits; the adapter rejects a prompt that exceeds a safe size rather than truncating it.
- Read-only executions use `--mode ask`.
- Write executions run without `--force`. In print mode Cursor already edits workspace files and rejects anything that would need approval. The adapter writes the envelope as `permissions.allow` / `deny` into the worktree's `.cursor/cli.json`. If the project tracks its own file, the adapter merges into it without weakening any existing deny rule, and the generated change is excluded from the task's change set.
- `--force` is used only for an execution whose `elevated` profile was approved by a human. Deny rules still apply.

### Claude Code CLI

```text
claude -p --output-format stream-json --verbose [--include-partial-messages]
       --session-id <uuid> | --resume <id>
       [--model <model>] [--effort <level>]
       [--append-system-prompt "<role card>"]
       [--tools "Read,Glob,Grep"]                      # read-only
       [--permission-mode acceptEdits]                 # write
       [--allowedTools "<rules>"] [--disallowedTools "<rules>"]
       [--max-budget-usd <amount>] [--json-schema '<schema>']
```

- The prompt is sent on stdin; the working directory is the worktree.
- `--max-budget-usd` is set to the smallest remaining applicable USD budget, giving a cap enforced inside the run.
- `--dangerously-skip-permissions` and `bypassPermissions` are never used.
- **Ambient configuration.** Without `--bare`, a `-p` run loads the user's hooks, plugins, MCP servers, and `CLAUDE.md`, which costs tokens and can run code the engine did not choose. `--bare` avoids that but works only with API-key authentication. The expected deployment is a subscription login, so the default path does not use `--bare`: it limits what loads with `--setting-sources` and `--strict-mcp-config` (*validate*). `--bare` is used only if the detected `authMethod` is an API key.
- **Subscription login.** Whether `total_cost_usd` and `--max-budget-usd` behave usefully under a subscription login is not yet verified (*validate*). Until it is, the in-run cap is treated as best effort and the engine's own duration and count limits are the ones relied on.

### Permission profiles

| Profile | Used for | Cursor | Claude Code |
|---------|----------|--------|-------------|
| `read_only` | Authoring, review | `--mode ask` | `--tools` limited to read tools |
| `workspace_write` | Implementation | Default print mode, envelope in `cli.json`, sandbox enabled | `acceptEdits`, envelope as allow and deny rules |
| `elevated` | Human-approved exceptions | As above plus `--force` | As above with widened allow rules |

These flags are the first line of control only. The engine independently enforces the envelope afterwards ([safety](safety-and-governance.md#3-permission-envelopes)).

## 5. Event normalization

| Normalized | Cursor source | Claude Code source |
|------------|---------------|--------------------|
| `session_started` | `system` / `init` (model, session id, permission mode) | `system` / `init` (model, tools, MCP servers, session id) |
| `assistant_text` | `assistant` (complete message) | `assistant` message |
| `assistant_delta` | `assistant` with `timestamp_ms` and no `model_call_id`; the two duplicate flush forms are skipped | `stream_event` text deltas |
| `tool_started` / `tool_completed` | `tool_call` `started` / `completed`, matched by `call_id` | `tool_use` and `tool_result` blocks |
| `permission_denied` | Rejected tool result (*validate shape*) | `permission_denied` system message; `permission_denials` in the result |
| `provider_retry` | - | `system` / `api_retry` (attempt, delay, error category) |
| `result` | `result` (durations, text, session id, request id) | `result` (text, cost, usage, session id) |

Tool events are reduced to a compact common form (tool class: `read`, `write`, `shell`, `search`, `other`; target path or command) for the event log and the 3D office. File contents in tool payloads are kept in the execution's raw output file, not copied into the database.

Cursor suppresses thinking events in print mode. The engine therefore derives "agent is thinking" for both providers from real stream state (a session is running and the model is producing output with no tool call open). It is never synthesized on a timer.

## 6. Usage reporting

```python
@dataclass(frozen=True)
class UsageReport:
    measurement: Literal["provider_reported", "estimated", "unknown"]
    amount_usd: float | None
    input_tokens: int | None
    output_tokens: int | None
    cache_read_tokens: int | None
    cache_write_tokens: int | None
    duration_ms: int
    api_duration_ms: int | None
    cumulative: bool          # True if the provider reports a session-wide total
    raw: dict
```

- **Claude Code** reports cost and tokens. Its cost is the conversation total when a session is resumed, so the adapter sets `cumulative` and the cost service subtracts what was already recorded for that session.
- **Cursor** reports durations. Cost and tokens are `None` and the measurement is `unknown` unless the installed version emits usage fields, in which case they are captured as found.
- The adapter reports only what the provider said. Turning tokens into an estimated amount is the cost service's job, using prices the user configured.

## 7. Errors

Failures are classified into one normalized class with the raw evidence attached.

| Class | Retryable | Recognized from |
|-------|-----------|-----------------|
| `auth` | No | Health check; Claude retry category `authentication_failed`; stderr |
| `rate_limit`, `overloaded`, `network` | Yes, with backoff | Claude retry categories; stderr patterns |
| `billing` | No | Claude `billing_error`, `account_on_hold` |
| `budget_cap` | No (needs approval) | Claude run stopped at `--max-budget-usd` |
| `model_unavailable`, `invalid_request` | No | Claude categories; non-zero exit before the run starts |
| `permission_denied` | After approval | Denials in the stream or result |
| `timeout` | Once | Runner's exit record |
| `cancelled` | No | Runner's exit record; Claude exit `143` after SIGTERM |
| `output_contract` | Once, as a repair turn | Engine validation of the result |
| `task_failure` | By policy | Agent's completion report says it could not finish |
| `unknown` | No | Anything else; stderr preserved |

Cursor reports failure as a non-zero exit and a stderr message with no terminal event, so its classification relies on message patterns and falls back to `unknown` more often. An `unknown` failure is surfaced to the user rather than retried blindly.

## 8. Cancellation and timeout

The runner owns the CLI's process group. Cancellation follows the adapter's `CancelPlan`: an interrupt signal, a grace period, a terminate signal, a second grace period, then a kill. For Claude Code, SIGINT lets the turn end cleanly before SIGTERM. Cursor's signal behavior is undocumented and is one of the things the first recorded runs establish. Timeouts are enforced by the runner itself, so a run is bounded even if the engine is not running.

## 9. Testing the adapters

| Level | What runs | Cost |
|-------|-----------|------|
| Fixture replay | Recorded NDJSON from real runs, per CLI version, through `parse_event` and `finalize` | None; runs in CI |
| Invocation snapshot | `build_invocation` output for each profile, compared to approved snapshots | None |
| Live contract | A small real task per provider: start, stream, cancel, timeout, resume, denied action | Real usage; opt-in, never automatic |

A script that replays recorded output stands in for the CLIs in engine integration tests. It exists only in the test suite. No product code path substitutes simulated output for a real provider.
