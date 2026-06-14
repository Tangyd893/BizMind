# BizMind — 项目完成度报告

> **版本：** v0.2-progress  
> **更新日期：** 2026-06-14  
> **代码基线：** `main`（Post-P1/P2 主体实现）

---

## 1. 总览

| 维度 | 完成度 | 说明 |
|------|--------|------|
| **P1 Baseline RAG** | **~95%** | Auth、文档索引、Baseline SSE、前端三页、Docker 已就绪 |
| **P2 Agent + Hybrid** | **~85%** | LangGraph 全图、Hybrid 检索、Agent SSE；Parent-Child 分块未落地 |
| **P3 生产特性** | **~55%** | 多租户、版本 stale、限流、Web Fallback 已有；Embedding 缓存 / 跨租户测试缺 |
| **P4 评测包装** | **~35%** | Eval API + RAGAS service（Baseline）；无跑分结果、无 Langfuse、无 Eval UI |
| **测试与 CI** | **~45%** | 覆盖率 **47%**（目标 P1: 50%）；集成测试依赖本地 PG |
| **文档** | **~90%** | 设计文档齐全；benchmark 仍为占位 |

**当前可演示：** 注册/登录 → 上传或 seed 文档 → Baseline / Agent 流式对话 → 引用与 stale 标记。  
**尚不可演示：** RAGAS 对比表、Langfuse trace、Eval 面板、完整 Golden QA 回归。

---

## 2. Phase 任务状态

### P1 — Baseline RAG MVP

| ID | 任务 | 状态 | 备注 |
|----|------|------|------|
| P1-01 | 后端脚手架 + health | ✅ | `app/main.py`, structlog, 异常处理 |
| P1-02 | Alembic 初始迁移 | ✅ | `001_initial_schema.py` |
| P1-03 | Auth JWT | ✅ | `auth.py` + `test_auth.py`（需 PG 运行） |
| P1-04 | RBAC + admin | ✅ | `rbac.py`, `admin.py` |
| P1-05 | 文档上传 | ✅ | mime/大小校验 |
| P1-06 | BackgroundTasks 索引 | ✅ | `indexing_service.py` |
| P1-07 | version bump + 列表/删 | ✅ | `document_service.py` |
| P1-08 | Dense retriever | ✅ | `retriever.retrieve()`；无独立 `baseline.py` |
| P1-09 | Thread CRUD | ✅ | `threads.py` |
| P1-10 | Baseline SSE | ✅ | `/chat/baseline/stream` |
| P1-11 | seed_demo_docs | ✅ | 幂等 + Demo 账号 |
| P1-12 | 前端 Login/Docs/Chat | ✅ | 无 Eval 页 |
| P1-13 | Docker Compose | ✅ | 全栈 compose |
| P1-14 | 覆盖率 ≥50% | ⚠️ | 当前 **47%**；缺集成/E2E |

### P2 — Agent + Hybrid

| 项 | 状态 | 备注 |
|----|------|------|
| LangGraph 工作流 | ✅ | `agent/graph.py` 全节点 |
| Agent SSE + agent_step | ✅ | `/chat/stream`，前端 ChatPage |
| Hybrid Dense + BM25 | ✅ | `hybrid_retrieve()` |
| Cross-Encoder Rerank | ⚠️ | 仅 **Cohere API**（可选）；无本地 bge-reranker |
| Parent-Child Chunking | ❌ | `chunker.py` 仍为段落合并；ADR-003 未完全实现 |
| Prompt 外置 | ✅ | `agent/prompts/*.txt`, `*.j2` |
| Agent 节点单测 | ❌ | 无 `test_agent_nodes.py` |

### P3 — 生产特性

| 项 | 状态 | 备注 |
|----|------|------|
| 多租户 PG + Qdrant filter | ✅ | payload `tenant_id` |
| documents_version + is_stale | ✅ | bump + 前端 ⚠ 标记 |
| Redis Rate Limit | ✅ | `RateLimitMiddleware` |
| Redis Embedding 缓存 | ❌ | 未实现 |
| Tavily Web Fallback | ✅ | `web_search.py` |
| 跨租户集成测试 | ❌ | test-plan TC-SEC-* 未写 |
| PDF 解析 | ❌ | 仅 Markdown 文本读取 |

