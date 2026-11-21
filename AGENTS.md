# Working rules for AI sessions

This project is built with Spec-Driven Development. Its engineering artifacts are in `.ai-office/`. These rules apply to every session, in Cursor or Claude Code.

## Before doing anything

1. Read `.ai-office/constitution.md`. It is binding.
2. Find the task you are working on in `.ai-office/tasks/`. If there is no task for the work, stop and say so; do not start coding.
3. Read the specification items the task lists under `implements` and `verifies`, and the design documents it references. Do not read the whole repository.

## Rules that are most often broken

- **No code without an approved specification.** If the feature's `spec.md` is not `status: approved`, the only work allowed is on the artifacts themselves.
- **Only the user approves.** Never set `status: approved`, never waive an acceptance criterion, never mark your own task `COMPLETED` without the evidence the task requires.
- **Approved artifacts are not edited in place.** Propose a new version, set it to `in_review`, and list what it affects.
- **Stay in the task's `write_scope`.** If the work needs a file outside it, stop and ask.
- **Report honestly.** State what was verified and how, what was not verified, and what remains.
- **Commits are allowed on working branches. Merging into the base branch, merging a pull request, and pushing are the user's decisions.**
- **No new dependency** unless the approved plan lists it.

## Working on a task

1. State which role you are acting as (the task's `role`).
2. Set the task's `state` as you go, following the state machine in `.ai-office/architecture/design/domain-model.md`.
3. Write tests with the code. Run the project's check command before reporting.
4. Finish with a completion report: criteria addressed and their evidence, files changed, commands run and their results, anything blocked or unverified.

## Where things are

| Need | Location |
|------|----------|
| What the product must do | `.ai-office/specifications/product-requirements.md` |
| A feature's requirements and acceptance criteria | `.ai-office/specifications/features/<feature>/spec.md` |
| How the system is designed | `.ai-office/architecture/system-design.md`, `.ai-office/architecture/design/` |
| Why a decision was made | `.ai-office/architecture/decisions/` |
| What to build next | `.ai-office/plans/`, `.ai-office/tasks/` |
| How the process works before the engine exists | `.ai-office/architecture/decisions/ADR-0013-bootstrap-with-sdd.md` |
