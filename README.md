# BizMind

**Business Mind** — 面向企业私有文档的多租户 Agentic RAG 平台。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **状态：** 开发中 · 待办见 [docs/todo0616.md](docs/todo0616.md)

## 特性

- **Agentic RAG** — LangGraph：Router → Retrieve → Grade → Rewrite → Generate → Critique
- **Hybrid Retrieval** — Dense + BM25 + 可选 Cohere Rerank
- **多租户隔离** — PostgreSQL + Qdrant payload filter
- **文档版本感知** — 知识库更新后 stale 会话提示
- **流式对话** — SSE + 引用溯源
- **评测** — Golden QA + RAGAS（Eval API / 前端 Eval 页）

## 架构

```
Web (React) ──SSE/REST──► FastAPI ──► LangGraph Agent
                              │              │
                              ▼              ▼
                         PostgreSQL    RAG (Qdrant)
                              │
                           Redis
```

## 快速开始

```bash
git clone https://github.com/Tangyd893/BizMind.git
cd BizMind
cp .env.example .env

make infra-up && make migrate
make dev-backend    # :8000
make dev-frontend   # :5173
```

Docker：`docker compose up -d --build` → http://localhost:3000

## 文档

| 文档 | 说明 |
|------|------|
| [docs/design.md](docs/design.md) | 总体设计 |
| [docs/api.md](docs/api.md) | API 规范 |
| [docs/dev.md](docs/dev.md) | 开发部署 |
| [docs/todo0616.md](docs/todo0616.md) | **待办清单** |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 协作流程 |

## 技术栈

Python 3.11 · FastAPI · LangGraph · Qdrant · PostgreSQL · Redis · React 19 · Vite · RAGAS

## License

MIT
