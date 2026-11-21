---
id: DN-0008
type: design-note
title: Safety and execution governance
version: 1
status: in_review
derives_from: [PRD, SYSTEM-DESIGN]
---

# Safety and Execution Governance

The platform runs coding agents and shell commands on the user's machine. The governing rule is that **the engine enforces its own policy and verifies results itself**; provider permission flags reduce risk but are not trusted as the boundary.

## 1. Layers

| Layer | Control | Enforced by |
|-------|---------|-------------|
| 1 | Local API is reachable only by the application's own UI | Engine |
| 2 | Work happens inside the project boundary, in an isolated worktree | Engine |
| 3 | Each execution has a permission envelope built from role, task, and approvals | Engine, translated to provider flags |
| 4 | Provider-side restrictions (modes, allow and deny rules, sandbox) | Provider CLI |
| 5 | After the run: the diff is checked against the declared write scope | Engine |
| 6 | Nothing reaches the user's branch without approval | Engine |
| 7 | Every decision and command is recorded | Engine |

Layers 2, 5, and 6 hold even if a provider ignores its restrictions entirely: the agent works in a separate checkout, anything it changed outside its scope is detected, and its changes cannot merge unseen.

**Limit of this design.** Layer 5 detects changes inside the worktree. It cannot detect what a shell command did elsewhere on the machine. That exposure is reduced by layers 3 and 4 (shell commands are allowlisted, the provider sandbox is enabled where available) but not eliminated. This is stated in the UI where permissions are configured.

## 2. Workspace boundary

- A project's `root_path` is its boundary. Every path the engine handles is resolved (symlinks included) and must fall inside the project root, the task's worktree, or the engine's data directory.
- Worktrees live in the engine's data directory, one per task.
- Protected paths are denied to agents regardless of scope: `.git/` internals, `.ai-office/` (engine-written only), CI secrets and credential files, and any path the project marks protected.
- Additional directories are never granted to a provider without an approval.

## 3. Permission envelopes

An envelope is the complete statement of what one execution may do.

```yaml
profile: workspace_write
write_globs: ["src/auth/**", "tests/auth/**"]
read_deny: [".env*", "**/*.pem", "**/secrets/**"]
commands_allow: ["test", "lint", "typecheck"]      # named commands from project.yaml
commands_deny: ["git push", "git commit", "rm -rf", "curl", "npm install", "pip install"]
network: deny
timeout_s: 1200
max_output_bytes: 20000000
```

- **Built only by the engine** from the role definition, the task's declared scope, project policy, and recorded approvals. Nothing an agent outputs can change it.
- **Widening requires an approval** that records what was added, for which execution, and by whom. The widening applies to that task only and does not persist to later tasks.
- Stored on the execution record, so what an execution was permitted to do is always auditable.

Application-level policy is enforced independently of what the provider did with its flags:

| Policy | Engine enforcement |
|--------|--------------------|
| Write scope | Post-run diff; out-of-scope changes are discarded or sent for approval |
| Protected paths | Post-run diff; a change there fails the execution |
| No agent git writes | Engine makes all commits and merges; an unexpected commit on the task branch is a violation |
| Dependency installation | Lockfile and manifest changes are detected in the diff and require approval before the task can proceed |
| Destructive file operations | Deletions in the diff beyond a threshold, or outside scope, require approval |
| Time and output limits | Runner enforces both |

## 4. Secrets

- The engine holds almost no credentials: both CLIs manage their own authentication. If the user supplies an API key, it is stored in the macOS Keychain and passed only to the process that needs it. It is never written to the database, to YAML, or to a log.
- **Environment allowlist.** Provider and command processes receive a minimal environment (path, home, locale, and the variables each CLI needs to authenticate), not the engine's full environment.
- **Not in prompts.** Context packages are built from artifacts, pointers, and code structure. Files matching secret patterns are excluded from the index and from context, and are denied for reading in the envelope.
- **Redaction.** Output is scanned for credential patterns and for the values of known secrets before it is written to events, logs, summaries, or sent to the UI. The raw output file is stored with user-only permissions.

## 5. Commands the engine runs

Tests, linters, builds, and git are run by the engine, not by an AI session.

- Commands are **named and declared** in `project.yaml` (`test`, `lint`, `typecheck`, `build`, and so on). The engine runs only declared commands; agents and artifacts refer to them by name.
- Each run has a working directory inside the boundary, the environment allowlist, a timeout, and an output cap.
- A command proposed by an agent that is not declared (for example, a migration or a deployment step) becomes an approval request showing the exact command line. Approving it can optionally add it to the project's declared commands.
- Deployment commands always require approval.

## 6. Local API protection

A local server that can start agents and run commands must not be drivable by another website open in the user's browser.

- Binds to `127.0.0.1` only. There is no option to bind to other interfaces in v1.
- Checks the `Host` and `Origin` headers on every request and WebSocket upgrade, which defeats cross-site requests and DNS rebinding.
- Requires a per-installation token, delivered to the UI at launch and never placed in a URL that is logged.
- No permissive CORS.

## 7. Human approval

Kinds, defaults, and flow are in [orchestration](orchestration-engine.md#5-approvals). Properties that matter for safety:

- A request shows the exact action (command line, files, diff, cost) and the snapshot is what gets recorded.
- Approvals are specific and expire. Approving one dependency installation does not approve the next.
- A rejected or expired approval never falls through to execution.
- Policies can be made stricter per project. Loosening a default (for example, auto-approving plans) is an explicit setting, itself recorded in the audit log.
- Merging into the user's base branch, merging a pull request, and pushing to a remote can never be loosened. They always need an explicit human decision for that specific action.

## 8. Recovery safety

- An interrupted execution that had write access is never restarted automatically. The engine inspects the worktree and asks ([orchestration](orchestration-engine.md#7-persistence-and-recovery)).
- Git operations are checked for incomplete state (merge or rebase in progress, lock files) on startup and reported, not auto-resolved.
- Worktrees are never deleted automatically while they contain changes that were not committed to a task branch.

## 9. Resource limits

Configurable limits on concurrent executions (global and per provider), execution duration, output size, events per second from a single execution, worktree count, and disk use by execution output. Reaching a limit defers work and emits an event; it does not fail silently.

## 10. Audit

The `audit_log` records, with actor and outcome: approvals and their snapshots, envelope creation and widening, policy violations, every command the engine ran, configuration and policy changes, budget changes, memory acceptance, and recovery decisions. It is append-only and viewable in the UI. Together with the event log and context manifests it answers who allowed what, what an agent was told, and what it actually did.
