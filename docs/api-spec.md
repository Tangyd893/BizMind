# BizMind — API 接口规范

> **版本：** v0.1  
> **Base URL：** `/api/v1`  
> **OpenAPI：** 实现阶段由 FastAPI 自动生成 `/docs`  
> **关联：** [requirements](./requirements.md) · [项目设计 §6](./项目设计.md#6-api-设计概要)

---

## 1. 通用约定

### 1.1 协议与格式

| 项 | 约定 |
|----|------|
| 协议 | HTTPS（生产）；本地 HTTP |
| 请求体 | JSON（`Content-Type: application/json`），上传除外 |
| 响应体 | JSON，UTF-8 |
| 时间 | ISO 8601 UTC（`2026-06-14T08:00:00Z`） |
| ID | UUID v4 字符串 |

### 1.2 认证

除公开端点外，请求头必填：

```http
Authorization: Bearer <access_token>
```

JWT Payload 字段：

```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "role": "user",
  "exp": 1718352000
}
```

### 1.3 分页

列表接口统一 query 参数：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | int | 1 | 页码，从 1 开始 |
| `page_size` | int | 20 | 每页条数，最大 100 |

响应 wrapper：

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

### 1.4 错误响应

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable message",
    "details": [
      {"field": "email", "message": "invalid format"}
    ],
    "request_id": "req-uuid"
  }
}
```

### 1.5 错误码枚举

| HTTP | code | 说明 |
|------|------|------|
| 400 | `VALIDATION_ERROR` | 参数校验失败 |
| 401 | `UNAUTHORIZED` | 未登录或 token 无效 |
| 403 | `FORBIDDEN` | 无权限（如非 admin 访问 eval） |
| 404 | `NOT_FOUND` | 资源不存在或跨租户 |
| 409 | `CONFLICT` | 邮箱已注册等 |
| 413 | `PAYLOAD_TOO_LARGE` | 文件超过 20MB |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | 非 PDF/MD |
| 429 | `RATE_LIMIT` | 限流 |
| 500 | `INTERNAL_ERROR` | 服务器错误 |
| 503 | `SERVICE_UNAVAILABLE` | 依赖不可用 |

---

## 2. 公开端点

### 2.1 GET /health

健康检查，无需认证。

**Response 200:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "checks": {
    "postgres": "ok",
    "redis": "ok",
    "qdrant": "ok"
  }
}
```

**Response 503:** 任一依赖失败时 `status: "degraded"`。

---

## 3. 认证模块

### 3.1 POST /auth/register

**Request:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "tenant_name": "Demo Corp"
}
```

| 字段 | 规则 |
|------|------|
| email | 合法邮箱，唯一 |
| password | ≥ 8 字符，含字母与数字 |
| tenant_name | 可选；省略则创建个人租户 |

**Response 201:**

```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "user",
    "tenant_id": "uuid"
  },
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 3.2 POST /auth/login

**Request:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response 200:** 同 register 响应结构。

**Response 401:** `UNAUTHORIZED`

### 3.3 GET /auth/me

