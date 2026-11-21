---
id: ADR-0003
type: adr
title: Artifacts live on the filesystem; SQLite indexes them
version: 1
status: in_review
derives_from: [SYSTEM-DESIGN]
---

# ADR-0003: Artifacts live on the filesystem; SQLite indexes them

## Context

Specifications, decisions, plans, and tasks must be persistent, versioned engineering knowledge. They should be readable and editable with ordinary tools, travel with the project, and be reviewable in version control. The engine also needs fast queries over their relationships.

## Decision

Store each artifact as a markdown file with YAML front matter under the project's `.ai-office/` directory. Store an immutable snapshot of every revision under `.ai-office/.history/`. Keep an index in SQLite: artifacts, revisions with content hashes, requirement-level items, and trace links. The files are authoritative for content; the database is authoritative for approvals and relationships. A reindex command rebuilds the content index from disk.

## Rationale

- Artifacts remain useful without the application and can be committed with the code they describe.
- Explicit snapshots mean versioning does not depend on the user's git history or on commits the engine would need approval to make.
- Item-level indexing (each requirement and criterion hashed separately) is what makes impact analysis precise.

## Consequences

- Files can be edited outside the application, so the engine must detect that by hash and reconcile it into a draft revision.
- Two representations must be kept consistent. Approval records and trace links exist only in the database, so the database must be backed up; it cannot be fully reconstructed from the files.
- Document structure is constrained (front matter, required sections, keyed items) so that it can be parsed reliably.

## Alternatives rejected

- Artifacts stored only in the database: opaque, not portable, not reviewable in version control.
- Relying on git for versioning: not every project is a git repository, and it would couple revisions to commits.
