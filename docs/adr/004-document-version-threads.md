# ADR-004: Document Version Aware Threads

**Status:** Accepted  
**Date:** 2026-06-14

## Context

When knowledge base documents are updated or re-indexed, existing chat threads may reference stale chunks, producing outdated or contradictory answers—a common production RAG pain point.

## Decision

Maintain a global `documents_version` counter incremented on successful index/delete. Threads snapshot version at creation. When version advances, mark older threads `is_stale` and prompt users to start new conversations.

## Consequences

**Positive:**

- Explicit handling of KB drift
- Demonstrates production-minded engineering in interviews

**Negative:**

- Users must start new threads after updates
- Extra DB field and bump logic on every index

## Behavior

```
Thread created at version=N → Active
Document indexed → version=N+1 → Thread.is_stale=true
User creates new thread → snapshot N+1 → Active
```

## References

- [database-schema.md §4.4–4.5](../database-schema.md#44-documents_version_counter)
- [architecture.md §9](../architecture.md#9-document-version-awareness)
