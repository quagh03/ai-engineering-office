---
id: DN-0009
type: design-note
title: Git convention
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:19:08Z
derives_from: [ADR-0014]
---

# Git convention

How git is used in this repository today, and the default the product will apply to managed projects later. Binding decisions are in [ADR-0014](../decisions/ADR-0014-git-convention.md). Human-only gates are [CON-004](../../specifications/product-requirements.md) and [C-040](../../constitution.md).

## 1. Two layers

| Layer | Who | Branch namespace | Purpose |
|-------|-----|-----------------|---------|
| Repository checkout | Human and AI sessions building this project (bootstrap) | `develop`, `feat/`, `task/`, `fix/`, `docs/` | Day-to-day work on the main clone |
| Engine-managed worktrees | The product, once FEAT-0004 exists | `aio/<feature>/<task>` | Isolated provider executions ([ADR-0007](../decisions/ADR-0007-engine-managed-worktrees.md)) |

This document specifies the repository-checkout layer. The engine layer stays as ADR-0007.

## 2. Base branch

- The base branch is **`develop`**.
- Nothing is merged into `develop`, no pull request is merged, and nothing is pushed to a remote without an explicit decision from the user for that specific action.
- `main` is not used. If a remote default named `main` appears, it is not the base branch for this project.

## 3. Branch names

| Kind | Pattern | Example | Used for |
|------|---------|---------|----------|
| Base | `develop` | `develop` | Integration line |
| Feature | `feat/FEAT-NNNN-<slug>` | `feat/FEAT-0001-foundation` | Optional long-lived branch for a multi-task feature |
| Task | `task/TASK-NNNN-<slug>` | `task/TASK-0001-backend-skeleton` | Default: one branch per task |
| Docs / artifacts | `docs/<slug>` | `docs/git-convention` | Artifact-only changes that are not a numbered task |
| Fix | `fix/<slug>` | `fix/health-port-message` | Hotfix not tied to a new task id (still needs a task before code, unless artifact-only) |

Rules:

- Branch from the latest `develop` unless the user says otherwise.
- Prefer **one branch per task**. Use a feature branch only when several tasks must integrate before merging to `develop`.
- Slugs are lowercase kebab-case, short, and stable; do not rename a branch after a pull request exists.
- AI sessions create a `task/...` branch before implementation commits, unless the user explicitly asks to commit on `develop`.

## 4. Permissions by actor

| Action | User | AI session |
|--------|------|------------|
| Create working branch | Yes | Yes |
| Commit on working branch | Yes | Yes |
| Commit on `develop` | Yes | Only when the user explicitly asks for that specific commit on `develop` |
| Open a pull request | Yes | When the user asks |
| Merge into `develop` | Yes (explicit) | Never |
| Merge a pull request | Yes (explicit) | Never |
| Push to remote | Yes (explicit) | Never |
| Force-push / history rewrite | User only, and never on `develop` | Never |
| Tag a release | Yes (explicit) | Never |

## 5. Commits

### Format

[Conventional Commits](https://www.conventionalcommits.org/) with an SDD trailer block:

```text
<type>(<scope>): <summary>

<optional body>

Implements: <item>[, <item>...]
Verifies: <item>[, <item>...]
Refs: <TASK-NNNN>[, <FEAT-NNNN>]
```

- **Summary:** imperative, ≤72 characters, no trailing period.
- **Body:** what changed and why, when the summary is not enough.
- **Trailers:** required on implementation commits. Artifact-only commits may omit `Implements` / `Verifies` and use `Refs` alone.

### Types

| Type | Use |
|------|-----|
| `feat` | User-visible or API behaviour for a task |
| `fix` | Bug fix |
| `test` | Tests only |
| `refactor` | No behaviour change |
| `docs` | SDD artifacts, README, comments that are documentation |
| `chore` | Tooling, formatting, lockfile-only when listed in the plan |
| `build` | Build scripts, packaging |
| `ci` | Checks and hooks |

### Scope

Prefer the task id when one exists: `feat(TASK-0001): ...`. For cross-cutting artifact work use `docs(sdd): ...` or `docs(approve): ...`.

### Examples

```text
feat(TASK-0001): add FastAPI application factory

Layered settings, correlation IDs, uniform errors, and health.

Implements: FEAT-0001#FR-002, FEAT-0001#FR-006, FEAT-0001#FR-010
Verifies: FEAT-0001#AC-003, FEAT-0001#AC-017
Refs: TASK-0001, FEAT-0001
```

```text
docs(approve): approve FEAT-0001 specification, architecture, and plan

Approved-by: Huy Le Quang
Refs: FEAT-0001, PLAN-0001
```

```text
docs(ADR-0014): add git branching and commit convention

Refs: ADR-0014, DN-0009
```

### Rules

- One logical change per commit. A task may be several commits; the final task state is not `COMPLETED` until its criteria pass.
- Do not commit secrets, `.env`, keychain exports, or local data directories.
- Do not use `--no-verify` unless the user explicitly asks.
- Do not amend a commit that has been pushed. Do not amend a commit you did not create in this session unless the user asks.
- Approval recording commits (`docs(approve): ...`) are made only after the user has approved; the AI never invents an approval.

## 6. Pull requests

- **Default:** one pull request per task, into `develop`.
- **Title:** `TASK-NNNN: <task title>` (same title as the task file when possible).
- **Body** (minimum):

```markdown
## Summary
- <what this task delivers>

## Trace
- Implements: ...
- Verifies: ...

## Evidence
- Commands run and results
- Criteria passed / not yet passed

## Merge
Human only. Do not merge or push without an explicit user decision.
```

- Rebase or merge commits onto the PR branch are fine; updating `develop` itself is not.
- The user merges. Squash or merge commit is the user's choice; prefer **squash** for a single-task PR so `develop` stays readable.

## 7. Tags and releases

- No release tags until the first delivered feature ships (FEAT-0001 delivery or later).
- When tagging starts: annotated tags `vMAJOR.MINOR.PATCH`, created only by the user.
- Do not move or delete tags that have been pushed.

## 8. Remotes

- A remote is optional. Local work does not require one.
- Pushing is always an explicit user decision (C-040).
- The AI never runs `git push`, `git push --force`, or sets `upstream` unless the user explicitly asks for that push.

## 9. What the engine will do later

When the product manages a project (ADR-0007):

- Task worktrees use `aio/<feature-key>/<task-key>`.
- Checkpoint commits on those branches are allowed without asking.
- Integration into a feature integration branch is allowed without asking.
- Integration into the project's `base_branch` (here, `develop`) remains human-only.
- Commit messages produced by the engine use the same format, with `Refs` pointing at the task and feature it is executing.

## 10. Adoption on this repository

After this design is approved:

1. Constitution v2 clauses take effect.
2. `AGENTS.md` and `project.yaml` reference this note.
3. Ongoing work for FEAT-0001 uses `task/TASK-NNNN-...` branches.
4. Optional commit-msg verification can be added under tooling (not required for approval of this ADR).
