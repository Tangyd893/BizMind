# Contributing to BizMind

感谢参与 BizMind 开发。本文说明协作流程、完成标准与文档同步要求。

**仓库：** https://github.com/Tangyd893/BizMind

## 开始之前

1. 阅读 [docs/README.md](docs/README.md) 与 [docs/decisions.md](docs/decisions.md)
2. 复制环境变量：`cp .env.example .env`（Windows: `copy .env.example .env`）
3. 本地启动：`make infra-up` → `make migrate` → `make dev-backend`

## 分支策略

| 分支 | 用途 |
|------|------|
| `main` | 稳定可演示；仅通过 PR 合并 |
| `develop` | 日常集成（可选） |
| `feature/*` | 功能开发，如 `feature/p1-auth` |
| `fix/*` | Bug 修复 |

从 `main`（或 `develop`）拉分支，完成后提 PR 回目标分支。

## 提交信息

使用 [Conventional Commits](https://www.conventionalcommits.org/)，带 scope：

```
feat(agent): add grade node conditional edge
fix(rag): tenant filter on qdrant search
docs(api): document SSE agent_step event
test(auth): register duplicate email returns 409
chore(ci): add qdrant service to workflow
```

## Pull Request

- 使用 PR 模板填写检查项
- CI 必须全绿
- 关联需求 ID（如 `FR-CHAT-02`）或 P1 任务编号
- API / DB 变更须同步文档（见下方）

## Definition of Done

每个 PR 合并前须满足：

- [ ] 功能符合 [requirements.md](docs/requirements.md) 或 P1 backlog 任务描述
- [ ] 新增/变更逻辑有测试，或 PR 中说明为何不测
- [ ] `ruff check` / `ruff format --check` 通过（Python）
- [ ] `npm run lint` 通过（前端，若改动 frontend）
- [ ] 无密钥、无 `.env` 文件进入 Git
- [ ] 公开 service / API / agent node 有 docstring 或 API 文档
- [ ] 若变更 REST/SSE：已更新 [docs/api-spec.md](docs/api-spec.md)
- [ ] 若变更 schema：已新增 Alembic migration 并更新 [docs/database-schema.md](docs/database-schema.md)

### Phase 覆盖率门禁

| Phase | Backend 覆盖率 |
|-------|----------------|
| 脚手架 / P1 初期 | ≥ 0%（CI 不 fail，仅报告） |
| P1 结束 | ≥ 50% |
| P2+ | ≥ 70%（见 test-plan） |

## 文档同步规则

| 变更类型 | 须更新 |
|----------|--------|
| 新 API 端点 | `docs/api-spec.md` |
| 表结构 | `docs/database-schema.md` + Alembic |
| Agent 节点/边 | `docs/agent-workflow.md` |
| 架构/组件 | `docs/architecture.md` |
| 已定决策 | `docs/decisions.md` + 可选新 ADR |
| 环境变量 | `.env.example` + `docs/deployment.md` |

**OpenAPI 以代码为准（code-first）：** 实现后 `/docs` 为权威；设计文档与之冲突时回写 markdown。

## 代码规范

详见 [docs/coding-standards.md](docs/coding-standards.md)。

## 本地质量检查

```bash
# Backend
cd backend && uv run ruff check . && uv run ruff format --check .
cd backend && uv run pytest tests/ -q

# Frontend
cd frontend && npm run lint

# Pre-commit（推荐）
pre-commit run --all-files
```

## 安全

- 禁止提交 API Key、`.env`
- Demo 账号密码仅用于本地
- 依赖升级 PR 注明原因

## 问题反馈

使用 GitHub Issues；功能请求请引用 P1/P2 Phase。
