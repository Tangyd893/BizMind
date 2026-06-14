# BizMind — 测试计划

> **版本：** v0.1  
> **关联：** [requirements](./requirements.md) · [项目设计 §7.3](./项目设计.md#73-测试策略)

---

## 1. 测试目标

- 保证多租户隔离零泄漏
- 保证 RAG 管道与 Agent 条件边行为可回归
- CI 不依赖外部 LLM API（mock）
- 核心模块覆盖率 ≥ 70%

---

## 2. 测试范围

| 范围内 | 范围外（v1） |
|--------|--------------|
| Backend API、RAG、Agent | 前端 E2E（Playwright，可选 nightly） |
| 单元 + 集成测试 | 真实 LLM 集成测试（手动 / nightly） |
| RAGAS 批跑脚本 | 性能压测（k6，v1.1） |
| Docker healthcheck | 安全渗透测试 |

---

## 3. 测试分层

```mermaid
pyramid
    title Test Pyramid
    "E2E / RAGAS (few)" : 10
    "Integration (moderate)" : 25
    "Unit (many)" : 65
```

| 层级 | 工具 | 目录 | 运行频率 |
|------|------|------|----------|
| 单元 | pytest | `backend/tests/unit/` | 每次 PR |
| 集成 | pytest + httpx | `backend/tests/integration/` | 每次 PR |
| Agent 图 | pytest + mock LLM | `backend/tests/unit/test_agent_graph.py` | 每次 PR |
| 前端单元 | Vitest | `frontend/src/**/*.test.tsx` | 每次 PR |
| RAGAS | scripts/eval_rag.py | `data/golden_qa.jsonl` | 发布前 / nightly |

---

## 4. 功能测试用例

### 4.1 认证 (FR-AUTH)

| ID | 用例 | 步骤 | 期望 |
|----|------|------|------|
| TC-AUTH-01 | 注册成功 | POST /auth/register 合法数据 | 201 + JWT |
| TC-AUTH-02 | 重复邮箱 | 同邮箱注册两次 | 409 CONFLICT |
| TC-AUTH-03 | 登录失败 | 错误密码 | 401 |
| TC-AUTH-04 | 无 token 访问 | GET /documents 无头 | 401 |
| TC-AUTH-05 | 过期 token | 使用 exp 已过 JWT | 401 |

### 4.2 文档 (FR-DOC)

| ID | 用例 | 步骤 | 期望 |
|----|------|------|------|
| TC-DOC-01 | 上传 PDF | multipart 合法 PDF | 202 pending |
| TC-DOC-02 | 索引完成 | mock embed + qdrant | status=indexed, chunk_count>0 |
| TC-DOC-03 | 超大文件 | 21MB 上传 | 413 |
| TC-DOC-04 | 非法类型 | .exe 上传 | 415 |
| TC-DOC-05 | 版本 bump | 索引第二个文档 | documents_version +1 |
| TC-DOC-06 | 租户隔离 | Tenant B 查 Tenant A doc id | 404 |
| TC-DOC-07 | 删除 | DELETE /documents/{id} | 204, Qdrant 无对应 points |

### 4.3 对话 (FR-CHAT)

| ID | 用例 | 步骤 | 期望 |
|----|------|------|------|
| TC-CHAT-01 | SSE 流式 | POST /chat/stream | 收到 token + done |
| TC-CHAT-02 | Citations | mock 检索有结果 | citation 事件含 doc_id |
| TC-CHAT-03 | 多轮 | 同 thread 两问 | 历史 messages 两条 user |
| TC-CHAT-04 | Stale thread | bump version 后 GET thread | is_stale=true |
| TC-CHAT-05 | Baseline | /chat/baseline/stream | 无 agent_step |
| TC-CHAT-06 | Rate limit | 超限请求 | 429 |

### 4.4 Agent 图

见 [agent-workflow §9](./agent-workflow.md#9-测试用例矩阵)（AGT-01 ~ AGT-07）。

### 4.5 评测 (FR-EVAL)

| ID | 用例 | 步骤 | 期望 |
|----|------|------|------|
| TC-EVAL-01 | 非 admin 触发 | user 角色 POST /eval/run | 403 |
| TC-EVAL-02 | 跑分入库 | admin + mock RAGAS | eval_runs 有 metrics |
| TC-EVAL-03 | 结果列表 | GET /eval/results | 分页正确 |

---

## 5. 非功能测试

### 5.1 安全

| ID | 用例 | 期望 |
|----|------|------|
| TC-SEC-01 | 跨租户 thread 访问 | 404 |
| TC-SEC-02 | Qdrant filter 绕过尝试 | 仅返回本 tenant chunks |
| TC-SEC-03 | SQL 注入 email | 400，无 DB 异常 |

### 5.2 性能（手动）

| ID | 指标 | 方法 |
|----|------|------|
| TC-PERF-01 | 首 token < 2s | 本地 Docker + 秒表 / Langfuse |
| TC-PERF-02 | 10 页 PDF 索引 < 30s | upload + 等待 indexed |

---

## 6. Mock 策略

### 6.1 LLM Mock

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel

router_llm = FakeListChatModel(responses=['{"route": "rag"}'])
grade_llm = FakeListChatModel(responses=['{"score": 0.9, "reason": "ok"}'])
```

### 6.2 HTTP Mock

- `pytest-httpx` mock Embedding / Tavily
- Qdrant：测试容器或 `qdrant-client` in-memory（若可用）

### 6.3 测试数据库

- pytest fixture：`TEST_DATABASE_URL` 指向临时 PG
- 每测试 function 级 transaction rollback 或 alembic upgrade + truncate

---

## 7. CI 配置

```yaml
# .github/workflows/ci.yml
jobs:
  backend-test:
    services:
      postgres: ...
      redis: ...
      qdrant: ...
    steps:
      - run: ruff check && ruff format --check
      - run: mypy app/
      - run: pytest tests/ -q --cov=app --cov-fail-under=70

  frontend-test:
    steps:
      - run: npm ci && npm run lint && npm run test

  docker-smoke:
    steps:
      - run: docker compose build
      - run: docker compose up -d
      - run: curl -f http://localhost:8000/api/v1/health
```

---

## 8. 测试数据

| 资源 | 路径 |
|------|------|
| 样例 PDF/MD | `backend/tests/fixtures/sample_docs/` |
| Golden QA | `data/golden_qa.jsonl` |
| Demo 文档 | `data/demo_docs/{his,erp,workpal}/` |

---

## 9. 退出准则（Phase 门禁）

| Phase | 门禁 |
|-------|------|
| P1 | TC-AUTH-* + TC-DOC-01~03 + Baseline SSE 通过 |
| P2 | AGT-* 全通过 + Hybrid retriever 单测 |
| P3 | TC-SEC-* + stale + rate limit 通过 |
| P4 | RAGAS 达到 [eval-benchmark](./eval-benchmark.md) 目标 + Docker smoke |

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-14 | 初始测试计划 |
