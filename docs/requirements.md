# BizMind — 软件需求规格说明书 (SRS)

> **文档编号：** SRS-BIZMIND-001  
> **版本：** v0.1  
> **状态：** 设计阶段  
> **关联：** [项目设计](./项目设计.md) · [api-spec](./api-spec.md)

---

## 1. 引言

### 1.1 目的

本文档定义 BizMind v1.0（MVP）的功能需求与非功能需求，作为开发、测试与验收的基准。

### 1.2 范围

BizMind 是一个面向企业私有文档的多租户 Agentic RAG 平台，支持文档上传、权限隔离、流式对话、检索质量自评与 RAGAS 量化评测。

**不在范围内：** 见 [项目设计 §1.4](./项目设计.md#14-非目标yagni)。

### 1.3 术语

| 术语 | 定义 |
|------|------|
| Tenant | 租户，数据隔离边界 |
| Thread | 对话会话，绑定知识库版本快照 |
| Baseline RAG | 简单单向量检索 + 生成，无 Agent 分支 |
| Agentic RAG | LangGraph 编排的完整 Agent 工作流 |
| Golden QA | 人工标注的标准问答评测集 |
| documents_version | 全局知识库版本号，文档变更时递增 |

### 1.4 用户角色

| 角色 | 标识 | 权限概要 |
|------|------|----------|
| 系统管理员 | `admin` | 用户管理、评测触发、全局配置 |
| 普通用户 | `user` | 文档上传（本租户）、对话、查看历史 |
| 部门管理员 | `user` + 扩展 | v1 与 `user` 等同；v1.1 可增文档审批 |

---

## 2. 功能需求

### 2.1 用户与认证 (FR-AUTH)

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| FR-AUTH-01 | 用户可使用邮箱 + 密码注册 | P0 | 注册成功后写入 `users` 表，密码 bcrypt 哈希 |
| FR-AUTH-02 | 用户可登录并获取 JWT | P0 | 返回 access token；无效凭证返回 401 |
| FR-AUTH-03 | 受保护接口需 Bearer JWT | P0 | 无 token / 过期 token 返回 401 |
| FR-AUTH-04 | 获取当前用户信息 | P0 | `GET /auth/me` 返回 id、email、role、tenant_id |
| FR-AUTH-05 | 角色 RBAC | P1 | admin 可访问 `/eval/*`、`/admin/*` |

### 2.2 文档管理 (FR-DOC)

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| FR-DOC-01 | 上传 PDF / Markdown | P0 | multipart 上传，返回 document id 与 status |
| FR-DOC-02 | 异步解析与索引 | P0 | status: pending → indexed / failed |
| FR-DOC-03 | Parent-Child 分块 | P0 | child 入 Qdrant，parent 关联可查 |
| FR-DOC-04 | 文档列表分页 | P0 | 仅返回当前 tenant 文档 |
| FR-DOC-05 | 删除文档 | P1 | 删除 PG 记录、向量、存储文件 |
| FR-DOC-06 | 版本 bump | P0 | 索引成功后 `documents_version` 全局 +1 |
| FR-DOC-07 | 文件校验 | P0 | 白名单 mime、最大 20MB |

### 2.3 对话与 Agent (FR-CHAT)

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| FR-CHAT-01 | 创建 / 列出 Thread | P0 | Thread 记录创建时 `documents_version` 快照 |
| FR-CHAT-02 | SSE 流式 Agent 对话 | P0 | 事件：token / citation / done / error |
| FR-CHAT-03 | Baseline RAG 流式对话 | P0 | 独立端点，无 Agent 分支 |
| FR-CHAT-04 | 多轮上下文 | P0 | 同一 Thread 内保留历史消息 |
| FR-CHAT-05 | 引用溯源 | P0 | 回答含 citations（doc_id, chunk_id, page） |
| FR-CHAT-06 | 版本 stale 提示 | P1 | `is_stale=true` 时 UI 提示开新对话 |
| FR-CHAT-07 | Router 分流 | P1 | direct / rag / web / oos 四类路由 |
| FR-CHAT-08 | 检索质量 Grade + Rewrite | P1 | 低质量时改写 query 重试，最多 2 次 |
| FR-CHAT-09 | Critique 自检 | P1 | 幻觉检测失败时重生成，最多 1 次 |
| FR-CHAT-10 | Web Fallback | P2 | 检索为空时可选 Tavily 搜索 |

### 2.4 多租户隔离 (FR-TENANT)

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| FR-TENANT-01 | 租户数据隔离 | P0 | API 层 filter tenant_id |
| FR-TENANT-02 | 向量检索隔离 | P0 | Qdrant payload filter 强制 tenant_id |
| FR-TENANT-03 | 跨租户访问拒绝 | P0 | 访问他租户 document/thread 返回 404 |

### 2.5 评测 (FR-EVAL)

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| FR-EVAL-01 | Golden QA 批跑 | P1 | admin 触发 RAGAS 评测 |
| FR-EVAL-02 | 评测结果持久化 | P1 | 存储各指标与模式（baseline/agent） |
| FR-EVAL-03 | 对比报告 | P1 | README / API 可查看历史结果 |

### 2.6 运维 (FR-OPS)

| ID | 需求 | 优先级 | 验收标准 |
|----|------|--------|----------|
| FR-OPS-01 | 健康检查 | P0 | `GET /health` 返回 DB/Redis/Qdrant 状态 |
| FR-OPS-02 | 结构化日志 | P1 | request_id、user_id、tenant_id |
| FR-OPS-03 | Langfuse 追踪 | P2 | 可选 profile，Agent 节点 span |

---

## 3. 非功能需求

### 3.1 性能 (NFR-PERF)

| ID | 指标 | 目标 |
|----|------|------|
| NFR-PERF-01 | 首 token 延迟（P95） | < 2s（Agent 模式，本地 Docker） |
| NFR-PERF-02 | 文档索引（10 页 PDF） | < 30s |
| NFR-PERF-03 | 并发用户（Demo） | ≥ 5 同时对话 |

### 3.2 可用性 (NFR-AVAIL)

| ID | 指标 | 目标 |
|----|------|------|
| NFR-AVAIL-01 | Docker Compose 一键启动 | 10 分钟内完成首次部署 |
| NFR-AVAIL-02 | Demo 完整流程 | 10 分钟内完成一次面试演示 |

### 3.3 安全 (NFR-SEC)

| ID | 要求 | 说明 |
|----|------|------|
| NFR-SEC-01 | 密钥不入库 | `.env` / Docker secrets |
| NFR-SEC-02 | JWT 过期 | access token 24h（v1） |
| NFR-SEC-03 | Rate Limit | Redis 滑动窗口，用户级 |
| NFR-SEC-04 | Prompt 注入防护 | 检索内容 XML 标签隔离 |

### 3.4 可维护性 (NFR-MAINT)

| ID | 要求 | 说明 |
|----|------|------|
| NFR-MAINT-01 | 测试覆盖率 | backend 核心模块 ≥ 70% |
| NFR-MAINT-02 | 配置外置 | 12-Factor，见 `.env.example` |
| NFR-MAINT-03 | API 文档 | FastAPI OpenAPI 自动生成 |

### 3.5 可观测性 (NFR-OBS)

| ID | 要求 | 说明 |
|----|------|------|
| NFR-OBS-01 | 请求追踪 | Langfuse trace per chat |
| NFR-OBS-02 | Token 统计 | 每条 message 记录 token_usage |

---

## 4. 外部接口

| 接口 | 协议 | 用途 |
|------|------|------|
| OpenAI 兼容 LLM API | HTTPS | 生成、Grade、Critique、Router |
| Embedding API | HTTPS | 文档与 query 向量化 |
| Tavily API | HTTPS | Web 搜索 fallback（可选） |
| Langfuse | HTTPS | 可观测（可选） |

详见 [api-spec.md](./api-spec.md)。

---

## 5. 数据需求

- 持久化：PostgreSQL（用户、文档、会话、消息、评测）
- 向量：Qdrant（chunk embeddings + payload）
- 缓存：Redis（embedding cache、rate limit）
- 文件：本地 volume 或 S3 兼容存储

详见 [database-schema.md](./database-schema.md)。

---

## 6. 验收标准（MVP 发布）

与 [项目设计 §1.5](./项目设计.md#15-成功标准) 对齐；**实时状态见 [progress.md](./progress.md)**。

- [x] GitHub 公开仓库，README 含架构图 + Docker Compose 一键启动
- [ ] ≥ 3 类企业样例文档 + ≥ 20 条 Golden QA（文档 ✅，QA 12/20）
- [x] LangGraph Agent 工作流可演示
- [ ] RAGAS 评测结果可复现，README 有 benchmark 表格
- [x] 多租户文档隔离 + 文档版本感知对话
- [ ] 10 分钟内可完成一次完整面试 Demo

---

## 7. 需求追溯矩阵（摘要）

| 需求域 | 设计文档 | 测试文档 |
|--------|----------|----------|
| FR-AUTH | 项目设计 §5.2, api-spec §3 | test-plan §4.1 |
| FR-DOC | 项目设计 §5.3, agent-workflow | test-plan §4.2 |
| FR-CHAT | agent-workflow, api-spec §4 | test-plan §4.3 |
| FR-EVAL | eval-benchmark | test-plan §4.5 |
| NFR-* | deployment, 项目设计 §7 | test-plan §5 |

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-14 | 验收标准勾选同步 progress 审计 |
