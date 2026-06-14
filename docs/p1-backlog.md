# BizMind — P1 任务拆解（Baseline RAG MVP）

> **周期：** 第 1–2 周  
> **目标：** Auth、文档上传索引、Baseline RAG、最小 UI  
> **关联：** [decisions.md](./decisions.md) · [requirements.md](./requirements.md)

---

## 里程碑

**Tag：** `v0.1-baseline-rag`  
**门禁：** P1 DoD + [test-plan](./test-plan.md) TC-AUTH/DOC/CHAT baseline 用例通过

---

## 任务列表

| ID | 任务 | 依赖 | 交付物 | FR |
|----|------|------|--------|-----|
| P1-01 | 后端脚手架：FastAPI、config、health、structlog | — | `app/main.py`, `/health` | FR-OPS-01 |
| P1-02 | PostgreSQL + Alembic 初始迁移 | P1-01 | tenants, users, documents, threads, messages | — |
| P1-03 | Auth：register / login / me + JWT | P1-02 | `api/v1/auth.py`, tests | FR-AUTH-* |
| P1-04 | RBAC 依赖 + admin 占位 | P1-03 | `dependencies.py`, `core/rbac.py` | FR-AUTH-05 |
| P1-05 | 文档上传 + 本地存储 + mime 校验 | P1-03 | `POST /documents/upload` | FR-DOC-01,07 |
| P1-06 | BackgroundTasks 索引管道 | P1-05 | parse MD → chunk → embed → Qdrant | FR-DOC-02,03 |
| P1-07 | documents_version bump + 列表/删除 | P1-06 | GET/DELETE documents | FR-DOC-04,05,06 |
| P1-08 | Baseline RAG retriever（dense only） | P1-06 | `rag/baseline.py`, `retriever.py` | — |
| P1-09 | Thread CRUD + 消息历史 | P1-03 | `threads` API | FR-CHAT-01,04 |
| P1-10 | SSE Baseline chat | P1-08, P1-09 | `POST /chat/baseline/stream` | FR-CHAT-02,05 |
| P1-11 | seed_demo_docs.py 幂等导入 | P1-06 | `data/demo_docs` 可索引 | — |
| P1-12 | 前端：Login + Documents + Chat 最小页 | P1-10 | Vite pages + SSE hook | — |
| P1-13 | Docker Compose 全栈 smoke | P1-01~12 | `docker compose up` 可 Demo | — |
| P1-14 | CI 覆盖率升至 50% | P1-03~10 | `--cov-fail-under=50` | NFR-MAINT-01 |

---

## 建议 PR 顺序

```
PR-1: P1-01 + P1-02 + CI 基础设施
PR-2: P1-03 + P1-04（Auth）
PR-3: P1-05 + P1-06 + P1-07（文档管道）
PR-4: P1-08 + P1-09 + P1-10（Baseline chat）
PR-5: P1-11 + P1-12 + P1-13（Demo + UI + Docker）
PR-6: P1-14（测试补全）
```

---

## 每个任务验收标准（摘要）

### P1-03 Auth

- [ ] 注册返回 JWT；重复邮箱 409
- [ ] `/auth/me` 需 Bearer token
- [ ] 密码 bcrypt 存储

### P1-06 索引

- [ ] MD 文件 pending → indexed
- [ ] Qdrant 有 payload（tenant_id, document_id）
- [ ] 失败时 status=failed + error_message

### P1-10 Baseline Chat

- [ ] SSE：token、citation、done
- [ ] citations 含 document_id
- [ ] mock LLM 集成测试通过

### P1-12 前端

- [ ] 登录后可见文档列表
- [ ] Chat 页流式显示回答

---

## GitHub Issues 标题模板

```
[P1-03] feat(auth): JWT register login and me endpoint
[P1-06] feat(doc): background indexing with qdrant upsert
```

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-14 | P1 backlog 初版 |
