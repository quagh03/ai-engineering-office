---
id: DN-0007
type: design-note
title: Frontend and 3D office
version: 1
status: in_review
derives_from: [PRD, SYSTEM-DESIGN]
---

# Frontend and 3D Office

The frontend is one React application with two modes over one store. The dashboard is complete without the 3D office. The 3D office renders the same state and issues the same commands; it holds no state of its own and is built last ([ADR-0012](../decisions/ADR-0012-local-web-app-3d-as-projection.md)).

## 1. Structure

```text
frontend/src/
├── api/          generated REST client, WebSocket client (resume, resync)
├── store/        Zustand slices and the single event reducer
├── features/     board, specs, architecture, executions, costs, tests, approvals, events, settings
├── inspector/    shared detail panel for agent, task, execution
├── office3d/     lazy-loaded scene
└── app/          shell, routing, theme
```

### State

- **TanStack Query** loads snapshots and paged history (artifacts, cost breakdowns, event history).
- **Zustand** holds live state derived from events: agents, tasks, executions, approvals, budgets, provider health, a bounded buffer of recent events, and UI preferences.
- **One reducer**, `applyEvent(state, event)`, is the only code that turns events into state. It is a pure function tested against recorded event sequences. Both modes read through selectors over the result.

### Shell

Present in both modes: project switcher, mode toggle (Office / Dashboard), provider health indicators, budget meter with measurement level, approvals indicator with count, connection status. The **inspector panel** on the right is shared: selecting an agent in the 3D office and selecting it in the dashboard open the same component.

## 2. Dashboard mode

