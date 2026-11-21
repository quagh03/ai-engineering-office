---
id: ADR-0010
type: adr
title: Pointer-first context packages; no vector search in v1
version: 1
status: in_review
derives_from: [SYSTEM-DESIGN]
---

# ADR-0010: Pointer-first context packages; no vector search in v1

## Context

Agents must get focused context instead of the whole project or conversation history. Both CLIs are coding agents that can read and search files in their workspace on their own. No local model runtime may be introduced, and semantic search is allowed only where it is measurably beneficial.

## Decision

A context package **inlines** only what must be authoritative and compact: the role card, the objective and output contract, the linked acceptance criteria verbatim, relevant constraints, required interface signatures, and a digest of prior attempts. Everything else is given as **pointers**: file paths with the reason they matter and, when available, symbol names and line ranges.

Retrieval uses, in order: trace links, SQLite FTS5 keyword search, and code structure (file index, import graph, tree-sitter symbols). No embeddings and no vector index in v1. Retrieval is measured, and those measurements decide whether vector search is added later.

Each package has a stored manifest listing every item with its revision or hash, provenance, and reason for inclusion.

## Rationale

- Inlined file content is paid for whether or not the agent needs it and can be stale by the time it is read; a pointer costs a few tokens and the agent reads the current file.
- Trace links already encode which specifications and files belong to a task, which is more precise than similarity search.
- FTS5 and tree-sitter are local, cheap, and need no model.

## Consequences

- Agents spend some tool calls reading files; that cost is visible in the stream and is part of what retrieval measurement tracks.
- Pointer quality depends on the planner declaring an accurate write scope and on the indexes being current.
- Embedding-based retrieval would require either a remote embedding service or a local model, both outside the current constraints.

## Alternatives rejected

- Inlining all relevant files: large prompts, stale content, duplicated reading.
- Vector search from the start: added machinery with unmeasured benefit, and no permitted way to compute embeddings locally.
