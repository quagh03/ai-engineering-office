---
id: CONSTITUTION
type: constitution
title: Project constitution
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
---

# Project constitution

The rules every piece of work on this project must follow, whoever or whatever does it. They come from sections 15 and 16 of the product brief and from the user's answers during discovery. A task that cannot be done without breaking a clause stops and raises it; it does not proceed.

## Process

- **C-001** Work is driven by artifacts. No code is written for a feature until its specification is `approved`, and no task is started unless it links to at least one approved specification item.
- **C-002** Only the user approves. An AI session never sets an artifact to `approved`, never waives an acceptance criterion, and never approves its own work.
- **C-003** An approved artifact is not edited in place. A change is a new version that returns to `in_review`; the tasks, tests, and documents it affects are identified and flagged before work continues.
- **C-004** Stages run in order: discovery, specification, architecture, planning, implementation, verification, review, delivery. A stage's gate must pass before the next stage's work is approved.
- **C-005** An architectural change is made by adding or superseding a decision record, never by drifting from one.
- **C-006** Ambiguity is raised as a question, not settled by a silent assumption. An assumption that must be made is written down and labeled as one.

## Engineering

- **C-010** Tasks are small and individually verifiable. A feature is not generated in one pass.
- **C-011** Tests are written with the code they test, in the same task.
- **C-012** The application stays runnable after every task.
- **C-013** Module boundaries in the system design are enforced by tooling. The orchestration engine contains no provider-specific logic.
- **C-014** Type checking is strict in both backend and frontend. Suppressions need a written reason.
- **C-015** No abstraction is added before something needs it.
- **C-016** A task changes only the files in its declared write scope. Anything else is raised first.

## Verification

- **C-020** A task is complete only when its acceptance criteria are verified and its required checks pass. Producing code is not completion.
- **C-021** Nothing is reported as verified, passed, or measured unless it was. Unverified items are reported as unverified.
- **C-022** External integrations are never faked in product code. Recorded-output replay exists in the test suite only.
- **C-023** Remaining risks and unfinished items are reported at the end of every task and feature.

## Cost

- **C-030** One AI session is used where one is enough. Roles are not a reason to start more sessions.
- **C-031** Work that code can do deterministically is done by code: tests, git, indexing, reports.
- **C-032** A session receives the context its task needs, not the whole project or the conversation history.
- **C-033** Analysis is not repeated while its inputs are unchanged.
- **C-034** A failure is classified before any retry, and the same failure is not retried indefinitely.
- **C-035** Tests that call a real provider spend real usage. They run only deliberately, and what they consumed is recorded.
- **C-036** Cost savings are stated only when measured. Subscription usage is never treated as free or unlimited.
- **C-037** Documentation is written only when it has engineering value.

## Safety

- **C-040** Commits are allowed on working branches. Nothing is merged into the base branch, no pull request is merged, and nothing is pushed to a remote without an explicit decision from the user for that specific action.
- **C-041** Dependencies are added only with the user's approval, each named with its purpose.
- **C-042** Destructive file operations outside a task's scope need approval.
- **C-043** Secrets are never written to artifacts, prompts, logs, or the repository.
- **C-044** CLI flags and provider behavior are used only when verified against the installed binary or official documentation. Unverified behavior is marked as such.

## Constraints

- **C-050** The only AI execution providers are Cursor CLI and Claude Code CLI. No other provider, and no local model runtime, is integrated.
- **C-051** The application runs locally on macOS as a browser-based app. No cloud-hosted backend is required to use it.
- **C-052** The dashboard is built before the 3D office and must work without it. The 3D office shows only real system state.
