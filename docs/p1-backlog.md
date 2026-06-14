# BizMind — P1 任务拆解（Baseline RAG MVP）

> **周期：** 第 1–2 周  
> **目标：** Auth、文档上传索引、Baseline RAG、最小 UI  
> **状态：** **基本完成**（见 [progress.md](./progress.md)）  
> **关联：** [decisions.md](./decisions.md) · [requirements.md](./requirements.md)

---

## 里程碑

**Tag：** `v0.1-baseline-rag`（待打）  
**门禁：** P1 DoD + [test-plan](./test-plan.md) TC-AUTH/DOC/CHAT baseline 用例通过  
**阻塞：** 覆盖率 47% < 50%；集成测试需本地 PostgreSQL

---

## 任务列表

| ID | 任务 | 状态 | 交付物 | FR |
|----|------|------|--------|-----|
| P1-01 | 后端脚手架：FastAPI、config、health、structlog | ✅ | `app/main.py`, `/health` | FR-OPS-01 |
| P1-02 | PostgreSQL + Alembic 初始迁移 | ✅ | `001_initial_schema.py` | — |
| P1-03 | Auth：register / login / me + JWT | ✅ | `api/v1/auth.py`, tests | FR-AUTH-* |
| P1-04 | RBAC 依赖 + admin 占位 | ✅ | `dependencies.py`, `core/rbac.py` | FR-AUTH-05 |
| P1-05 | 文档上传 + 本地存储 + mime 校验 | ✅ | `POST /documents/upload` | FR-DOC-01,07 |
| P1-06 | BackgroundTasks 索引管道 | ✅ | MD → chunk → embed → Qdrant | FR-DOC-02,03 |
| P1-07 | documents_version bump + 列表/删除 | ✅ | GET/DELETE documents | FR-DOC-04,05,06 |
| P1-08 | Baseline RAG retriever（dense only） | ✅ | `rag/retriever.py` | — |
| P1-09 | Thread CRUD + 消息历史 | ✅ | `threads` API | FR-CHAT-01,04 |
| P1-10 | SSE Baseline chat | ✅ | `POST /chat/baseline/stream` | FR-CHAT-02,05 |
| P1-11 | seed_demo_docs.py 幂等导入 | ✅ | Demo 账号 + 文档 | — |
| P1-12 | 前端：Login + Documents + Chat | ✅ | 三页 + SSE | — |
| P1-13 | Docker Compose 全栈 smoke | ✅ | `docker-compose.yml` | — |
| P1-14 | CI 覆盖率升至 50% | ⚠️ | 当前 47% | NFR-MAINT-01 |

---

## 验收标准（当前）

### P1-03 Auth

- [x] 注册返回 JWT；重复邮箱 409
- [x] `/auth/me` 需 Bearer token
- [x] 密码 bcrypt 存储

### P1-06 索引

- [x] MD 文件 pending → indexed
- [x] Qdrant payload（tenant_id, document_id）
- [x] 失败时 status=failed + error_message

### P1-10 Baseline Chat

- [x] SSE：token、citation、done
- [x] citations 含 document_id
- [ ] mock LLM 集成测试（待补）

### P1-12 前端

- [x] 登录后可见文档列表
- [x] Chat 页流式显示回答

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-14 | P1 backlog 初版 |
| 2026-06-14 | 对照代码更新任务状态与验收勾选 |
