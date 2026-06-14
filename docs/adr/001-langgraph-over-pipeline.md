# ADR-001: LangGraph over Fixed Pipeline

**Status:** Accepted  
**Date:** 2026-06-14  
**Deciders:** BizMind team

## Context

Enterprise Q&A with private documents requires handling uncertain retrieval quality. A fixed pipeline (retrieve → generate) cannot express retry logic, query rewriting, or self-critique without ad-hoc imperative code.

## Decision

Use **LangGraph** to build an explicit state machine for the Agent workflow with conditional edges (router, grade, rewrite, critique).

## Consequences

**Positive:**

- Each node is independently testable with mocked LLM responses
- Conditional paths are visible in diagrams and Langfuse traces
- Strong interview narrative for "decision logic"

**Negative:**

- Higher learning curve than LangChain LCEL chains
- More LLM calls → higher latency and cost

## Alternatives Considered

| Alternative | Rejected because |
|-------------|------------------|
| Fixed RAG pipeline | No grade/rewrite/critique loops |
| Raw LangChain AgentExecutor | Opaque tool loop, harder to test |
| Custom asyncio state machine | Reinventing LangGraph |

## References

- [agent-workflow.md](../agent-workflow.md)
- [项目设计 ADR-001](../项目设计.md#adr-001langgraph-而非固定-pipeline)
