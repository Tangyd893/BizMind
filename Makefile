.PHONY: help infra-up infra-down migrate dev-backend dev-frontend test-backend test-frontend docker-up docker-down seed-demo

help:
	@echo "BizMind development targets:"
	@echo "  make infra-up       Start postgres, redis, qdrant"
	@echo "  make migrate        Run alembic upgrade head"
	@echo "  make dev-backend    Run FastAPI with reload"
	@echo "  make dev-frontend   Run Vite dev server"
	@echo "  make test-backend   Run backend pytest"
	@echo "  make docker-up      docker compose up -d"
	@echo "  make seed-demo      Seed demo docs (dry-run until P1-11)"

infra-up:
	docker compose up -d postgres redis qdrant

infra-down:
	docker compose stop postgres redis qdrant

migrate:
	cd backend && uv run alembic upgrade head

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

test-backend:
	cd backend && uv run pytest tests/ -q

test-frontend:
	cd frontend && npm run test

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

seed-demo:
	cd backend && uv run python ../scripts/seed_demo_docs.py --dry-run