| View | Shows | Actions |
|------|-------|---------|
| Overview | Active feature and stage, what is running, what is blocked, what needs approval, budget position | Describe a feature |
| Task board | Columns by task state; cards show role, provider, category, estimate and actual, reassessment flag | Create, assign, pin provider, pause, resume, cancel, retry |
| Dependencies | Task graph with state colors and the reason any task is deferred | - |
| Specifications | Artifact tree, rendered documents, revision history and diffs, impact preview | Edit a draft, approve, reject |
| Architecture | Design documents, diagrams, ADR list | Approve, reject |
| Traceability | Requirement to code to test, navigable in both directions; acceptance criteria matrix | Waive a criterion (recorded) |
| Executions | Running and past executions; live output; prompt, context manifest, diff, cost | Stop |
| Tests | Verification runs, results per criterion, reused runs marked | Re-run |
| Costs | The analytics in [cost and context](cost-and-context.md#11-analytics); budgets and thresholds | Edit budgets, pricing assumptions |
| Approvals | Pending requests with the exact action and its context | Approve, reject, with a note |
| Events | The event inspector | Filter |
| Settings | Providers, tier mappings, policies, roles, rendering | Edit |

## 3. 3D office mode

### Scene

An isometric office (orthographic camera, limited orbit and zoom) with fixed zones:

| Zone | Occupants and use |
|------|-------------------|
| Command center | Engineering Manager desk; wall display of stage, budget, and approvals |
| Product planning | Product Owner desk |
| Architecture room | Architect desk |
| Backend area | Backend Developer desk |
| Frontend area | Frontend Developer desk |
| QA laboratory | QA Engineer desk; where agents go while their task is in `TESTING` |
| DevOps room | DevOps Engineer desk |
| Review area | Code Reviewer desk; where agents go while their task is in `REVIEW` |
| Documentation corner | Documentation desk |
| Meeting room | Where a sender and recipient meet when a structured message is exchanged |

The layout is data (`officeLayout.ts`: zone bounds, desk positions, a waypoint graph). Avatars are low-poly primitives with a role color and a status ring, not imported character models, which keeps the scene light and avoids an asset pipeline.

### Avatar state is a function of real state

```ts
type Presence = {
  zone: ZoneId
  pose: 'idle' | 'receiving' | 'reading' | 'working' | 'testing'
      | 'reviewing' | 'waiting' | 'alert' | 'celebrating' | 'paused'
  taskId?: string
  executionId?: string
  provider?: 'cursor' | 'claude-code'
  progress?: { done: number; total: number }
}

function derivePresence(role: RoleId, state: OfficeState): Presence
```

`derivePresence` is pure. Animation is how the scene moves from the previous presence to the new one. Consequently a reload or reconnect shows the correct scene immediately, and there is no code path that can animate work that is not happening. A role with no execution and no active task is `idle` at its desk and is labeled idle.

| Real event | Presence change | Rendering |
|------------|-----------------|-----------|
| `AgentStarted` | Role becomes active | Avatar walks to its workspace |
| `TaskAssigned` | `receiving` | Task card appears at the desk |
| Authoring execution running | `reading` | Avatar reviews documents |
| Implementation execution running | `working` | Avatar at the computer; monitor lit in the provider's color |
| `AgentActivityChanged` | Sub-state within `working` | Reading, editing, or running a command, shown on the monitor |
| Task enters `TESTING`, `TestStarted` | `testing`, zone QA lab | Avatar walks to the QA lab |
| Task enters `REVIEW` | `reviewing`, zone review area | Avatar walks to the review area |
| `TaskBlocked` | `waiting` | Waiting pose with the blocker shown |
| `ApprovalRequested` | `alert` | Alert marker above the avatar and on the command center display |
| `TaskCompleted` | `celebrating`, then `idle` | Brief completion animation |
| `TaskPaused` | `paused` | Dimmed with a pause marker |
| `AgentMessageSent` | Both roles to the meeting room briefly | Link drawn between the two |

**Progress** is shown only from real counts: completion criteria met out of total, or checks passed out of total. There is no time-based progress bar.

**Provider visibility.** The monitor color and a label show which provider and model is executing each task. Two executions as the same role (parallel backend tasks) appear as a second workstation in that zone.

### Interaction

Clicking an avatar, desk, or display opens the shared inspector. Every action calls the same REST command as the dashboard.

| Target | Inspector content | Actions |
|--------|-------------------|---------|
| Avatar | Role profile, current task, live activity, execution log, history, cost | Assign a task, pause, resume, stop the execution |
| Task card | Task detail, dependencies, trace links, criteria status | Open specification, pause, cancel |
| Alert marker | The approval request | Approve, reject |
| Command center display | Stage, budget, pending approvals | Open the corresponding dashboard view |
| Link between avatars | The messages exchanged | Open the message thread |

## 4. Performance

| Technique | Use |
|-----------|-----|
| Lazy loading | The `office3d` chunk, three.js, and drei load only when the mode is first opened |
| Event-driven rendering | `frameloop="demand"`; a frame is requested when presence changes or a transition is running. An idle office renders nothing |
| Instancing | Desks, chairs, monitors, wall panels, and floor tiles as instanced meshes |
| Level of detail | Zoomed out: simplified avatars, no labels. Labels are GPU text, not DOM overlays |
| Efficient updates | Transitions mutate object transforms through refs; they do not trigger React re-renders. Components subscribe to narrow selectors |
| Quality presets | Low: no shadows, no post-processing, capped pixel ratio. Medium: basic shadows. High: soft shadows and restrained bloom |
| Reduced motion | Follows `prefers-reduced-motion` and a setting: avatars change position without walking, no idle motion |
| Off switch | 3D can be disabled entirely. With it off, or if WebGL is unavailable, the three.js chunk is never loaded |
| Background tab | Rendering stops when the tab is hidden |

A frame-time budget is checked in development, and the Phase 8 exit criteria include measured idle CPU and memory.

## 5. Visual direction

Dark theme, restrained neon accents used for meaning (provider identity, status, alerts) rather than decoration, translucent panels with enough contrast to read, a clear type scale, and short transitions. Accessibility requirements apply to the dashboard throughout: keyboard navigation, visible focus, sufficient contrast, and no information conveyed by color alone. Because every 3D action exists in the dashboard, the application is fully usable without the 3D scene.