**Response 200:**

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "role": "user",
  "tenant_id": "uuid",
  "created_at": "2026-06-14T08:00:00Z"
}
```

---

## 4. 文档模块

### 4.1 POST /documents/upload

`multipart/form-data`

| 字段 | 类型 | 必填 |
|------|------|------|
| file | binary | 是 |

**允许类型：** `application/pdf`, `text/markdown`, `text/plain`（.md）

**Response 202:**

```json
{
  "id": "uuid",
  "filename": "his-manual.pdf",
  "mime_type": "application/pdf",
  "status": "pending",
  "created_at": "2026-06-14T08:00:00Z"
}
```

索引完成后 status 变为 `indexed`；客户端可轮询 `GET /documents/{id}` 或 WebSocket（v2）。

### 4.2 GET /documents

**Query:** `page`, `page_size`, `status`（可选 filter）

**Response 200:**

```json
{
  "items": [
    {
      "id": "uuid",
      "filename": "his-manual.pdf",
      "mime_type": "application/pdf",
      "status": "indexed",
      "chunk_count": 42,
      "documents_version": 3,
      "created_at": "2026-06-14T08:00:00Z",
      "indexed_at": "2026-06-14T08:00:30Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

### 4.3 GET /documents/{id}

**Response 200:** 单条 document 对象。

**Response 404:** 不存在或非本租户。

### 4.4 DELETE /documents/{id}

**Response 204:** 无 body。

副作用：删除 Qdrant points、存储文件、可能 bump version（设计选项：删除也 bump，推荐）。

---

## 5. 会话模块

### 5.1 POST /threads

**Request:**

```json
{
  "title": "Optional title"
}
```

**Response 201:**

```json
{
  "id": "uuid",
  "title": "New conversation",
  "documents_version": 3,
  "is_stale": false,
  "created_at": "2026-06-14T08:00:00Z"
}
```

### 5.2 GET /threads

分页列表，按 `updated_at` 降序。

### 5.3 GET /threads/{id}/messages

**Response 200:**

```json
{
  "thread_id": "uuid",
  "is_stale": false,
  "documents_version": 3,
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "挂号流程是什么？",
      "citations": [],
      "created_at": "2026-06-14T08:01:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "根据操作手册...",
      "citations": [
        {
          "document_id": "uuid",
          "chunk_id": "uuid",
          "source": "his/manual.md",
          "page": 5,
          "text_preview": "挂号流程包括..."
        }
      ],
      "token_usage": {"prompt": 800, "completion": 200, "total": 1000},
      "latency_ms": 2100,
      "created_at": "2026-06-14T08:01:02Z"
    }
  ]
}
```

---

## 6. 对话模块（SSE）

### 6.1 POST /chat/stream

Agent 模式流式对话。

**Request:**

```json
{
  "thread_id": "uuid",
  "message": "跨境电商库存盘点 SOP 是什么？",
  "options": {
    "web_search_enabled": true
  }
}
```

**Response:** `Content-Type: text/event-stream`

**SSE 事件类型：**

#### event: token

增量文本 token。

```
event: token
data: {"content": "根据"}

event: token
data: {"content": "库存"}
```

#### event: agent_step（可选，Demo 用）

Agent 节点进度，便于 UI 展示「检索中」「生成中」。

```
event: agent_step
data: {"node": "retrieve", "status": "completed", "retrieval_score": 0.82}
```

#### event: citation

引用块，可在回答完成前推送。

```
event: citation
data: {
  "document_id": "uuid",
  "chunk_id": "uuid",
  "source": "erp/inventory-sop.md",
  "page": null,
  "text_preview": "盘点周期为每月..."
}
```

#### event: done

```
event: done
data: {
  "message_id": "uuid",
  "token_usage": {"prompt": 1200, "completion": 350, "total": 1550},
  "latency_ms": 2800,
  "route": "rag",
  "retrieval_attempts": 1
}
```

#### event: error

```
event: error
data: {"code": "RATE_LIMIT", "message": "Too many requests"}
```

客户端应在收到 `error` 或连接断开时停止渲染。

### 6.2 POST /chat/baseline/stream

请求/响应格式与 `/chat/stream` 相同，但：

- 不发送 `agent_step` 事件
- `done.route` 固定为 `"baseline"`
- 无 rewrite / critique 分支

---

## 7. 评测模块（Admin）

### 7.1 POST /eval/run

**权限：** `admin`

**Request:**

```json
{
  "mode": "agent",
  "dataset": "default",
  "sample_limit": null
}
```

| mode | 说明 |
|------|------|
| `baseline` | Baseline RAG |
| `agent` | LangGraph Agent |
| `both` | 依次跑两种并对比 |

**Response 202:**

```json
{
  "run_id": "uuid",
  "status": "running",
  "mode": "agent"
}
```

### 7.2 GET /eval/results

**Response 200:**

```json
{
  "items": [
    {
      "id": "uuid",
      "mode": "agent",
      "metrics": {
        "faithfulness": 0.88,
        "answer_relevancy": 0.82,
        "context_precision": 0.79,
        "context_recall": 0.74
      },
      "sample_count": 24,
      "duration_sec": 320,
      "created_at": "2026-06-14T10:00:00Z"
    }
  ]
}
```

### 7.3 GET /eval/results/{id}

单条评测详情，含 `config_snapshot`。

---

## 8. 管理模块（Admin，P2）

### 8.1 GET /admin/users

租户内用户列表。

### 8.2 PATCH /admin/users/{id}/role

```json
{"role": "admin"}
```

---

## 9. Rate Limit 响应头

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1718352060
```

超限返回 429 + SSE/JSON error。

---

## 10. 版本与兼容

- URL 版本：`/api/v1`
- 破坏性变更升 `/api/v2`
- 新增字段向后兼容，不删除已有字段

---

## 11. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-14 | 初始 API 规范，补充错误码与 SSE 细节 |
