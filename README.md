# BizMind

**Business Mind** — 面向企业私有文档的多租户 Agentic RAG 平台。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **当前状态：** 开发中（v0.2-progress）— P1 基本完成，P2 Agent 已可演示；详见 [docs/progress.md](docs/progress.md)

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
| [docs/progress.md](docs/progress.md) | **项目完成度报告** |
| [docs/项目设计.md](docs/项目设计.md) | 总体设计 |
| [docs/requirements.md](docs/requirements.md) | 需求规格 (SRS) |
| [docs/architecture.md](docs/architecture.md) | 系统架构 |
| [docs/api-spec.md](docs/api-spec.md) | API 规范 |
| [docs/agent-workflow.md](docs/agent-workflow.md) | LangGraph 工作流 |
| [docs/development-guide.md](docs/development-guide.md) | 开发指南 |

## 技术栈

Python 3.11 · FastAPI · LangGraph · Qdrant · PostgreSQL · Redis · React 19 · Vite · Tailwind CSS 4 · RAGAS · Langfuse

## 开发路线

| Phase | 交付 | 状态 |
|-------|------|------|
| P1 | Auth、文档索引、Baseline RAG、最小 UI | ~95% |
| P2 | LangGraph Agent、Hybrid 检索 | ~85% |
| P3 | 多租户、版本感知、限流 | ~55% |
| P4 | RAGAS、Langfuse、面试就绪 | ~35% |

完整对照：[docs/progress.md](docs/progress.md)

## Benchmark

> 设计目标占位；真实跑分待 P4 完成。Eval API 已支持 Baseline RAGAS。

| 模式 | faithfulness | context_precision | avg_latency |
|------|-------------|-------------------|-------------|
| Baseline RAG | _待测_ | _待测_ | _待测_ |
| Agentic RAG | _待测_ | _待测_ | _待测_ |

跑分方法：[docs/eval-benchmark.md](docs/eval-benchmark.md)

## License

MIT — see [LICENSE](LICENSE)
