---
id: ADR-0012
type: adr
title: Local web app; the 3D office is an optional projection of shared state
version: 1
status: in_review
derives_from: [SYSTEM-DESIGN]
---

# ADR-0012: Local web app; the 3D office is an optional projection of shared state

## Context

The brief asks for a polished desktop-oriented experience with two modes, a dashboard and a 3D office, sharing backend state. It also requires that the dashboard work without 3D, that 3D not consume excessive resources, and that animations reflect only real activity.

## Decision

1. Ship a single-page web application served by the local engine and opened in the browser. No desktop shell; the user confirmed a browser-based local app.
2. Both modes read one client store that is updated by one event reducer over one WebSocket connection.
3. The 3D office is a **projection**: each avatar's presence is a pure function of store state (`derivePresence`), and animation is only the transition between two presences. The scene holds no state and issues the same REST commands as the dashboard.
4. The 3D code is a lazily loaded chunk that renders on demand, can be disabled entirely, and is built in Phase 8.

## Rationale

- A pure function from state to presence makes fabricated activity structurally impossible and makes the scene correct after a reload or reconnect.
- One store and one reducer mean the two modes cannot disagree.
- A browser application needs no installer, signing, or auto-update, and keeps the early phases focused on the engine.

## Consequences

- The application runs in a browser tab rather than its own window.
- The local server needs protection against other web pages (loopback bind, Host and Origin checks, token).
- Transitions that have no real cause do not exist: no idle typing, no time-based progress bars.
- Because the scene adds no capability of its own, every feature must exist in the dashboard first.

## Alternatives rejected

- Electron or Tauri from the start: packaging and update work before there is a product to package.
- A scene with its own simulation state: drifts from reality and invites decorative animation.
