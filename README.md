<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/Docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<h1 align="center">🧠 BizMind</h1>
<h3 align="center">企业私有文档 · 多租户 Agentic RAG 平台</h3>
<p align="center">让企业知识库从"能搜"进化到"能答、能审、能溯源"</p>
<p align="center">
  <b>文档上传 → 智能检索 → Agent 推理 → 引用溯源 → 质量自评</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/状态-v0.5--quality-green?style=flat" alt="Status">
  <img src="https://img.shields.io/github/stars/Tangyd893/BizMind?style=flat&logo=github" alt="Stars">
  <img src="https://img.shields.io/github/last-commit/Tangyd893/BizMind?style=flat&logo=github" alt="Last Commit">
</p>

---

## 💡 核心理念

> **RAG 不该只是"检索+拼接"，而是一个有判断力的 Agent 工作流。**

传统 RAG 方案在企业场景下存在三大痛点：**检索质量不可控**（召回噪声大）、**回答无审核**（幻觉难追溯）、**多租户隔离缺失**（数据泄露风险）。BizMind 通过 LangGraph 编排的 Agentic 流程，让每一次回答都经历检索 → 评估 → 改写 → 生成 → 自评的完整链路，确保输出可溯源、可审计、可信赖。

## 🏗️ 工作流

```
用户提问                   文档知识库
    │                         │
    ▼                         ▼
 ┌─────────┐            ┌──────────┐
 │  Router  │──路由──►  │ Retriever │
 └────┬────┘            └────┬─────┘
      │                      │
      │               Dense + BM25 + Rerank
      │                      │
      ▼                      ▼
 ┌─────────┐         ┌────────────┐
 │ Rewrite  │◄─不相关─│   Grader   │
 └────┬────┘         └────────────┘
      │
      ▼
 ┌──────────┐
 │ Generate  │──流式 SSE──► 前端展示 + 引用溯源
 └────┬─────┘
      │
      ▼
 ┌──────────┐
 │ Critique  │──质量评分──► RAGAS 评测
 └──────────┘
```

## 📁 项目结构

```
BizMind/
├── 📖 README.md
├── 📜 LICENSE
├── 🔧 Makefile
├── 🐳 docker-compose.yml
├── ⚙️ .env.example
│
├── 📦 backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── agent/               # LangGraph Agent 节点
│   │   ├── api/                 # REST 路由
│   │   ├── core/                # 认证、安全、配置
│   │   ├── db/                  # 数据库连接 & 会话
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── rag/                 # 检索、分块、嵌入
│   │   ├── schemas/             # Pydantic Schema
│   │   └── services/            # 业务逻辑层
│   ├── alembic/                 # 数据库迁移
│   ├── tests/                   # 测试套件
│   ├── pyproject.toml
│   └── Dockerfile
│
├── 🎨 frontend/                 # React 前端
│   ├── src/
│   │   ├── api/                 # API 客户端
│   │   ├── components/          # UI 组件
│   │   ├── pages/               # 页面
│   │   ├── hooks/               # 自定义 Hooks
│   │   └── contexts/            # React Context
│   └── Dockerfile
│
├── 📂 data/                     # 示例数据
│   ├── demo_docs/               # 演示文档（HIS/ERP/WorkPal/HR）
│   └── golden_qa.jsonl          # 评测金标 QA
│
├── 📜 scripts/                  # 工具脚本
│   ├── dev.ps1                  # 开发启动
│   ├── eval_rag.py              # RAG 评测
│   ├── seed_demo_docs.py        # 种子数据导入
│   └── setup_db.py              # 数据库初始化
│
└── 📚 docs/                     # 项目文档
    ├── design.md                # 总体设计
    ├── api.md                   # API 规范
    ├── dev.md                   # 开发部署
    ├── todo0619.md              # 待办清单（当前）
    └── adr/                     # 架构决策记录
```

## 🚀 快速开始

### ✅ 前置条件

