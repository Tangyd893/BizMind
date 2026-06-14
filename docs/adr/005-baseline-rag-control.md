# ADR-005: Baseline RAG as Control Group

**Status:** Accepted  
**Date:** 2026-06-14

## Context

Claims that "Agentic RAG is better" need quantitative evidence. Interviewers ask for A/B comparison, not only qualitative demos.

## Decision

Implement a **Baseline RAG** path (`/chat/baseline/stream` and `rag/baseline.py`): single dense retrieval + one LLM call, no Agent branches. Use it as the control group in RAGAS benchmarks.

## Consequences

**Positive:**

- Measurable Agent lift (faithfulness, precision, latency)
- Simpler fallback if Agent path fails in demo
- Feature flag for cost-sensitive tenants

**Negative:**

- Additional code path to maintain
- Two endpoints to test

## References

- [eval-benchmark.md §4](../eval-benchmark.md#4-实验设计)
- [api-spec.md §6.2](../api-spec.md#62-post-chatbaselinestream)
