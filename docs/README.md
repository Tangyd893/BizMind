# BizMind 文档

| 文档 | 说明 |
|------|------|
| [design.md](./design.md) | 总体设计：定位、架构、数据模型、里程碑 |
| [api.md](./api.md) | REST + SSE 接口约定（实现以 `/docs` OpenAPI 为准） |
| [dev.md](./dev.md) | 本地开发、部署、代码规范 |
| [todo0619.md](./todo0619.md) | 完成度与待办（当前） |
| [todo0616.md](./todo0616.md) | v0.4 收尾审计（已归档） |

根目录 [README.md](../README.md) · 协作 [CONTRIBUTING.md](../CONTRIBUTING.md)

## 仓库结构

```
BizMind/
├── backend/           # FastAPI · LangGraph · RAG
│   ├── app/
│   │   ├── api/       # HTTP 路由
│   │   ├── services/  # 业务逻辑
│   │   ├── rag/       # 检索与分块
│   │   ├── agent/     # LangGraph 工作流
│   │   └── models/    # ORM
│   ├── alembic/       # 数据库迁移
│   └── tests/
├── frontend/          # React 19 · Vite · Tailwind
│   └── src/
│       ├── pages/     # Login · Chat · Documents · Eval · Admin
│       └── api/       # 客户端与 SSE
├── data/
│   ├── demo_docs/     # HIS / ERP / WorkPal / HR（含 PDF）
│   ├── eval-results.json  # RAGAS 最新跑分
│   └── golden_qa.jsonl
├── scripts/           # seed_demo_docs · eval_rag · dev.ps1
├── docs/              # 本目录
├── docker-compose.yml
└── Makefile
```
