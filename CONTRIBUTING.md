# Contributing to BizMind

**仓库：** https://github.com/Tangyd893/BizMind

## 开始之前

1. 阅读 [docs/design.md](docs/design.md) 与 [docs/dev.md](docs/dev.md)
2. `cp .env.example .env`
3. `make infra-up` → `make migrate` → `make dev-backend`

## 提交与 PR

- Conventional Commits：`feat(scope): message`
- CI 全绿，使用 PR 模板
- 无 `.env` / 密钥进仓库

## Definition of Done

- [ ] 有测试或说明为何不测
- [ ] `ruff check` / `npm run lint` 通过
- [ ] API 变更 → 更新 `docs/api.md`
- [ ] Schema 变更 → Alembic + `docs/design.md` §5

## 本地检查

```bash
cd backend && uv run ruff check . && uv run pytest tests/ -q
cd frontend && npm run lint && npm run test
```
