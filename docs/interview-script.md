# BizMind 面试话术 & Demo 演练脚本

> 约 10 分钟完整演示 + 架构讲解。

---

## 1. 开场白（~30s）

> "BizMind 是一个面向企业内部的 Agentic RAG 知识库平台。和传统 RAG 不同，它不是简单的'检索+拼接'，而是通过 LangGraph 编排了一个 6 步 Agent 工作流：Router → Retrieve → Grade → Rewrite → Generate → Critique。每一步都可以独立评分、追踪、溯源。支持多租户隔离、文档版本感知、以及 RAGAS 量化评测。"

---

## 2. Demo 步骤（~6 min）

### 2.1 登录 + 文档上传（1 min）

```powershell
# 1. 启动（如果未启动）
docker compose up -d
.\scripts\seed_demo_docs.py   # 预置 4 类文档

# 2. 浏览器打开 http://localhost:3000
#    用 demo@bizmind.local / DemoPass123! 登录
```

**展示要点：**
- 4 类样例文档：HIS（门诊流程）、ERP（库存盘点）、WorkPal（缺陷管理）、HR（入职指南 PDF）
- 进入「文档」页，展示文档列表、状态（已索引）、分段数

### 2.2 对话 — Agent 模式（2 min）

**展示要点：**
- 在「对话」页切换到 **Agent** 模式
- 提问：*"门诊挂号需要哪些证件？"*
- **重点展示 SSE 流式输出**：前端实时显示 Agent 步骤（router → retrieve → grade → generate → critique）
- 回答附带引用溯源：点击跳转到源文档
- 再问：*"盘盈和盘亏分别如何处理？"* — 跨文档检索

### 2.3 对话 — Baseline 对比（1 min）

- 切换到 **Baseline** 模式
- 同样的问题再问一次
- 展示回答质量差异（Agent 通常更精准，有引用）
- 对比延迟（Agent 更慢但更可靠）

### 2.4 评测页（1 min）

- 进入「评测」页
- 点击触发评测（选 Baseline 模式快速出结果）
- 展示评测指标：Faithfulness / Answer Relevancy / Context Recall
- 说明：RAGAS 量化验证，不是拍脑袋说好

### 2.5 Admin 管理页（1 min）

- 进入「管理」页（ROLE=ADMIN 可见）
- 展示多租户用户列表
- 说明权限控制：ADMIN vs USER，租户间数据隔离

---

## 3. 架构讲解（~3 min）

### 3.1 LangGraph 工作流

```
用户提问 → Router（分类：rag/direct/web/oos）
                ↓  rag
          Retrieve（Dense + BM25 + Cohere Rerank）
                ↓
          Grade（相关性评分 0-1）
           ↙  < threshold        ≥ threshold ↘
    Rewrite（改写 query）         Generate（生成回答）
         ↓                              ↓
    Retrieve（重试 ≤ 2 次）        Critique（自评通过？）
                                         ↙  No ↓ Yes
                                   Generate    END
```

**关键决策：**
- **Router**：避免无关问题走 RAG（打招呼、"今天天气"直接回答或 OOS 拒绝）
- **Grade + Rewrite**：检索质量闭环，不相关时自动改写 query 重试
- **Critique**：模型对自己的回答做 hallucination 检测

### 3.2 混合检索

| 层级 | 方法 | 说明 |
|------|------|------|
| Dense | BGE-M3 Embedding（SiliconFlow） | 语义匹配 |
| BM25 | rank-bm25（本地） | 关键词精确匹配 |
| Fusion | 0.7×Dense + 0.3×BM25 | 加权融合 |
| Rerank | Cohere Rerank v3（可选） | 无 Key 时降级为融合排序 |

### 3.3 多租户隔离

- PostgreSQL **行级安全**：每个查询自动带 `WHERE tenant_id = ?`
- Qdrant **payload filter**：向量数据库层面也做租户过滤
- 跨租户测试：`test_tenant_security.py` 验证隔离有效性

### 3.4 文档版本感知

- 全局 `documents_version_counter` 每次索引递增
- 会话创建时记录当前版本号
- 文档更新后，关联会话自动标记 `is_stale`，提示用户重新检索

---

## 4. 必问问题应答（~1 min）

### Q: 评测指标偏低（context_precision=0），怎么回事？

> "这是 RAGAS 和 DeepSeek 的已知局限，不是检索链路的问题。
> 
> **Faithfulness 0.70 是最重要的指标**——它衡量回答是否基于检索到的上下文，直接反映 RAG 质量。
> 
> context_precision 在 RAGAS 内部依赖多次生成（n>1）计算方差，DeepSeek 只支持 n=1，所以该项恒为 0。我们已在 README 和文档中明确标注这一局限。
> 
> 我们刻意选择 DeepSeek + BGE-M3 作为默认栈——体现成本意识和对国产 OpenAI 兼容 API 的适配能力，不依赖 GPT。"

### Q: 为什么不用 LangChain 的 LCEL？

> "我们用了 LangGraph，它是 LangChain 生态里专门做 Agent 编排的库，更适合复杂条件分支。LangGraph 的 StateGraph 基于状态机，每个节点输入/输出都是 dict，可独立测试，带断点重试。"

### Q: 多租户怎么保证数据不泄露？

> "两层隔离：数据库层 PostgreSQL 行级 RLS，向量库层 Qdrant payload filter。每个请求经过 auth 中间件提取 `tenant_id`，后续所有 DB 和向量查询都自动带过滤条件。我们有专门的跨租户安全测试 `test_tenant_security.py` 验证。"

---

## 5. 技术栈一览

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| Agent 编排 | LangGraph（StateGraph 条件分支） |
| 向量数据库 | Qdrant（HNSW 索引） |
| 关系数据库 | PostgreSQL 16（行级安全） |
| 缓存 | Redis 7 |
| Embedding | BGE-M3 via SiliconFlow |
| LLM | DeepSeek Chat |
| Rerank | Cohere Rerank v3（可选）/ Dense+BM25 融合降级 |
| 评测 | RAGAS（Faithfulness, Answer Relevancy, Context Recall, Context Precision） |
| 前端 | React 19 + Vite + Tailwind CSS |
| 测试 | pytest + pytest-cov + vitest + @testing-library/react |
| CI/CD | GitHub Actions（PG + Qdrant + Redis） |
| 部署 | Docker Compose 一键启动 |

---

## 6. 常见追问应对

- **"Agent 延迟比 Baseline 高多少？"** → Agent ~2.8s，Baseline ~1.5s。但 Agent 多了 Retrieve→Grade→Rewrite→Critique 四个质量步骤，准确率提升明显。
- **"为什么用 DeepSeek 而不是 GPT？"** → 成本更低，OpenAI 兼容 API 可插拔（改 env 即可换模型）；项目默认不依赖 GPT，体现对国内模型的工程适配。
- **"21 条 Golden QA 够吗？"** → 覆盖了 HIS/ERP/WorkPal/HR 四类文档的典型问题类型（事实查询、流程查询、多跳推理、边界问题），回归已有意义。30+ 在路线图上。
- **"如果让你重做，哪里会不一样？"** → 1) 一开始就引入 LangGraph 而不是从 LangChain Chain 迁移；2) 评测先行，用 RAGAS 驱动的 TDD 思路去优化检索。

---

## 7. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-19 | 初版：10 分钟 Demo 流程 + 架构讲解 + 必问应答 |
