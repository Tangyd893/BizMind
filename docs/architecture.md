# BizMind — System Architecture

> **Version:** v0.1  
> **Status:** Design phase  
> **Related:** [项目设计](./项目设计.md) · [database-schema](./database-schema.md) · [agent-workflow](./agent-workflow.md)

---

## 1. Architecture Overview

BizMind is a multi-tenant Agentic RAG platform. The system separates **document ingestion**, **retrieval**, and **agent orchestration** into distinct layers with clear boundaries.

### 1.1 Quality Attributes

| Attribute | Target | Mechanism |
|-----------|--------|-----------|
| Isolation | Zero cross-tenant leakage | PG filter + Qdrant payload filter |
| Accuracy | RAGAS faithfulness ≥ 0.85 | Hybrid retrieval + rerank + Agent grade/critique |
| Latency | First token < 2s P95 | Streaming SSE, embedding cache, parallel I/O |
| Observability | End-to-end trace | Langfuse spans per Agent node |
| Reproducibility | Benchmark in README | Golden QA + RAGAS batch script |

---

## 2. C4 Context Diagram

```mermaid
C4Context
    title BizMind System Context

    Person(employee, "Employee", "Queries internal SOPs and manuals")
    Person(admin, "Admin", "Manages users and eval benchmarks")

    System(bizmind, "BizMind", "Multi-tenant Agentic RAG platform")

    System_Ext(llm, "LLM Provider", "OpenAI-compatible API")
    System_Ext(embed, "Embedding API", "Vector embeddings")
    System_Ext(tavily, "Tavily", "Web search fallback")
    System_Ext(langfuse, "Langfuse", "Tracing and observability")

    Rel(employee, bizmind, "Chat, upload docs", "HTTPS/SSE")
    Rel(admin, bizmind, "Admin, eval", "HTTPS")
    Rel(bizmind, llm, "Generate, grade, critique", "HTTPS")
    Rel(bizmind, embed, "Embed chunks and queries", "HTTPS")
    Rel(bizmind, tavily, "Web fallback", "HTTPS")
    Rel(bizmind, langfuse, "Traces", "HTTPS")
```

---

## 3. Container Diagram

```mermaid
flowchart TB
    subgraph client [Client Tier]
        WEB[React SPA<br/>Vite + Tailwind]
    end

    subgraph app [Application Tier]
        API[FastAPI Backend<br/>Port 8000]
        AGENT[LangGraph Agent]
        RAG[RAG Subsystem]
    end

    subgraph data [Data Tier]
        PG[(PostgreSQL 16)]
        QD[(Qdrant)]
        RD[(Redis 7)]
        FS[File Storage<br/>Local Volume]
    end

    subgraph external [External Services]
        LLM[LLM API]
        EMB[Embedding API]
        LF[Langfuse]
    end

    WEB -->|REST + SSE| API
    API --> AGENT
    API --> RAG
    AGENT --> RAG
    API --> PG
    API --> RD
    RAG --> QD
    RAG --> EMB
    RAG --> FS
    AGENT --> LLM
    AGENT --> LF
    API --> PG
```

---

## 4. Backend Component Diagram

```mermaid
flowchart LR
    subgraph api_layer [API Layer]
        AUTH_R[auth.py]
        DOC_R[documents.py]
        CHAT_R[chat.py]
        EVAL_R[eval.py]
    end

    subgraph services [Service Layer]
        AUTH_S[AuthService]
        DOC_S[DocumentService]
        CHAT_S[ChatService]
        EVAL_S[EvalService]
    end

    subgraph rag [RAG Subsystem]
        PARSER[Parsers]
        CHUNK[Chunking]
        EMB[Embedding]
        VS[VectorStore]
        RET[Retriever]
        BASE[Baseline RAG]
    end

    subgraph agent [Agent Subsystem]
        GRAPH[LangGraph]
        NODES[Nodes]
        PROMPTS[Prompts]
    end

    subgraph core [Cross-cutting]
        SEC[Security/JWT]
        RBAC[RBAC]
        RL[RateLimit]
        LOG[Logging]
    end

    AUTH_R --> AUTH_S
    DOC_R --> DOC_S
    CHAT_R --> CHAT_S
    EVAL_R --> EVAL_S

    DOC_S --> PARSER --> CHUNK --> EMB --> VS
    CHAT_S --> GRAPH
    GRAPH --> NODES --> RET
    RET --> VS
    CHAT_S --> BASE
    BASE --> RET

    api_layer --> core
```

### 4.1 Layer Responsibilities

| Layer | Responsibility | Must NOT |
|-------|----------------|----------|
| `api/` | HTTP binding, auth deps, response mapping | Business logic, direct ORM in routes |
| `services/` | Use-case orchestration, transactions | LangGraph node logic |
| `rag/` | Parse, chunk, embed, retrieve | Agent routing decisions |
| `agent/` | State machine, LLM calls for workflow | Direct DB access (via injected services) |
| `core/` | Security, logging, rate limit | Domain rules |

---

