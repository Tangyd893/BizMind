# BizMind — 面试叙事与 Demo 提纲

> **版本：** v0.1  
> **用途：** 技术面试项目介绍、Live Demo 脚本、高频 Q&A  
> **关联：** [项目设计 §10](./项目设计.md#10-面试叙事提纲摘要) · [eval-benchmark](./eval-benchmark.md)

---

## 1.  Elevator Pitch（30 秒）

> BizMind 是我做的企业知识智能助手：多租户 Agentic RAG 平台，支持私有文档上传、权限隔离、Hybrid 检索和 LangGraph 条件工作流。相比简单 RAG，增加了检索质量评判、查询改写和回答自检，并用 RAGAS 量化对比 Baseline。整个项目 Docker 一键启动，10 分钟可完整 Demo。

---

## 2. 为什么做这个项目

| 痛点 | BizMind 回应 |
|------|--------------|
| 已有 HIS/ERP 后端项目，缺 AI 应用代表作 | 企业知识场景与领域经验一致 |
| 简单 ChatGPT 套壳缺乏深度 | Agent 工作流 + 评测 + 多租户工程化 |
| 面试官关心「决策逻辑」 | LangGraph 显式状态机，可讲每个分支 WHY |

---

## 3. 技术亮点（按优先级）

### 3.1 必讲（核心差异化）

1. **LangGraph Agent 工作流** — Router → Retrieve → Grade → Rewrite → Generate → Critique
2. **Hybrid Retrieval + Rerank** — Dense + BM25 + Cross-Encoder
3. **Parent-Child Chunking** — 小块检索、大块上下文
4. **文档版本感知 Thread** — 知识库更新后 stale 提示
5. **RAGAS 量化对比** — Agent vs Baseline 表格

### 3.2 工程亮点（展示广度）

- 多租户 PG + Qdrant 双重隔离
- SSE 流式 + citation 溯源
- Redis Embedding 缓存 + Rate Limit
- structlog + Langfuse 可观测
- pytest 分层 + CI 70% 覆盖率

---

## 4. 架构讲解顺序（5 分钟）

1. **Context** — 用户上传 PDF → 索引到 Qdrant
2. **Chat 路径** — SSE 进入 LangGraph
3. **Agent 图** — 展开 whiteboard / architecture.md 状态图
4. **检索管道** — Hybrid → Rerank → Parent context
5. **数据** — ER 图强调 tenant_id、documents_version
6. **评测** — Golden QA + RAGAS 表格

---

## 5. Live Demo 脚本（10 分钟）

| 时间 | 动作 | 话术要点 |
|------|------|----------|
| 0:00 | 打开首页，登录 demo 账号 | 「多租户，每个组织数据隔离」 |
| 1:00 | 文档页：展示 HIS/ERP/WorkPal 三类文档 | 「Parent-Child 分块已索引」 |
| 2:30 | 新建对话，问 ERP 库存 SOP | 「走 Agent 模式，SSE 流式」 |
| 4:00 | 指出 citation 跳转 | 「答案可溯源到 chunk 和页码」 |
| 5:00 | 问一个模糊问题，观察 rewrite | 「Grade 低分会改写 query 重检」 |
| 6:30 | 切换到 Baseline 对比同一问题 | 「延迟更低但 faithfulness 更差」 |
| 8:00 | 打开 Eval 面板 / README 表格 | 「RAGAS 可复现，Agent +0.16 faithfulness」 |
| 9:00 | 上传新文档，旧对话 stale 提示 | 「版本感知，避免过期知识」 |
| 9:30 | Langfuse trace（可选） | 「每个 Agent 节点有 span」 |

**备用：** API 失败时用预录屏或本地 mock 环境。

---

## 6. 权衡故事（面试官最爱）

### 6.1 Agent 延迟 vs 准确率

- Baseline ~1.2s，Agent ~2.8s
- 多 2 次 LLM 调用（grade + critique）换 faithfulness +0.16
- 选型：企业 SOP 场景准确率优先

### 6.2 Parent-Child vs Fixed Chunk

- Fixed 512：检索准但上下文断
- Parent 2048：生成连贯，存储略增
- 参数来自 ADR-003，可 A/B

### 6.3 Qdrant vs Chroma

- 要 payload filter 多租户 + hybrid → Qdrant
- 见 ADR-002

### 6.4 自托管 Rerank vs Cohere API

- 本地 bge-reranker：零 API 费，占内存
- Cohere：省资源，Demo 环境可选

---

## 7. 高频 Q&A

### Q1: 和 LangChain Chain 有什么区别？

LangGraph 把每一步建成显式节点和条件边，状态可测试、可观测；Chain 适合线性流程，不适合 grade/rewrite 循环。

### Q2: 如何防止跨租户数据泄露？

三层：JWT tenant_id、PG 查询 filter、Qdrant payload must filter；集成测试覆盖 cross-tenant 404。

### Q3: 如何防止幻觉？

检索上下文 XML 隔离 + Critique 节点自检 + RAGAS faithfulness 回归；仍不做 100% 保证，产品层提示「仅供参考」。

### Q4: Prompt 注入怎么处理？

系统 prompt 与用户输入分离；检索内容包在 `<retrieved_context>` 标签；不在 prompt 里拼接未转义 HTML。

### Q5: 文档更新后旧对话怎么办？

documents_version 全局递增；旧 thread 标记 is_stale；UI 引导新对话，避免引用过期 chunk。

### Q6: 成本怎么控？

Router 分流 direct 简单问题；Embedding Redis 缓存；Critique 用小模型；Rate limit 防滥用。

### Q7: 为什么不用 Fine-tuning？

RAG 更适合频繁更新的企业文档；Fine-tuning 成本高且数据同步难；见非目标 YAGNI。

### Q8: 评测数据集怎么保证质量？

人工编写 Golden QA，覆盖三类业务 + 拒答 + 多跳；expected_answer 来自源文档原文。

### Q9: 下一步做什么？

MCP 工具导出、WorkPal 工单 Mock 联动、长对话 summary 压缩。

### Q10: 你负责哪部分？

（按实际填写）后端 RAG + Agent 全链路 / 前端 SSE UI / 评测脚本 / Docker 部署。

---

## 8. 负面问题应对

| 挑战 | 回应 |
|------|------|
| 「不就是 RAG 套壳？」 | 强调 Agent 条件分支、版本感知、RAGAS 对照、多租户 |
| 「延迟太高」 | 承认 trade-off；可讲缓存、并行、小模型优化路线 |
| 「没上生产」 | MVP 定位；工程化要素（隔离、限流、迁移、CI）已设计 |

---

## 9. 材料清单

- [ ] GitHub README 架构图
- [ ] 本地 Docker 环境验证
- [ ] Demo 账号密码记录（勿 commit）
- [ ] RAGAS 结果截图
- [ ] Langfuse trace 截图 1–2 张
- [ ] 本提纲打印 / 第二屏参考

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-14 | 完整面试叙事与 Demo 脚本 |
