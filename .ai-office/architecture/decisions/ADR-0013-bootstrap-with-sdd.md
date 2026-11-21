---
id: ADR-0013
type: adr
title: This platform is built with its own SDD process
version: 1
status: in_review
derives_from: [PRD#CON-005]
---

# ADR-0013: This platform is built with its own SDD process

## Context

The user requires that the AI Engineering Office itself be built using SDD. The engine that will manage SDD artifacts does not exist yet, so the process has to be followed by hand until it does.

## Decision

1. This repository is the first SDD project. Its engineering artifacts live in `.ai-office/`, in the same layout and document format the engine will later read: front matter with `id`, `type`, `version`, and `status`, and requirements and criteria as keyed items.
2. Until the engine can manage artifacts (the end of FEAT-0002), the process is run manually:
   - **Roles** are played by AI coding sessions in Cursor or Claude Code, directed by the user. A session states which role it is acting as.
   - **Approval** is given by the user and recorded in the artifact's front matter (`status: approved`, `approved_by`, `approved_at`). Sessions never record an approval on their own initiative.
   - **Revisions** are tracked by the `version` field together with version control: one commit per approved revision. The engine's `.history/` snapshots replace this later.
   - **Task state** is the `state` field in each task file, following the task state machine in the [domain model](../design/domain-model.md#3-task-state-machine).
   - **Verification** results are written to `.ai-office/test-reports/`, and reviews to `.ai-office/reviews/`.
   - **Cost** of bootstrap sessions is recorded as unknown, because nothing measures it yet.
3. `AGENTS.md` at the repository root carries the working rules to every AI session, so the process does not depend on a session remembering it.
4. When FEAT-0002 is delivered, this repository is imported into the platform as its first project. Indexing these hand-written artifacts without error is an exit criterion of that feature.

## Rationale

- Using the real layout and format now means the artifacts are test data for the parser, the format is exercised before code depends on it, and nothing needs converting later.
- Features are specified one at a time, when their turn comes, so later specifications benefit from what earlier features taught.
- The platform's own rules (approved specifications before code, traceable tasks, verified completion) are tested on a real project before they are automated.

## Consequences

- The process relies on discipline until the engine enforces it. `AGENTS.md` and the constitution are the safeguard.
- Without version control there is no history of approved revisions. A git repository is therefore a prerequisite for the first approval.
- Some overhead is accepted for small tasks during the bootstrap, since workflow profiles are not automated yet. The `quick` profile's rules are followed by hand for small changes.

## Alternatives rejected

- Building the platform ad hoc and adopting SDD once it works: contradicts the user's requirement, and the platform would be built without the discipline it exists to provide.
- Writing specifications for all nine features up front: large documents that would be out of date before they are used.
