# ADR-003: Parent-Child Chunking

**Status:** Accepted  
**Date:** 2026-06-14

## Context

Enterprise SOP documents have hierarchical structure. Small chunks improve retrieval precision; large chunks preserve context for generation.

## Decision

Index **child chunks** (512 tokens, overlap 64) in Qdrant for search. Link to **parent chunks** (2048 tokens) used as LLM context after retrieval.

## Consequences

**Positive:**

- Better retrieval precision on specific procedures
- Coherent generation context from parent text
- Fits structured manuals (HIS/ERP/WorkPal demos)

**Negative:**

- 2x storage for overlapping text
- Indexing pipeline complexity

## Parameters

| Parameter | Initial value |
|-----------|---------------|
| child_size | 512 tokens |
| child_overlap | 64 tokens |
| parent_size | 2048 tokens |

## References

- [agent-workflow.md §6.2](../agent-workflow.md#62-generate)
- [项目设计 ADR-003](../项目设计.md#adr-003parent-child-chunking)
