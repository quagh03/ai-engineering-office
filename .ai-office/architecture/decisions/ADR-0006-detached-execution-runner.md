---
id: ADR-0006
type: adr
title: Detached execution runner with file-backed output
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
derives_from: [SYSTEM-DESIGN]
---

# ADR-0006: Detached execution runner with file-backed output

## Context

Executions can run for many minutes and must survive an application restart. If the engine spawns a CLI directly and reads its pipe, an engine crash breaks the pipe, loses the output, and leaves the exit code uncollectable. Timeouts enforced by the engine also stop being enforced when the engine is down.

## Decision

Each execution is launched through a small **runner** process (`python -m aio.runner`) started in its own session and process group. The runner starts the CLI, redirects stdout and stderr to files in the execution's directory, enforces the timeout and output cap, and writes an exit record (exit code, signal, timestamps, whether it timed out) when the CLI ends. The engine never reads a pipe: it tails the output file from a persisted offset. Provider adapters are pure translators and own no process.

## Rationale

- After a crash the engine can reattach by resuming the tail, or settle a finished execution from the exit record.
- A timeout holds even with the engine stopped, so no execution runs unbounded.
- Pure adapters can be tested against recorded files with no process and no cost.
- The raw output file is the complete, replayable record of what the provider emitted.

## Consequences

- The provider contract is shaped as `build_invocation` / `parse_event` / `finalize` rather than a single `execute` generator; the execution manager composes them.
- Liveness is checked by pid together with process start time, to avoid mistaking a reused pid for the runner.
- Relies on POSIX sessions and signals. macOS is the only supported and tested platform.
- Output files need retention management.

## Alternatives rejected

- Direct child process with piped output: simplest, but an engine crash loses the execution.
- Cancelling all executions on engine exit: safe but wastes paid work on every restart.
- A terminal multiplexer or the CLIs' own background modes: provider-specific and not available on both.
