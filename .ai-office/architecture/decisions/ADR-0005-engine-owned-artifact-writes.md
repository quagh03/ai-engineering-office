---
id: ADR-0005
type: adr
title: Authoring executions are read-only; the engine writes artifacts
version: 1
status: approved
approved_by: Huy Le Quang
approved_at: 2026-11-21T15:14:01Z
derives_from: [SYSTEM-DESIGN]
---

# ADR-0005: Authoring executions are read-only; the engine writes artifacts

## Context

Product Owner, Architect, and Engineering Manager executions produce documents. The two CLIs differ: Claude Code can validate output against a JSON schema, Cursor cannot; and Cursor's print mode edits workspace files unless it is put in a read-only mode. Approved specifications must never be silently overwritten.

## Decision

Authoring and review executions run with the `read_only` permission profile. They return their documents as an **artifact bundle** in the final result text: one or more markdown documents with front matter, separated by a fixed marker. The engine validates the bundle (front matter schema, required sections, item keys, trace links), then writes the files, creates draft revisions, and records provenance. Agents have no write access to `.ai-office/`.

## Rationale

- Both CLIs return a final result text, so the mechanism is identical across providers.
- A read-only run cannot damage the workspace, so it can be retried automatically after an interruption.
- Every artifact change passes through one validated, audited code path.

## Consequences

- Bundles must be parsed strictly. A validation failure costs one repair turn on the same session, with the specific errors; a second failure goes to the user.
- Very large documents in a single result are a risk; templates keep artifacts focused and plans are split per task file.
- Where a provider supports schema-validated output, the adapter may use it for structured parts, as an enhancement that the engine does not depend on.

## Alternatives rejected

- Letting agents write artifact files directly: provider-dependent permissions, no validation before the write, and a path to overwriting approved content.
- Requiring schema-validated output: available on only one of the two providers.