## 5. Document Ingestion Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant DS as DocumentService
    participant FS as File Storage
    participant PG as PostgreSQL
    participant RAG as RAG Pipeline
    participant QD as Qdrant

    U->>API: POST /documents/upload
    API->>DS: validate mime, size
    DS->>FS: save file
    DS->>PG: insert document (pending)
    API-->>U: 202 {id, status: pending}

    DS->>RAG: parse → chunk → embed
    RAG->>QD: upsert vectors + payload
    DS->>PG: bump documents_version
    DS->>PG: update status=indexed
    DS->>PG: mark threads stale
```

---

## 6. Chat / Agent Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant CS as ChatService
    participant G as LangGraph
    participant R as Retriever
    participant LLM as LLM API
    participant PG as PostgreSQL

    U->>API: POST /chat/stream {thread_id, message}
    API->>CS: authorize tenant, load thread
    CS->>PG: save user message
    CS->>G: invoke AgentState

    loop Agent nodes
        G->>LLM: router / grade / generate / critique
        G->>R: retrieve (hybrid + rerank)
    end

    CS-->>U: SSE token events
    CS-->>U: SSE citation events
    CS->>PG: save assistant message
    CS-->>U: SSE done event
```

---

## 7. Retrieval Pipeline

```mermaid
flowchart LR
    Q[User Query] --> EMB_Q[Embed Query]
    EMB_Q --> DENSE[Dense Search<br/>Qdrant HNSW]
    Q --> SPARSE[BM25 Sparse]
    DENSE --> FUSE[Score Fusion<br/>RRF or weighted]
    SPARSE --> FUSE
    FUSE --> RERANK[Cross-Encoder Rerank]
    RERANK --> TOPK[Top-K Parent Chunks]
    TOPK --> CTX[LLM Context]
```

**Default parameters:**

| Parameter | Value |
|-----------|-------|
| Dense top_k | 20 |
| Sparse top_k | 20 |
| Fusion | RRF k=60 |
| Rerank top_k | 4 |
| Context | Parent chunks (2048 tokens each) |

---

## 8. Multi-Tenancy Model

```mermaid
flowchart TB
    subgraph tenant_a [Tenant A]
        UA[Users A]
        DA[Documents A]
        QA[Qdrant filter tenant_id=A]
    end

    subgraph tenant_b [Tenant B]
        UB[Users B]
        DB[Documents B]
        QB[Qdrant filter tenant_id=B]
    end

    UA --> DA --> QA
    UB --> DB --> QB
```

**Defense in depth:**

1. JWT carries `tenant_id` claim
2. All PG queries include `WHERE tenant_id = :tenant_id`
3. Qdrant search always applies `must: [{ key: tenant_id, match: { value } }]`
4. Integration tests assert cross-tenant 404

---

## 9. Document Version Awareness

```mermaid
stateDiagram-v2
    [*] --> Active: Thread created<br/>snapshot version=N
    Active --> Stale: New doc indexed<br/>version=N+1
    Stale --> Active: User creates new thread<br/>snapshot version=N+1

    note right of Stale
        UI shows banner:
        Knowledge base updated
    end note
```

---

## 10. Deployment Topology (Docker Compose)

```mermaid
flowchart TB
    subgraph compose [Docker Compose Network]
        NG[frontend:3000<br/>nginx]
        BE[backend:8000]
        PG[(postgres:5432)]
        QD[(qdrant:6333)]
        RD[(redis:6379)]
        LF[langfuse:3001<br/>optional profile]
    end

    USER[Browser] --> NG
    NG -->|/api proxy| BE
    BE --> PG
    BE --> QD
    BE --> RD
    BE -.-> LF
```

See [deployment.md](./deployment.md) for service definitions and volumes.

---

## 11. Technology Mapping

| Concern | Technology | Module |
|---------|------------|--------|
| HTTP API | FastAPI | `backend/app/api/` |
| Agent | LangGraph | `backend/app/agent/` |
| ORM | SQLAlchemy 2 async | `backend/app/models/` |
| Migrations | Alembic | `backend/alembic/` |
| Vector DB | qdrant-client | `backend/app/rag/vectorstore.py` |
| Cache | redis-py | `backend/app/core/rate_limit.py` |
| Frontend | React 19 + Vite | `frontend/src/` |
| Eval | RAGAS | `scripts/eval_rag.py` |

---

## 12. ADR Index

| ID | Title | Status |
|----|-------|--------|
| [ADR-001](./adr/001-langgraph-over-pipeline.md) | LangGraph over fixed pipeline | Accepted |
| [ADR-002](./adr/002-qdrant-over-chroma.md) | Qdrant over Chroma | Accepted |
| [ADR-003](./adr/003-parent-child-chunking.md) | Parent-Child chunking | Accepted |
| [ADR-004](./adr/004-document-version-threads.md) | Document version aware threads | Accepted |
| [ADR-005](./adr/005-baseline-rag-control.md) | Baseline RAG as control group | Accepted |

---

## 13. Revision History

| Version | Date | Description |
|---------|------|-------------|
| v0.1 | 2026-06-14 | Initial architecture with Mermaid diagrams |