| 依赖 | 必需 | 获取方式 |
|:-----|:----:|---------|
| **Python 3.11+** | ✅ | [python.org](https://www.python.org/downloads/) |
| **Node.js 18+** | ✅ | [nodejs.org](https://nodejs.org/) |
| **Docker & Docker Compose** | ✅ | [docs.docker.com](https://docs.docker.com/get-docker/) |
| **Qdrant** | ✅ | Docker 启动（见下方） |
| **LLM API Key** | ✅ | 默认 [DeepSeek](https://platform.deepseek.com/)（OpenAI 兼容） |
| **Embedding API Key** | ✅ | 默认 [SiliconFlow](https://siliconflow.cn/) BGE-M3 |
| **Cohere API Key** | ⭐ | [cohere.com](https://cohere.com/)（可选，用于 Rerank） |

### 📦 Step 1 — 克隆 & 配置

```bash
git clone https://github.com/Tangyd893/BizMind.git
cd BizMind
cp .env.example .env
```

编辑 `.env` 填写必要配置：

| 字段 | 必填 | 说明 |
|:-----|:----:|------|
| `DATABASE_URL` | ✅ | PostgreSQL 连接串 |
| `QDRANT_URL` | ✅ | Qdrant 地址，默认 `http://localhost:6333` |
| `LLM_API_KEY` | ✅ | LLM Key（默认 DeepSeek，`LLM_BASE_URL` 见 `.env.example`） |
| `EMBEDDING_API_KEY` | ✅ | Embedding Key（默认 SiliconFlow BGE-M3） |
| `COHERE_API_KEY` | ⭐ | Cohere Rerank Key（可选） |
| `SECRET_KEY` | ✅ | JWT 签名密钥 |

### ▶️ Step 2 — 运行

**Docker 一键启动（推荐）：**

```bash
docker compose up -d --build
```

访问 http://localhost:3000

**本地开发模式：**

```bash
make infra-up && make migrate    # 启动基础设施 + 数据库迁移
make dev-backend                 # 后端 :8000
make dev-frontend                # 前端 :5173
```

**Windows PowerShell：**

```powershell
.\scripts\dev.ps1
```

### 🧪 Step 3 — 验证

```bash
# 健康检查
curl http://localhost:8000/health

# 运行测试
cd backend && uv run pytest

# RAG 评测
python scripts/eval_rag.py
```

## ✨ 特性

### Agentic RAG 工作流

基于 LangGraph 编排的六步 Agent 链路：Router → Retrieve → Grade → Rewrite → Generate → Critique。每个节点独立可测，支持断点重试和状态追踪。

### 混合检索 + Rerank

Dense Embedding（BGE-M3 / OpenAI 兼容 API）+ BM25 稀疏检索双重召回，可选 Cohere Rerank 精排。兼顾语义理解和关键词精确匹配。

### 多租户隔离

PostgreSQL 行级安全 + Qdrant payload filter，租户间数据物理隔离。支持 RBAC 权限控制。

### 文档版本感知

知识库文档更新后，关联会话自动标记 stale，提示用户重新检索，避免基于过期信息回答。

### 流式对话 + 引用溯源

SSE 流式输出，回答附带源文档引用片段，支持一键跳转原文。

### 评测体系

Golden QA + RAGAS 自动评测，内置 Eval API 和前端 Eval 页面，量化追踪检索质量和回答质量。

**📊 RAGAS Benchmark（21 QA Pairs · DeepSeek Chat + SiliconFlow BGE-M3）**

| 指标 | Baseline | Agent (Hybrid) | 说明 |
|:-----|:--------:|:--------------:|------|
| **Faithfulness** | **0.6983** | **0.6908** | 回答忠实度 — 生成内容是否基于上下文 |
| Answer Relevancy | 0.1578 | 0.1712 | 回答相关性 — 答案与问题的匹配度 |
| Context Precision | 0.0000 | 0.0000 | 上下文精确率 — 检索到的内容是否相关 |
| Context Recall | 0.2353 | 0.1905 | 上下文召回率 — 相关内容是否被检索到 |

> **注：** Baseline 使用单阶段 Dense 检索；Agent 使用 Hybrid 检索（Dense + BM25 + Cohere Rerank）。评测栈为 **DeepSeek Chat + SiliconFlow BGE-M3**（无 GPT 依赖）。DeepSeek 不支持 `n>1` 多采样，`answer_relevancy` / `context_*` 仅供参考；**faithfulness ~0.70 是主要参考指标**，面试叙事以 Agent 架构与可溯源为主。

## ❓ 常见问题

| 问题 | 解决方案 |
|:-----|---------|
| Qdrant 连接失败 | 确认 Docker 容器已启动：`docker compose ps` |
| 前端白屏 | 检查后端是否在 :8000 运行，查看浏览器控制台 |
| 迁移报错 | 确认 `DATABASE_URL` 正确，运行 `make migrate` |
| Embedding 超时 | 检查 `EMBEDDING_API_KEY` 余额和网络连通性 |
| Rerank 不生效 | 无 `COHERE_API_KEY` 时自动降级为 Dense+BM25 融合（见 `dev.md`） |

## 📚 文档

| 文档 | 说明 |
|:-----|------|
| [docs/design.md](docs/design.md) | 总体设计 & 架构决策 |
| [docs/api.md](docs/api.md) | REST API 规范 |
| [docs/dev.md](docs/dev.md) | 开发 & 部署指南 |
| [docs/interview-script.md](docs/interview-script.md) | 🎤 面试 Demo 话术 |
| [docs/todo0619.md](docs/todo0619.md) | 📋 待办清单 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 协作流程 |

## 🛠️ 技术栈

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/LangGraph-Agent-000000?style=for-the-badge&logo=langchain&logoColor=white" alt="LangGraph">
  <img src="https://img.shields.io/badge/Qdrant-Vector_DB-DC382D?style=for-the-badge&logo=qdrant&logoColor=white" alt="Qdrant">
  <img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/Vite-6-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/RAGAS-Eval-FF6B6B?style=for-the-badge" alt="RAGAS">
</p>

---

<p align="center">
  <b>⭐ 觉得有用？点个 Star 支持一下！</b>
</p>
