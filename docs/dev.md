# BizMind — 开发与部署

> 环境变量见根目录 `.env.example` · 协作流程见 [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 1. 环境要求

Python 3.11+ · Node 20+ · Docker 24+ · uv（推荐）

---

## 2. 本地开发

```bash
git clone https://github.com/Tangyd893/BizMind.git
cd BizMind
cp .env.example .env          # Windows: copy .env.example .env

make infra-up                 # postgres + redis + qdrant
make migrate
make dev-backend              # :8000
make dev-frontend             # :5173，/api 代理到后端
```

Demo 数据：

```bash
cd backend && uv run python ../scripts/seed_demo_docs.py
# 账号 demo@bizmind.local / DemoPass123!
```

---

## 3. Docker 全栈

```bash
docker compose up -d --build
curl http://localhost:8000/api/v1/health
# 前端 http://localhost:3000
```

---

## 4. 目录约定

| 层 | 职责 | 禁止 |
|----|------|------|
| `api/` | HTTP、鉴权、映射响应 | 业务逻辑、直接访问 Qdrant |
| `services/` | 用例编排、事务 | Agent 节点逻辑 |
| `rag/` | 解析、分块、检索 | 路由决策 |
| `agent/` | LangGraph 状态机 | 直接 ORM |

配置项统一进 `app/config.py`，禁止 magic number。

---

## 5. 代码规范

| 范围 | 工具 |
|------|------|
| Python | Ruff format/lint，`mypy app/` |
| Frontend | `npm run lint` |
| 提交 | Conventional Commits，如 `feat(agent): ...` |

公开 service / API / agent node 需 docstring。异常使用 `AppException`，错误码与 [api.md](./api.md) 一致。

---

## 6. 测试

```bash
cd backend
make infra-up && uv run alembic upgrade head   # 集成测试需要 PG
uv run pytest tests/ -q --cov=app
```

| 阶段 | 覆盖率目标 |
|------|------------|
| 当前 | ≥ 50% |
| P2 结束 | ≥ 70% |

CI 使用 mock LLM，不消耗 API 额度。

---

## 7. 变更检查清单

| 变更 | 须更新 |
|------|--------|
| API | `docs/api.md` + FastAPI 路由 |
| 表结构 | Alembic migration + `design.md` §5 |
| 环境变量 | `.env.example` |

---

## 8. 故障排查

| 现象 | 处理 |
|------|------|
| health 503 | 检查 `DATABASE_URL`、容器是否 healthy |
| 文档一直 pending | 查 backend 日志、LLM/Embedding Key |
| 检索无结果 | 确认 indexed、`tenant_id` filter |
| SSE 断开 | nginx 需 `X-Accel-Buffering: no` |

---

## 9. 已定实现决策（摘要）

| 项 | 决策 |
|----|------|
| 文档索引 | P1 用 `BackgroundTasks` |
| JWT | 仅 access token，24h |
| OpenAPI | code-first，`/docs` 为准 |
| 开发端口 | 前端 5173，API 8000；Docker 前端 3000 |
| Demo | 单租户 `Demo Corp` + seed 脚本 |

Parent-Child 分块已实现（`chunker.py`，ADR-003）。
