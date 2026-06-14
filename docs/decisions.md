# BizMind — 已定工程决策

> **状态：** 定稿（编码前锁定）  
> **日期：** 2026-06-14  
> 若变更须更新本文并视情况新增 [ADR](./adr/)。

---

## 1. 文档索引（异步）

| 项 | 决策 |
|----|------|
| **P1** | FastAPI `BackgroundTasks` 执行 parse → chunk → embed → upsert |
| **P3 可选** | 若队列积压再引入 ARQ/Celery |
| **状态查询** | 客户端轮询 `GET /documents/{id}`；WebSocket 不在 v1 |

---

## 2. 租户与 Demo

| 项 | 决策 |
|----|------|
| **P1 Demo** | 单租户 `Demo Corp` + `scripts/seed_demo_docs.py` 预置文档 |
| **注册** | 保留 `/auth/register`；新用户默认创建新 tenant（`tenant_name` 可选） |
| **多租户测试** | P3 集成测试覆盖 cross-tenant 404 |

---

## 3. 文档删除与版本

| 项 | 决策 |
|----|------|
| **删除文档** | ** bump `documents_version`**，并 mark 相关 threads stale |
| **删除向量** | 按 `document_id` + `tenant_id` 删除 Qdrant points |
| **物理删除** | v1 物理删除 PG 行与文件，不做 soft delete |

---

## 4. 认证

| 项 | 决策 |
|----|------|
| **JWT** | 仅 access token，过期 **24h** |
| **Refresh token** | **v1 不做** |
| **算法** | HS256 + `SECRET_KEY` |

---

## 5. P1 默认 AI 栈（降复杂度）

| 项 | P1 | P2+ |
|----|-----|-----|
| Embedding | OpenAI 兼容 API（云端） | 可选本地 BGE-M3 |
| Retrieval | Dense only（Baseline） | Hybrid + BM25 |
| Rerank | **关闭** | 开启 bge-reranker 或 Cohere |
| Agent | **关闭**（Baseline chat only） | LangGraph 全图 |
| Web Search | **关闭** | P3 可选 Tavily |

---

## 6. API 与文档权威

| 项 | 决策 |
|----|------|
| **OpenAPI** | **Code-first**：FastAPI 自动生成 `/docs` |
| **设计文档** | `docs/api-spec.md` 为设计参考；冲突以代码为准并回写 md |

---

## 7. 端口与联调

| 环境 | 前端 | 后端 |
|------|------|------|
| **本地开发** | Vite `5173`，proxy → `8000` | `8000` |
| **Docker Compose** | nginx `3000` 反代 `/api` | `8000`（内部） |

---

## 8. 包管理与锁文件

| 项 | 决策 |
|----|------|
| Python | **uv** + `uv.lock` 提交仓库 |
| Node | **npm** + `package-lock.json` 提交仓库 |
| 依赖升级 | 独立 PR，注明安全/功能原因 |

---

## 9. 测试与 CI

| 项 | 决策 |
|----|------|
| **CI** | 每次 push/PR：ruff、mypy（warning 模式至 P1 末）、pytest |
| **覆盖率 fail** | 脚手架阶段 `--cov-fail-under=0`；P1 结束升至 50，P2 升至 70 |
| **LLM** | CI 使用 mock，不调用真实 API |

---

## 10. 数据与免责声明

| 项 | 决策 |
|----|------|
| **Demo 文档** | 虚构内容，仅用于演示；见 `data/demo_docs/DISCLAIMER.md` |
| **seed 脚本** | 幂等：已存在同 hash 文档则 skip |
| **Golden QA** | 与 demo 文档路径一致 |

---

## 11. 已知实现偏差

| 项 | 文档 | 当前代码 | 计划 |
|----|------|----------|------|
| Parent-Child 分块 | ADR-003 | 段落 chunk（`chunker.py`） | P2 收尾或修订 ADR |
| P1 无 Agent | decisions §5 | P2 Agent 已合并进 main | 以 progress.md 为准 |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-14 | 编码前定稿 |
