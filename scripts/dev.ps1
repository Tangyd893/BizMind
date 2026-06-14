# BizMind Windows dev helpers (PowerShell)
# Usage: .\scripts\dev.ps1 infra-up

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("infra-up", "migrate", "dev-backend", "dev-frontend", "test-backend", "docker-up")]
    [string]$Command
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

switch ($Command) {
    "infra-up" { docker compose up -d postgres redis qdrant }
    "migrate" { Set-Location backend; uv run alembic upgrade head }
    "dev-backend" { Set-Location backend; uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 }
    "dev-frontend" { Set-Location frontend; npm run dev }
    "test-backend" { Set-Location backend; uv run pytest tests/ -q }
    "docker-up" { docker compose up -d --build }
}