### P4 — 评测与包装

| 项 | 状态 | 备注 |
|----|------|------|
| Golden QA 数据集 | ⚠️ | **12 / 20** 条（`data/golden_qa.jsonl`） |
| Demo 文档三类 | ✅ | his / erp / workpal 各 1 份 |
| RAGAS eval API | ⚠️ | `eval_service.py` 仅跑 **Baseline**；`mode=agent` 未接通 |
| `scripts/eval_rag.py` | ❌ | CLI 仍为 stub |
| README benchmark 表 | ❌ | 仍为设计占位数值 |
| Langfuse | ❌ | 无 compose profile / span 埋点 |
| Eval 前端页 | ❌ | 无 `EvalPage.tsx` |
| 面试文档 | ✅ | `interview-talking-points.md` 已写 |

---

## 3. 成功标准对照（项目设计 §1.5）

| 标准 | 状态 |
|------|------|
| GitHub 公开 + README + Docker 一键启动 | ✅ |
| ≥3 类样例文档 + ≥20 Golden QA | ⚠️ 文档 ✅ / QA **12 条** |
| LangGraph 可演示（grade / critique 分支） | ✅ |
| RAGAS 可复现 + README benchmark | ❌ |
| 多租户隔离 + 版本感知对话 | ✅ 实现 / ⚠️ 测试不足 |
| 10 分钟完整 Demo | ⚠️ 依赖 LLM Key 与 `seed` |

---

## 4. API 实现清单

| 模块 | 路径 | 状态 |
|------|------|------|
| Health | `GET /health` | ✅ |
| Auth | `/auth/register`, `/login`, `/me` | ✅ |
| Documents | upload, list, get, delete | ✅ |
| Threads | create, list, messages | ✅ |
| Chat | `/chat/baseline/stream`, `/chat/stream` | ✅ |
| Eval | `/eval/run`, `/eval/results` | ⚠️ Baseline only |
| Admin | `/admin/users` | ✅ 占位 |

详见 [api-spec.md](./api-spec.md)；**OpenAPI 以 `/docs` 为准**。

---

## 5. 前端页面

| 页面 | 路径 | 状态 |
|------|------|------|
| Login | `/login` | ✅ |
| Register | `/register` | ✅ |
| Chat | `/chat` | ✅ Agent + Baseline 切换、SSE、stale |
| Documents | `/documents` | ✅ 上传 + 列表 |
| Eval Dashboard | — | ❌ 未实现 |

---

## 6. 测试与质量

| 指标 | 当前 | 目标 |
|------|------|------|
| Backend 覆盖率 | **47%** | P1: 50% → P2: 70% |
| 单元测试 | `test_chunker` 等 9 passed | — |
| 集成测试 | `test_auth` 12 errors（无 PG） | CI 有 services |
| 前端测试 | 1 placeholder | 待补充 |

**本地跑全绿：** 先 `make infra-up` + `make migrate`，再 `uv run pytest`。

---

## 7. 与设计决策的偏差

| 决策 | 文档 | 实际 | 建议 |
|------|------|------|------|
| Parent-Child 分块 | ADR-003 | 段落 chunk | P2 收尾或更新 ADR |
| P1 无 Rerank | decisions.md | P2 已加 Hybrid | 文档已超前，保持 |
| eval CLI | eval-benchmark.md | service 已有，CLI stub | 接通 `eval_rag.py` |
| Golden QA ≥20 | eval-benchmark.md | 12 条 | 补 8 条 |

---

## 8. 建议下一步（优先级）

1. **P1-14** — 补 auth/document 集成测试，覆盖率过 50%
2. **Golden QA** — 扩至 20 条，接通 agent eval mode
3. **RAGAS 跑分** — 真实 LLM 跑一轮，更新 README benchmark
4. **Parent-Child chunker** — 对齐 ADR-003
5. **EvalPage** + Langfuse（P4）
6. **跨租户测试** — TC-SEC-01/02

---

## 9. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-14 | 首版完成度审计（相对 v0.1-scaffold） |
