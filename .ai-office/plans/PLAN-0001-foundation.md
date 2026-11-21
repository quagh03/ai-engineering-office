---
id: PLAN-0001
type: plan
title: Implementation plan for the application foundation
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
feature: FEAT-0001
derives_from: [FEAT-0001]
---

# PLAN-0001: Application foundation

Approved with the [FEAT-0001 specification](../specifications/features/FEAT-0001-foundation/spec.md) and the architecture. Approving this plan also approved the dependencies it lists. [TASK-0001](../tasks/TASK-0001-backend-skeleton.md) is `READY`; the others stay in `BACKLOG` until their dependencies are completed.

## Tasks

| Task | Title | Role | Category | Depends on | Implements | Verifies |
|------|-------|------|----------|------------|------------|----------|
| [TASK-0001](../tasks/TASK-0001-backend-skeleton.md) | Backend skeleton | backend-developer | routine | - | FR-002, FR-006, FR-010 | AC-003, AC-017 |
| [TASK-0009](../tasks/TASK-0009-tooling-and-scripts.md) | Quality tooling and scripts | devops-engineer | routine | 0001 | FR-001, FR-011, NFR-001, NFR-002, NFR-004 | AC-001, AC-002, AC-019, AC-022 |
| [TASK-0002](../tasks/TASK-0002-database-and-migrations.md) | Database and migrations | backend-developer | routine | 0001 | FR-003 | AC-004, AC-005 |
| [TASK-0003](../tasks/TASK-0003-domain-core.md) | Domain core | backend-developer | simple | 0001 | FR-004 | - |
| [TASK-0004](../tasks/TASK-0004-event-store-and-bus.md) | Event store and bus | backend-developer | complex | 0002, 0003 | FR-004 | AC-006, AC-007 |
| [TASK-0005](../tasks/TASK-0005-rest-and-websocket.md) | REST foundation and WebSocket gateway | backend-developer | complex | 0004 | FR-005, FR-006, NFR-005 | AC-008, AC-009, AC-021 |
| [TASK-0006](../tasks/TASK-0006-local-api-protection.md) | Local API protection | backend-developer | critical | 0005 | FR-007, NFR-003 | AC-010, AC-011 |
| [TASK-0008](../tasks/TASK-0008-project-service.md) | Project service | backend-developer | routine | 0004, 0005 | FR-008 | AC-012, AC-013, AC-014 |
| [TASK-0007](../tasks/TASK-0007-frontend-shell.md) | Frontend shell | frontend-developer | routine | 0005, 0006, 0008 | FR-009, FR-006, FR-011 | AC-015, AC-016, AC-018 |

Rows are in execution order. Task numbers follow the roadmap's Phase 1 numbering (1.1 to 1.9).

## Sequencing

The tasks run one at a time. Several of them touch the same application wiring (the app factory and router registration), which is a shared resource under the parallel admission rules, and each task is short, so parallel execution would cost more in integration than it saves.

Tooling (TASK-0009) comes second so that every later task is checked by the same command from the start. TASK-0007 extends that command with the frontend checks.

## Coverage

Every requirement and criterion in the specification is owned by a task, except one criterion that is verified at the feature's review stage.

| Item | Covered by |
|------|-----------|
| FR-001 | TASK-0009; TASK-0007 adds serving the built UI |
| FR-002, FR-010 | TASK-0001 |
| FR-003 | TASK-0002 |
| FR-004 | TASK-0003, TASK-0004 |
| FR-005 | TASK-0005 |
| FR-006 | TASK-0001 (errors, health), TASK-0005 (OpenAPI), TASK-0007 (generated client) |
| FR-007 | TASK-0006 |
| FR-008 | TASK-0008 |
| FR-009 | TASK-0007 |
| FR-011, NFR-001, NFR-002, NFR-004 | TASK-0009, extended by TASK-0007 |
| NFR-003 | TASK-0006, and AC-020 at feature review |
| NFR-005 | TASK-0005 |
| AC-020 | Feature review stage (method: review) |
| Edge cases | Named in the completion criteria of TASK-0002, TASK-0005, and TASK-0008 |

## Feature-level gates

After the last task:

1. **Verification.** The check command passes on a clean checkout, and every acceptance criterion's status is recorded in `.ai-office/test-reports/FEAT-0001.md` with its evidence.
2. **Review.** One code review of the whole feature against the specification, the system design, and the constitution, including AC-020. Written to `.ai-office/reviews/`.
3. **Delivery.** A delivery report states what was completed, what remains, and any risk. Merging into the base branch is the user's decision (constitution C-040).

## Dependencies to approve

Approving this plan approves adding these (constitution C-041). Exact versions are pinned in lockfiles by the tasks that add them.

| Package | Used for | Added by |
|---------|----------|----------|
| fastapi, uvicorn | HTTP and WebSocket server | TASK-0001 |
| pydantic, pydantic-settings | Validation and layered settings | TASK-0001 |
| pyyaml | Reading `project.yaml` | TASK-0001 |
| sqlalchemy, aiosqlite, alembic | Database access and migrations | TASK-0002 |
| python-ulid | Sortable identifiers | TASK-0003 |
| pytest, pytest-asyncio, httpx | Backend tests | TASK-0001 |
| ruff, mypy, import-linter | Linting, type checking, boundary rules | TASK-0009 |
| react, react-dom, react-router-dom | UI and routing | TASK-0007 |
| zustand, @tanstack/react-query | Live state and server state | TASK-0007 |
| tailwindcss | Styling | TASK-0007 |
| vite, typescript, @vitejs/plugin-react | Frontend build | TASK-0007 |
| vitest, @testing-library/react, jsdom | Frontend unit tests | TASK-0007 |
| eslint, typescript-eslint | Frontend linting | TASK-0007 |
| openapi-typescript | Generating the API client types | TASK-0007 |
| @playwright/test | Browser tests for AC-015 and AC-016; downloads a browser once | TASK-0007 |

Logging uses the standard library, and the data directory path is fixed for macOS, so neither needs a package.

## Risks

| Risk | Mitigation |
|------|------------|
| The transactional event write (TASK-0004) is the foundation of every later feature | Classified complex; AC-006 and AC-007 test failure on both sides of the transaction |
| The API protection (TASK-0006) is a security boundary | Classified critical; reviewed on its own before TASK-0007 depends on it |
| Browser tests are slower and more fragile than the rest | Limited to the two criteria that need a real browser |

## Cost

No estimate is given. There is no execution history to estimate from, and bootstrap sessions are not metered by anything yet, so their cost is recorded as unknown (ADR-0013).
