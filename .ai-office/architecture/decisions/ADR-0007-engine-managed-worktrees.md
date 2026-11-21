---
id: ADR-0007
type: adr
title: The engine manages git worktrees and all git writes
version: 1
status: in_review
derives_from: [SYSTEM-DESIGN]
---

# ADR-0007: The engine manages git worktrees and all git writes

## Context

Parallel tasks need isolated workspaces, and the engine must be able to see exactly what each execution changed. Both CLIs have their own worktree flag, but they place worktrees in different locations and behave differently.

## Decision

The engine creates one worktree and one branch per task with plain git, under its own data directory, and passes that directory to the provider as the workspace. The engine performs every git write: checkpoint commits on task branches, merges into the feature's integration branch, and the final merge into the user's base branch. Agents are denied git write commands. The CLIs' own worktree flags are not used.

## Rationale

- Identical behavior on both providers, and worktree lifecycle that the engine can recover after a restart.
- The diff of a worktree against its base is the engine's own evidence of what an execution changed, which is what scope enforcement and code traceability are built on.
- Keeping commits and merges in the engine puts them behind approval policy and gives consistent, attributable history.

## Consequences

- Git is required for parallel execution and for diff-based scope enforcement. A non-git project is offered `git init` on import; without it, it runs sequentially with snapshot-based change detection.
- The engine commits and integrates freely on branches it owns (task branches and the feature's integration branch). It has no permission to merge into the user's base branch or to merge a pull request: that happens only by an explicit human decision for that specific merge, and no policy setting can remove the requirement. The engine also never pushes to a remote without approval.
- Merge conflicts at integration are surfaced as blocked tasks, never auto-resolved.
- Dependencies installed per worktree (for example `node_modules`) cost time and disk; a project can declare a worktree setup command, and very short tasks are not parallelized.

## Alternatives rejected

- The CLIs' worktree flags: divergent locations and semantics, outside the engine's control.
- Working directly in the user's checkout: no isolation, and the user's uncommitted work would be mixed with agent changes.
- Copying the project per task: slow and has no merge story.
