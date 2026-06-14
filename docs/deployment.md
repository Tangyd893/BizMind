# BizMind — 部署与运维指南

> **版本：** v0.1  
> **关联：** [architecture §10](./architecture.md#10-deployment-topology-docker-compose) · [项目设计 §3.3](./项目设计.md#33-部署架构docker-compose)

---

## 1. 部署方式概览

| 环境 | 方式 | 用途 |
|------|------|------|
| 本地开发 | Docker Compose + 热重载 | 日常开发 |
| 演示 / 面试 | Docker Compose 全栈 | 一键 Demo |
| 生产（未来） | K8s / 云 VM | 不在 v1 范围 |

---

## 2. 前置条件

- Docker Engine ≥ 24，Docker Compose v2
- 8GB+ 内存（含 rerank 模型时建议 16GB）
- LLM API Key（OpenAI 兼容）
- 可选：Tavily API Key、Langfuse 账号

---

## 3. 快速启动

```bash
# 1. 克隆仓库
git clone https://github.com/<you>/BizMind.git
cd BizMind

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY 等

# 3. 启动核心服务
docker compose up -d

# 4. 健康检查
curl http://localhost:8000/api/v1/health

# 5. 访问前端
open http://localhost:3000
```

### 3.1 导入 Demo 数据

```bash
docker compose exec backend python scripts/seed_demo_docs.py
```

### 3.2 启用可观测性（可选）

```bash
docker compose --profile observability up -d
# Langfuse UI: http://localhost:3001
```

---

## 4. Docker Compose 服务定义（设计稿）

| 服务 | 镜像 | 端口 | Volume |
|------|------|------|--------|
| frontend | build `./frontend` | 3000 | — |
| backend | build `./backend` | 8000 | `./data:/app/data` |
| postgres | postgres:16-alpine | 5432 | `pg_data` |
| qdrant | qdrant/qdrant:latest | 6333 | `qdrant_data` |
| redis | redis:7-alpine | 6379 | — |
| langfuse | langfuse images | 3001 | profile: observability |

**依赖顺序：** postgres, redis, qdrant → backend → frontend

---

## 5. 环境变量

完整列表见根目录 [`.env.example`](../.env.example)。

### 5.1 必填项

| 变量 | 说明 |
|------|------|
| `SECRET_KEY` | JWT 签名，≥ 32 字符随机串 |
| `LLM_API_KEY` | LLM 提供商密钥 |
| `DATABASE_URL` | PostgreSQL 连接串 |
| `QDRANT_URL` | Qdrant HTTP 地址 |
| `REDIS_URL` | Redis 连接串 |

### 5.2 国内模型示例

```env
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
EMBEDDING_MODEL=text-embedding-3-small
# 或本地 BGE：EMBEDDING_PROVIDER=local
```

---

## 6. 数据库迁移

```bash
# 容器内
docker compose exec backend alembic upgrade head

# 本地开发
cd backend && uv run alembic upgrade head
```

---

## 7. 日志

- 格式：JSON（structlog）
- 字段：`timestamp`, `level`, `request_id`, `user_id`, `tenant_id`, `message`
- 查看：`docker compose logs -f backend`

---

## 8. 备份与恢复

| 数据 | 方式 |
|------|------|
| PostgreSQL | `pg_dump` / volume snapshot |
| Qdrant | volume `qdrant_data` 或 snapshot API |
| 上传文件 | `./data` volume |

恢复后需保证 `documents_version` 与 Qdrant payload 一致；不一致时建议 re-index。

---

## 9. 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| health 503 postgres | DB 未就绪 | 等待 / 检查 DATABASE_URL |
| 文档一直 pending | LLM/Embedding 失败 | 查 backend 日志、API Key |
| 检索无结果 | Qdrant 空 / filter 错误 | 确认 indexed、tenant_id |
| SSE 断开 | nginx 缓冲 | 确认 `X-Accel-Buffering: no` |
| Rerank OOM | 内存不足 | 改用 Cohere API 或减小 batch |
| Rate limit 429 | 请求过快 | 调 MAX_REQUESTS 或等待 reset |

---

## 10. Demo 检查清单（面试前）

- [ ] `.env` 中 LLM Key 有效，余额充足
- [ ] `docker compose ps` 全部 healthy
- [ ] Demo 文档已 seed，≥ 3 类
- [ ] 测试账号可登录
- [ ] Agent 模式能流式输出 + 引用
- [ ] Baseline vs Agent 对比数字已写入 README
- [ ] 备用 base_url 已配置（防 API 抖动）
- [ ] 10 分钟 Demo 脚本演练一遍 → [interview-talking-points](./interview-talking-points.md)

---

## 11. 安全运维

- 禁止将 `.env` 提交 Git
- 生产环境更换默认 `SECRET_KEY`
- 演示账号使用弱密码仅限本地
- 定期轮换 API Key

---

## 12. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-14 | 初始部署指南 |
