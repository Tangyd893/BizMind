# BizMind — 开发与部署

> 环境变量见根目录 `.env.example` · 协作流程见 [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 1. 环境要求

Python 3.11+ · Node 20+ · Docker 24+ · uv（推荐）

**Windows 本地编译：** 部分 Python 依赖（如 `ragas` → `scikit-network`）需要 **MSVC 14+**。若 `uv sync` 报 `Microsoft Visual C++ 14.0 or greater is required`：

```powershell
# 一键安装（管理员 PowerShell，约 5–10 分钟）
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --accept-package-agreements --accept-source-agreements --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

安装后**新开终端**，或在运行 `uv` 前加载编译环境：

```powershell
cmd /c "`"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat`" && set PATH=$env:USERPROFILE\.local\bin;%PATH% && cd backend && uv sync --all-extras"
```

验证：`cl` 能输出版本信息即表示 MSVC 可用。

### 默认模型栈（无 GPT）

| 用途 | 默认 | 配置项 |
|------|------|--------|
| LLM | DeepSeek Chat | `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` |
| Embedding | SiliconFlow BGE-M3 | `EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL` / `EMBEDDING_MODEL` |
| Rerank | 本地 Dense+BM25 融合 | `RERANK_PROVIDER=local`；有 Key 可切 Cohere |

均为 **OpenAI 兼容 API**，无需 GPT 账号。RAGAS 评测在 DeepSeek 下 `answer_relevancy` / `context_*` 可能偏低（`n=1` 限制），**faithfulness ~0.70 为主要参考**。

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

### Langfuse 可观测（可选）

```bash
# 创建 Langfuse 数据库（首次）
docker compose up -d postgres
docker exec bizmind-postgres-1 psql -U bizmind -c "CREATE DATABASE bizmind_langfuse"

# 启动 Langfuse
docker compose -f docker-compose.yml -f docker-compose.observability.yml --profile observability up -d

# .env 中设置 LANGFUSE_ENABLED=true 并填入 UI 中的 Key
# 可选安装 SDK：cd backend && uv sync --extra observability
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
uv run pytest tests/ -q --cov=app --cov-fail-under=60   # 默认 SQLite，无需 Docker
```

可选：用 Docker PostgreSQL 跑集成测试（宿主机端口 **5433**，避免与本地 PostgreSQL 5432 冲突）：

```bash
make infra-up
docker exec bizmind-postgres-1 psql -U bizmind -d bizmind -c "CREATE DATABASE bizmind_test"
DATABASE_URL=postgresql+asyncpg://bizmind:bizmind@127.0.0.1:5433/bizmind_test \
  uv run pytest tests/ -q
```

| 阶段 | 覆盖率目标 |
|------|------------|
| v0.6（当前） | ≥ **60%**（CI 门槛；~94 tests） |
| 后续目标 | ≥ 70%（`eval_service` / `indexing` 集成路径） |

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
| Rerank 未生效 | 检查 `COHERE_API_KEY`；无 Key 时自动降级为 Dense(0.7)+BM25(0.3) 融合 |
| SSE 断开 | nginx 需 `X-Accel-Buffering: no` |
| Langfuse 未启动 | `docker compose -f docker-compose.yml -f docker-compose.observability.yml --profile observability up -d` |

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
