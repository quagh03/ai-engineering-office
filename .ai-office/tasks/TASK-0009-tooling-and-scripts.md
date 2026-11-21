---
id: TASK-0009
type: task
title: Quality tooling and scripts
version: 1
status: draft
state: BACKLOG
feature: FEAT-0001
plan: PLAN-0001
role: devops-engineer
category: routine
depends_on: [TASK-0001]
implements: [FEAT-0001#FR-001, FEAT-0001#FR-011, FEAT-0001#NFR-001, FEAT-0001#NFR-002, FEAT-0001#NFR-004]
verifies: [FEAT-0001#AC-001, FEAT-0001#AC-002, FEAT-0001#AC-019, FEAT-0001#AC-022]
write_scope:
  - scripts/**
  - backend/pyproject.toml
  - backend/uv.lock
  - backend/.importlinter
  - backend/tests/**
  - .gitignore
  - .ai-office/project.yaml
---

# TASK-0009: Quality tooling and scripts

## Objective

Provide the commands the project is run and checked with, so that every later task is verified the same way: start, stop, and one check command that runs everything.

## Deliverables

- `scripts/start` and `scripts/stop`. Start fails clearly when the port is in use. Stop ends the engine cleanly.
- `scripts/check`: ruff format check, ruff lint, mypy in strict mode, the import-linter contracts, and pytest. It exits non-zero if any step fails and names the step.
- Import-linter contracts for the dependency rules in the system design: `domain` imports no other application module, and `orchestration` does not import a concrete provider adapter. Contracts for modules that do not exist yet are added by the tasks that create them.
- Python and Node.js versions pinned for the project.
- The commands declared by name in `.ai-office/project.yaml`.

## Completion criteria

- AC-001, AC-002, and AC-022 pass. AC-019 passes for the backend: the check command succeeds on a clean checkout and fails when a deliberate type error, boundary violation, or failing test is introduced, each demonstrated and then removed.
- AC-019 is verified again at the feature's verification gate, after TASK-0007 has added the frontend checks.

## References

[System design](../architecture/system-design.md#3-components), [roadmap](../plans/roadmap.md#working-rules).
