# ADR-002: Qdrant over Chroma

**Status:** Accepted  
**Date:** 2026-06-14

## Context

Multi-tenant RAG requires strict payload filtering at vector search time. Hybrid retrieval (dense + sparse) is a v1 requirement.

## Decision

Use **Qdrant** as the vector database with payload filters on `tenant_id` and native hybrid search support.

## Consequences

**Positive:**

- Mature Docker deployment
- Payload `must` filters for tenant isolation
- Hybrid search without separate BM25 index (optional sparse vectors)

**Negative:**

- Heavier than Chroma for minimal prototypes
- Operational knowledge required for HNSW tuning

## Alternatives Considered

| Alternative | Rejected because |
|-------------|------------------|
| Chroma | Weaker multi-tenant filter story |
| Milvus | Heavier ops for MVP timeline |
| pgvector only | Hybrid + scale less proven for this use case |

## References

- [database-schema.md §5](../database-schema.md#5-qdrant-collection交叉引用)
- [architecture.md §7](../architecture.md#7-retrieval-pipeline)
