# BizMind — 开发指南

> **版本：** v0.1  
> **关联：** [项目设计 §4](./项目设计.md#4-目录结构) · [deployment](./deployment.md)

---

## 1. 开发环境要求

| 工具 | 版本 |
|------|------|
| Python | 3.11+ |
| Node.js | 20+ |
| uv 或 Poetry | 最新 |
| Docker | 24+ |
| Git | 2.40+ |

推荐 IDE：VS Code / Cursor，安装 Ruff、Pylance、ESLint 插件。

---

## 2. 首次 setup

```bash
git clone https://github.com/<you>/BizMind.git
cd BizMind
cp .env.example .env

# 基础设施
docker compose up -d postgres redis qdrant

# Backend
cd backend
uv sync                    # 或 poetry install
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000

# Frontend（新终端）
cd frontend
npm install
npm run dev                # http://localhost:5173
```

前端 dev 需在 `vite.config.ts` 配置 proxy 到 `localhost:8000`。

---

## 3. 目录与模块约定

```
backend/app/
├── api/          # 薄路由，仅 HTTP
├── services/     # 业务用例
├── rag/          # 检索管道（无 Agent 逻辑）
├── agent/        # LangGraph（无直接 ORM）
├── models/       # SQLAlchemy
├── schemas/      # Pydantic
└── core/         # 安全、日志、限流
```

**禁止：**

- 在 `api/` 写 SQL 或调用 Qdrant
- 在 `agent/nodes/` 直接 `session.query`
- 硬编码 magic number（用 `config.py`）

---

## 4. 分支与提交

### 4.1 Git 分支

```
main          ← 稳定可演示
develop       ← 日常集成
feature/*     ← 功能分支
release/v0.x  ← 发布候选
```

### 4.2 Conventional Commits

```
feat: add hybrid retriever with RRF fusion
fix: tenant filter on document delete
docs: update api-spec SSE events
test: agent grade low path
refactor: extract embedding cache to redis
```

### 4.3 PR 要求

- CI 全绿
- 关联需求 ID（如 FR-CHAT-02）
- 公开 service / agent node 需 docstring

---

## 5. 代码规范

| 范围 | 工具 | 命令 |
|------|------|------|
| Python format/lint | Ruff | `ruff check . && ruff format .` |
| Python types | mypy | `mypy app/` |
| Frontend | ESLint + Prettier | `npm run lint` |

---

## 6. 本地测试

```bash
cd backend
uv run pytest tests/ -q
uv run pytest tests/unit/test_retriever.py -v
uv run pytest --cov=app --cov-report=term-missing
```

集成测试需本地 PG/Redis/Qdrant 或 pytest-docker。

---

## 7. 常用开发任务

### 7.1 新增 API 端点

1. `schemas/` 定义 request/response
2. `services/` 实现逻辑
3. `api/v1/` 注册路由
4. `tests/integration/` 添加用例
5. 更新 [api-spec.md](./api-spec.md)

### 7.2 新增 Agent 节点

1. `agent/nodes/` 实现 node 函数
2. `agent/prompts/` 添加模板
3. `agent/graph.py` 注册节点与边
4. `tests/unit/test_agent_nodes.py` mock 测试
5. 更新 [agent-workflow.md](./agent-workflow.md)

### 7.3 数据库变更

```bash
uv run alembic revision --autogenerate -m "add eval_runs table"
uv run alembic upgrade head
```

同步更新 [database-schema.md](./database-schema.md)。

---

## 8. 调试技巧

| 场景 | 方法 |
|------|------|
| Agent 路径 | 日志 `route`、`retrieval_score`；Langfuse trace |
| 检索质量 | 脚本单独调用 `Retriever.hybrid_search` |
| SSE | curl `-N` 或 Postman stream |
| Qdrant | `http://localhost:6333/dashboard` |

---

## 9. Phase 开发顺序

| Phase | 周期 | 重点 |
|-------|------|------|
| P1 | W1–2 | Auth、上传索引、Baseline、最小 UI |
| P2 | W3–4 | LangGraph、Hybrid、SSE |
| P3 | W5–6 | 多租户、版本感知、限流 |
| P4 | W7–8 | RAGAS、Langfuse、README、面试 doc |

严格按 Phase 交付，避免 scope 膨胀。

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-14 | 初始开发指南 |
