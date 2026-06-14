# BizMind — 编码规范

> **版本：** v0.1  
> **关联：** [CONTRIBUTING.md](../CONTRIBUTING.md) · [development-guide.md](./development-guide.md)

---

## 1. Python（Backend）

### 1.1 通用

- Python **3.11+**，新代码全量 type hints
- 格式化与 lint：**Ruff**（line-length 100）
- 类型检查：**mypy strict** on `app/`（P1 前 mypy 可在 CI 为 continue-on-error）
- 公开函数、service 方法、agent node：**Google 风格 docstring**

### 1.2 异步约定

| 层级 | 约定 |
|------|------|
| API 路由 | `async def` |
| Service | **全 async**（`async def`） |
| DB | SQLAlchemy 2.0 **async session** |
| 同步 CPU 密集 | `asyncio.to_thread()` 包裹（PDF 解析等） |

### 1.3 模块与命名

```
app/api/v1/{resource}.py     # 路由，薄
app/services/{name}_service.py
app/models/{entity}.py
app/schemas/{entity}.py
app/rag/{component}.py
app/agent/nodes/{node}.py
tests/unit/test_{module}.py
tests/integration/test_{flow}.py
```

- 测试函数：`test_<场景>_<期望>`，例 `test_register_duplicate_email_returns_409`
- 常量：大写蛇形；配置项从 `Settings` 读取，禁止 magic number

### 1.4 依赖注入

统一入口（`app/dependencies.py`）：

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]: ...
async def get_current_user(...) -> User: ...
async def get_current_admin(user: User = Depends(get_current_user)) -> User: ...
```

路由层禁止直接 `SessionLocal()`。

### 1.5 异常与错误码

- 业务异常继承 `AppException(code, message, status_code)`
- `code` 与 [api-spec.md](./api-spec.md) 错误码枚举一致
- 全局 handler 输出统一 JSON：`{ "error": { "code", "message", "request_id" } }`

| 场景 | 异常类 | HTTP |
|------|--------|------|
| 参数无效 | `ValidationError` | 400 |
| 未登录 | `UnauthorizedError` | 401 |
| 非 admin | `ForbiddenError` | 403 |
| 跨租户/不存在 | `NotFoundError` | 404 |

### 1.6 日志（structlog）

每条请求日志**必须**包含：

- `request_id`
- `tenant_id`（若已认证）
- `user_id`（若已认证）

Agent 节点额外记录：`node`, `route`, `retrieval_score`, `latency_ms`。

### 1.7 分层禁令

| 禁止 | 原因 |
|------|------|
| `api/` 内写 SQL / Qdrant | 分层 |
| `agent/nodes/` 直接 ORM | 可测试性 |
| `rag/` 内 LLM 路由决策 | 职责分离 |

---

## 2. TypeScript（Frontend）

### 2.1 栈与工具

- React 19 + TypeScript strict
- ESLint + Prettier（2 空格，single quote，semi）
- 样式：Tailwind CSS 4

### 2.2 目录

```
src/
├── api/           # fetch client、SSE helper、types
├── components/
│   ├── ui/        # 无业务逻辑
│   ├── layout/
│   └── {feature}/ # chat、documents、eval
├── hooks/
├── pages/
└── types/
```

### 2.3 API Client

- 类型与 backend OpenAPI 对齐；P1 可手写，P2 考虑 openapi-typescript
- TanStack Query key：`['documents', 'list', { page }]` 格式
- SSE：统一 `useChatStream` hook，处理 `token|citation|done|error`

### 2.4 组件

- 页面只组合 feature 组件，不写 fetch 细节
- `components/ui` 不含 tenant/chat 等领域词

---

## 3. Git

### 3.1 Scope 列表

`auth` · `doc` · `rag` · `agent` · `chat` · `eval` · `admin` · `ci` · `docker` · `frontend`

### 3.2 示例

```
feat(auth): implement JWT login and register
feat(doc): add background indexing task
test(rag): dense retriever tenant filter
```

---

## 4. 数据库迁移

1. 修改 `app/models/`
2. `alembic revision --autogenerate -m "describe change"`
3. 人工 review 迁移脚本
4. 更新 `docs/database-schema.md`

禁止手改生产库 schema 而不写 migration。

---

## 5. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-14 | 初始编码规范 |
