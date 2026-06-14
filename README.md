# BizMind

**Business Mind** — 面向企业私有文档的多租户 Agentic RAG 平台。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **当前状态：** 设计阶段（v0.1-design）— 文档已就绪，编码尚未开始。

## 特性

- **Agentic RAG** — LangGraph 编排：Router → Retrieve → Grade → Rewrite → Generate → Critique
- **Hybrid Retrieval** — Dense + BM25 + Cross-Encoder Rerank
- **多租户隔离** — PostgreSQL + Qdrant payload 双重 filter
- **文档版本感知** — 知识库更新后自动标记 stale 会话
- **流式对话** — SSE + 引用溯源
- **可量化评测** — Golden QA + RAGAS，Baseline vs Agent 对比

## 架构概览

```
Web (React) ──SSE/REST──► FastAPI ──► LangGraph Agent
                              │              │
                              ▼              ▼
                         PostgreSQL    RAG (Qdrant)
                              │
                           Redis
```

详细架构见 [docs/architecture.md](docs/architecture.md)。

## 快速开始

```bash
git clone https://github.com/Tangyd893/BizMind.git
cd BizMind
cp .env.example .env   # Windows: copy .env.example .env
```

**本地开发（推荐）：**

```bash
make infra-up          # 或 .\scripts\dev.ps1 infra-up
make migrate
make dev-backend       # API :8000
make dev-frontend      # UI  :5173
```

**Docker 全栈：**

```bash
docker compose up -d --build
curl http://localhost:8000/api/v1/health
open http://localhost:3000
```

## 文档

| 文档 | 说明 |
|------|------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | 协作流程与 Definition of Done |
| [docs/README.md](docs/README.md) | 文档中心索引 |
| [docs/decisions.md](docs/decisions.md) | 编码前已定工程决策 |
| [docs/p1-backlog.md](docs/p1-backlog.md) | P1 任务拆解 |
| [docs/项目设计.md](docs/项目设计.md) | 总体设计 |
| [docs/requirements.md](docs/requirements.md) | 需求规格 (SRS) |
| [docs/architecture.md](docs/architecture.md) | 系统架构 |
| [docs/api-spec.md](docs/api-spec.md) | API 规范 |
| [docs/agent-workflow.md](docs/agent-workflow.md) | LangGraph 工作流 |
| [docs/development-guide.md](docs/development-guide.md) | 开发指南 |

## 技术栈

Python 3.11 · FastAPI · LangGraph · Qdrant · PostgreSQL · Redis · React 19 · Vite · Tailwind CSS 4 · RAGAS · Langfuse

## 开发路线

| Phase | 周期 | 交付 |
|-------|------|------|
| P1 | W1–2 | Auth、文档索引、Baseline RAG |
| P2 | W3–4 | LangGraph Agent、Hybrid 检索 |
| P3 | W5–6 | 多租户、版本感知、限流 |
| P4 | W7–8 | RAGAS、Docker、面试就绪 |

## Benchmark（目标）

| 模式 | faithfulness | context_precision | avg_latency |
|------|-------------|-------------------|-------------|
| Baseline RAG | 0.72 | 0.61 | 1.2s |
| Agentic RAG | 0.88 | 0.79 | 2.8s |

跑分方法与 Golden QA：[docs/eval-benchmark.md](docs/eval-benchmark.md)

## License

MIT — see [LICENSE](LICENSE)
