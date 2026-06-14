# BizMind — 评测基准与 RAGAS 实验

> **版本：** v0.1  
> **状态：** 📋 模板就绪，跑分结果待实现后填入  
> **关联：** [requirements FR-EVAL](./requirements.md#25-评测-fr-eval) · [项目设计 §8](./项目设计.md#8-评测体系)

---

## 1. 评测目标

- 量化 Agentic RAG 相对 Baseline RAG 的收益
- 建立 Golden QA 回归集，防止检索 / Prompt 改动退化
- README 展示可复现 benchmark 表格（面试说服力）

---

## 2. Golden QA 数据集

### 2.1 文件位置

```
data/golden_qa.jsonl
```

### 2.2 格式规范

每行一个 JSON 对象（JSONL）：

```json
{
  "id": "qa-his-001",
  "question": "门诊挂号需要携带哪些证件？",
  "expected_answer": "需携带身份证或医保卡；外籍患者携带护照。",
  "doc_refs": ["his/outpatient-guide.md"],
  "category": "his",
  "type": "single_hop",
  "tags": ["factual", "sop"]
}
```

### 2.3 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| id | 是 | 唯一标识 |
| question | 是 | 用户问题 |
| expected_answer | 是 | 参考答案（RAGAS 用） |
| doc_refs | 是 | 期望引用的文档路径 |
| category | 是 | `his` / `erp` / `workpal` |
| type | 是 | 见下表 |
| tags | 否 | 额外标签 |

### 2.4 问题类型

| type | 说明 | 数量目标 |
|------|------|----------|
| single_hop | 单文档单点事实 | ≥ 8 |
| multi_hop | 跨章节综合 | ≥ 6 |
| rejection | 文档外应拒答/说明未知 | ≥ 4 |
| version_sensitive | 依赖特定版本表述 | ≥ 2 |

**总量：** ≥ 20 条，三类文档各覆盖。

### 2.5 示例条目（待写入 golden_qa.jsonl）

```jsonl
{"id":"qa-his-001","question":"门诊挂号需要携带哪些证件？","expected_answer":"需携带身份证或医保卡。","doc_refs":["his/outpatient-guide.md"],"category":"his","type":"single_hop"}
{"id":"qa-erp-001","question":"跨境电商库存盘点周期是多久？","expected_answer":"每月最后一个工作日进行全面盘点。","doc_refs":["erp/inventory-sop.md"],"category":"erp","type":"single_hop"}
{"id":"qa-wp-001","question":"P0 缺陷的响应时限是多少？","expected_answer":"2 小时内响应，24 小时内修复或 workaround。","doc_refs":["workpal/defect-severity.md"],"category":"workpal","type":"single_hop"}
{"id":"qa-rej-001","question":"今天上海天气怎么样？","expected_answer":"该问题不在企业知识库范围内。","doc_refs":[],"category":"his","type":"rejection"}
```

---

## 3. RAGAS 指标

| 指标 | 含义 | v1 目标（Agent） | v1 目标（Baseline） |
|------|------|------------------|---------------------|
| faithfulness | 答案是否忠于检索上下文 | ≥ 0.85 | ≥ 0.70 |
| answer_relevancy | 答案是否切题 | ≥ 0.80 | ≥ 0.75 |
| context_precision | 检索结果精准度 | ≥ 0.75 | ≥ 0.60 |
| context_recall | 检索召回关键信息 | ≥ 0.70 | ≥ 0.55 |

---

## 4. 实验设计

### 4.1 对比模式

| 模式 | 路径 | 变量 |
|------|------|------|
| Baseline | `/chat/baseline/stream` 逻辑 | 仅 dense + generate |
| Agent | LangGraph 全图 | + grade, rewrite, critique |

**控制变量：** 相同 Embedding、相同 chunk 参数、相同 LLM model、相同 golden_qa 集。

### 4.2 实验矩阵

| 实验 ID | chunk_size | rerank | Agent | 目的 |
|---------|------------|--------|-------|------|
| EXP-01 | 512 | off | off | Baseline 下限 |
| EXP-02 | 512 | on | off | +Rerank 收益 |
| EXP-03 | 512 | on | on | 完整 Agent |
| EXP-04 | 256 | on | on | 参数敏感性（可选） |

---

## 5. 执行方法

### 5.1 CLI 脚本

```bash
# 跑 Agent 模式
python scripts/eval_rag.py --mode agent --dataset data/golden_qa.jsonl

# 跑 Baseline
python scripts/eval_rag.py --mode baseline

# 对比并写 README 表格
python scripts/eval_rag.py --mode both --output docs/eval-results.json
```

### 5.2 API 触发

```http
POST /api/v1/eval/run
Authorization: Bearer <admin_token>
Content-Type: application/json

{"mode": "both", "dataset": "default"}
```

### 5.3 脚本逻辑（设计）

1. 加载 golden_qa.jsonl
2. 对每条 question 调用对应 pipeline（mock 不可用，需真实 LLM）
3. RAGAS evaluate：`faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`
4. 聚合均值 ± 标准差
5. 写入 `eval_runs` 表 + 可选 JSON 文件

---

## 6. 结果记录模板

> 以下数值为**目标占位**，实现后替换为真实跑分。

### 6.1 主对比表（README 用）

| 模式 | faithfulness | answer_relevancy | context_precision | context_recall | avg_latency |
|------|-------------|------------------|-------------------|----------------|-------------|
| Baseline RAG | 0.72 | 0.78 | 0.61 | 0.58 | 1.2s |
| Agentic RAG | **0.88** | **0.82** | **0.79** | **0.74** | 2.8s |

### 6.2 分类 breakdown

| category | Baseline F | Agent F | Δ |
|----------|------------|---------|---|
| his | 0.74 | 0.90 | +0.16 |
| erp | 0.71 | 0.87 | +0.16 |
| workpal | 0.70 | 0.86 | +0.16 |
| rejection | 0.65 | 0.82 | +0.17 |

### 6.3 跑分历史

| run_id | date | mode | faithfulness | git_sha |
|--------|------|------|--------------|---------|
| _待填_ | 2026-__-__ | agent | _._ | _commit_ |

---

## 7. CI 集成

| 级别 | 策略 |
|------|------|
| PR CI | 不跑 RAGAS（省 API 费用） |
| nightly | `workflow_dispatch` 跑 baseline smoke（3 条） |
| release | 全量 golden_qa + 门禁指标 |

---

## 8. 失败分析与优化顺序

1. **context_precision 低** → 调 chunk / hybrid / rerank
2. **faithfulness 低** → 调 generate prompt、critique
3. **rejection 类差** → 调 router / oos prompt
4. **latency 高** → 减 critique 次数、用小模型 grade

---

## 9. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-14 | 评测框架与 Golden QA 规范 |
