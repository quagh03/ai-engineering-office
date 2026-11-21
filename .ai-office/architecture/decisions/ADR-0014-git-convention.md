---
id: ADR-0014
type: adr
title: Git branching and commit convention
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:19:08Z
derives_from: [PRD#CON-004, CONSTITUTION#C-040, ADR-0007, ADR-0013]
---

# ADR-0014: Git branching and commit convention

## Context

This repository is built under SDD with AI sessions and a human owner. Commits are allowed; merging into the base branch, merging pull requests, and pushing are human-only ([CON-004](../../specifications/product-requirements.md), [C-040](../../constitution.md)). The product will later manage git for customer projects ([ADR-0007](ADR-0007-engine-managed-worktrees.md)). Without a shared convention, branch names, commit messages, and PR bodies will not carry task and requirement identity, and AI sessions will not know what they may do.

The base branch is already `develop` (see `.ai-office/project.yaml`).

## Decision

1. Adopt the [git convention](../design/git-convention.md) for this repository immediately (bootstrap), and as the default the engine applies to managed projects later.
2. Keep the human-only gates unchanged: merge to base, merge of a pull request, and push require an explicit user decision for that action.
3. AI sessions may commit on working branches and may open a pull request when asked. They never merge, never push, never force-push, never rewrite published history, and never commit directly to `develop` unless the user explicitly asks for that specific commit on `develop`.
4. Every implementation commit references its task. Every task branch name contains its task id. Pull requests are one task unless the user directs otherwise.

## Rationale

- Traceability from commit → task → specification item matches the SDD graph the product is built on.
- A single convention for this repo and for managed projects means the engine will not invent a second workflow later.
- Forbidding AI merges and pushes encodes CON-004 in daily practice, not only in policy text.
- Conventional-commit types stay readable to humans and tooling; SDD ids in the scope and footer keep the audit trail.

## Consequences

- Constitution gains binding git clauses (proposed as constitution v2).
- `AGENTS.md` and `project.yaml` point at the convention.
- Approval of artifact-only changes still needs a commit; that commit follows the `docs` / `chore` rules and lands on `develop` only by the user's merge or explicit request.
- Commit-message and branch checks can be added as optional tooling later (candidate for TASK-0009 or a small follow-up task). They are not required to accept this ADR.
- ADR-0007's engine-owned names (`aio/<feature>/<task>`) remain the product's internal branch scheme; this convention's `task/` and `feat/` names are for human and bootstrap work on a repository's main checkout. Managed worktrees continue to use `aio/...`.

## Alternatives rejected

- Trunk-only commits on `develop` with no task branches: loses isolation and makes review of AI work harder.
- Strict GitFlow (`main` + `develop` + release branches): extra ceremony for a single-maintainer local product.
- Free-form commit messages with task ids only in the PR: history becomes useless when browsing `git log` on a branch.
