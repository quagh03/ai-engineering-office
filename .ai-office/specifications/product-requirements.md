---
id: PRD
type: product-requirements
title: AI Engineering Office product requirements
version: 1
status: in_review
source: Product brief, sections 1-18, and the user's answers of 2026-11-21
---

# AI Engineering Office: product requirements

This is the root of the traceability graph. Every feature specification derives from items here, and each item cites the section of the product brief it comes from. How the brief's ambiguities were resolved is recorded in the [discovery notes](discovery-notes.md).

## Vision

A local application in which a team of specialized AI agent roles, coordinated by an orchestration engine and driven by specifications, turns a described software idea into requirements, architecture, plans, working code, tests, reviews, and documentation. The work is done through Cursor CLI and Claude Code CLI, kept within budgets, and visible and controllable through a dashboard and a 3D office. People make the important decisions.

## Goals

- **G-001** Specifications drive development: every piece of work traces to an approved requirement. (brief 1, 2.1)
- **G-002** The required engineering quality is delivered at the lowest reasonable execution cost, with no redundant work. (brief 5)
- **G-003** Everything the system does is observable, controllable, recoverable, and accountable. (brief 18)
- **G-004** It is a working engineering platform first. The 3D office visualizes it and never dictates its design. (brief 1, 18)

## User stories

From the brief's definition of success (17). As the user, I can:

- **US-001** Open the application locally.
- **US-002** Create or import a software project.
- **US-003** Describe a new software feature.
- **US-004** Have the Product Owner role generate specifications.
- **US-005** Have the Architect role design the solution.
- **US-006** Have the Engineering Manager role decompose the work.
- **US-007** Assign implementation tasks to Cursor CLI or Claude Code CLI.
- **US-008** Have suitable execution configurations selected automatically.
- **US-009** Execute multiple independent tasks safely.
- **US-010** Control execution budgets.
- **US-011** Monitor estimated and actual costs.
- **US-012** Have tests and code reviews run automatically.
- **US-013** Track requirements through implementation and verification.
- **US-014** Inspect agent activity in the 3D office.
- **US-015** Pause, resume, and control agents.
- **US-016** Approve important decisions.
- **US-017** Recover project execution after restarting the application.
- **US-018** Understand exactly what has been completed, what remains, and what it has cost.

## Product requirements

### Spec-driven development

- **PR-001** Specifications, architecture decisions, plans, tasks, and acceptance criteria are persistent, versioned artifacts stored in the project's `.ai-office/` directory and indexed by the database. (brief 2.1, 4.2)
- **PR-002** Every feature follows eight stages: discovery, specification, architecture, planning, implementation, verification, review, delivery. (brief 4.1)
- **PR-003** A traceability graph links requirement, specification, decision, plan, task, code change, test, review, and delivery, and can be inspected. (brief 4.3)
- **PR-004** When a specification changes, the affected decisions, tasks, tests, and documentation are identified and marked for reassessment. (brief 2.1, 4.3)
- **PR-005** Agents work from approved artifacts rather than from conversation history. (brief 2.1)

### Events and observability

- **PR-010** Every meaningful activity produces a structured event. Important events are persisted so history can be reconstructed after a restart. (brief 2.2)
- **PR-011** The frontend receives updates in real time. (brief 2.2)
- **PR-012** Live agent status, execution timeline, task progress, provider health, usage, duration, cost, errors, retries, test results, approvals, and budget alerts are visible, with an event inspector filterable by project, agent, task, provider, event type, execution status, and date range. (brief 10)

### Providers

- **PR-020** Exactly two execution providers are supported: Cursor CLI and Claude Code CLI. (brief 1, 2.3, 7)
- **PR-021** Both integrate through one internal execution interface. Provider-specific behavior stays inside adapters, and the orchestration engine contains none. (brief 2.3, 7.3)
- **PR-022** Each adapter supports discovery, a configurable executable path, version detection, authentication and health checks, task execution in a chosen workspace, output capture, exit code handling, timeouts, permission controls, cancellation, streaming, and usage information, each where the CLI supports it. (brief 7.1, 7.2)
- **PR-023** Only officially supported CLI interfaces are used. No flag or capability is invented or assumed. (brief 7)

### Engineering organization

- **PR-030** Nine roles exist with the responsibilities in the brief: Product Owner, Technical Architect, Engineering Manager, Backend Developer, Frontend Developer, DevOps Engineer, QA Engineer, Code Reviewer, Documentation. (brief 3.1-3.3)
- **PR-031** Each role has an identifier, responsibilities, input and output contracts, allowed tools, permission boundaries, a provider preference, context requirements, a cost budget, and completion criteria, and is configurable. (brief 3.4)
- **PR-032** Roles are logical. A process is not started per role, and sessions are consolidated wherever one can do the work. (brief 3, 3.4, 5.6)

### Orchestration

- **PR-040** Tasks follow a controlled state machine that prevents invalid transitions. (brief 6.1)
- **PR-041** The engine schedules tasks, resolves dependencies, assigns work, and manages execution queues. (brief 6)
- **PR-042** Independent tasks can run in parallel safely: declared file and resource ownership, conflict detection, isolated workspaces, and controlled integration. Parallelism is used only when it is worth its cost. (brief 5.7, 6.2)
- **PR-043** Agents communicate through structured, task-oriented messages rather than open conversation. (brief 6.3)
- **PR-044** Executions, assignments, approvals, retries, and budget state survive a restart and are recovered safely. Potentially destructive operations are not restarted automatically. (brief 6.4)
- **PR-045** The user can pause, resume, stop, and cancel work. (brief 6, 9.4)

### Human control

- **PR-050** High-impact operations require approval: specifications, architecture, destructive file operations, dependency installation, commits and merges as configured, external integrations, permission escalation, deployment. Agents never make such decisions silently. (brief 2.4)

### Cost

- **PR-060** Tasks are classified by complexity and routed accordingly. Neither the most expensive nor an inadequately weak configuration is chosen by default. (brief 5.1)
- **PR-061** Provider selection supports a default, per-role and per-category preferences, manual and automatic selection, and explicitly configured fallback. A fixed provider is never switched silently, and a provider is verified as installed, authenticated, and operational before use. (brief 5.2)
- **PR-062** Budgets are configurable per execution, task, feature, project, day, and month, with three execution policies and configurable warning, reassessment, and stop thresholds. Budgets are never exceeded silently. (brief 5.3)
- **PR-063** Each execution receives a compact, task-specific context package with recorded provenance, never the whole project or conversation by default. (brief 5.4)
- **PR-064** Prompt templates are reusable and versioned per role. (brief 5.5)
- **PR-065** Retries are bounded and classified, reuse completed work, and escalate only when justified. Retry cost is recorded separately. (brief 5.8)
- **PR-066** Analyses, indexes, context packages, and test results are reused when their inputs are unchanged, invalidated by content hashes. (brief 5.9)
- **PR-067** A cost dashboard shows the analytics in the brief. Every figure is labeled as provider-reported, estimated, or unknown, and costs are never fabricated. (brief 5.10)
- **PR-068** The twelve cost rules and three questions of the brief apply to every engineering workflow. (brief 16)

### Memory

- **PR-070** Project, feature, task, and agent memory layers exist, with hybrid retrieval and no separate local model. Memory updates are auditable and never silently override approved specifications. (brief 8)

### User interface

- **PR-080** An engineering dashboard provides the task board, specifications, logs, architecture, execution monitoring, cost analytics, test results, and approval center, and is fully functional without 3D. (brief 9.5, 9.6)
- **PR-081** A 3D office shows the zones and agent avatars of the brief, driven only by real orchestration events. (brief 9.1-9.3)
- **PR-082** The user can inspect and control agents, tasks, executions, costs, and approvals from the 3D office. (brief 9.4)
- **PR-083** The 3D office is efficient, offers rendering quality and reduced-motion settings, and can be disabled completely. (brief 9.6)
- **PR-084** The interface is dark, clear, and professional, and makes plain what the team is doing, what is blocked, what needs approval, which provider runs each task, and how the budget stands. (brief 13)

### Safety

- **PR-090** Workspace boundaries, filesystem permissions, command policies, timeouts, cancellation, resource limits, secret protection, audit logs, and safe recovery are implemented. (brief 11)
- **PR-091** Application-level policy is enforced independently of provider permission controls. An agent can never expand its own permissions, and destructive actions need explicit authorization. (brief 11)

### Platform

- **PR-100** The application, its database, its processes, its configuration, and its event history are local. No cloud-hosted backend is required. The product states clearly that the CLIs' model inference is remote. (brief 2.5)
- **PR-101** Frontend: React, TypeScript, Vite, Tailwind CSS, three.js, React Three Fiber, Zustand. Backend: Python with FastAPI. Persistence: SQLite with migrations and transactions, and the local filesystem. Communication: REST and WebSockets. (brief 12)
- **PR-102** Startup and shutdown are simple, and ports and configuration are local and configurable. (brief 12)

### Quality

- **PR-110** A task is complete only when its acceptance criteria are satisfied and its verification checks pass. (brief 15)
- **PR-111** The workflow includes implementation, automated testing, code review, git integration, and documentation. (brief 14)

## Constraints

From the user's answers on 2026-11-21.

- **CON-001** The product is a browser-based local application. There is no desktop shell.
- **CON-002** macOS is the only supported platform.
- **CON-003** Cursor and Claude Code are used through the user's subscriptions and CLI logins. Cost accounting defaults to a subscription basis, in which dollar amounts are notional.
- **CON-004** The engine may commit to branches it owns. It has no permission to merge into the base branch or to merge a pull request; that is always an explicit human decision.
- **CON-005** This platform is itself built using its own SDD process.

## Features

Each feature gets its own specification, written and approved when its turn comes rather than all in advance. Order and dependencies are in the [roadmap](../plans/roadmap.md).

| Feature | Title | Primary requirements | Specification |
|---------|-------|----------------------|---------------|
| FEAT-0001 | Application foundation | PR-010, PR-011, PR-100, PR-101, PR-102, US-001, US-002 | [In review](features/FEAT-0001-foundation/spec.md) |
| FEAT-0002 | SDD engine | PR-001 to PR-005 | Not started |
| FEAT-0003 | Orchestration engine | PR-030 to PR-032, PR-040 to PR-045, PR-050 | Not started |
| FEAT-0004 | Cursor and Claude Code integrations | PR-020 to PR-023, PR-090, PR-091 | Not started |
| FEAT-0005 | Cost optimization engine | PR-060 to PR-068 | Not started |
| FEAT-0006 | Complete engineering workflow | PR-110, PR-111, US-003 to US-013 | Not started |
| FEAT-0007 | Project memory and observability | PR-012, PR-070 | Not started |
| FEAT-0008 | 3D virtual office | PR-081 to PR-084 | Not started |
| FEAT-0009 | Advanced capabilities | Brief 14, phase 9 | Not started |
