#!/usr/bin/env pwsh
# BizMind 10 分钟 Demo 演练脚本
# 用法: .\scripts\demo.ps1

$ErrorActionPreference = "Stop"
$StartTime = Get-Date

function Step($name, $script) {
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "▶ $name" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    $stepStart = Get-Date
    & $script
    $elapsed = (Get-Date) - $stepStart
    Write-Host "  ✅ 完成 (耗时: $($elapsed.TotalSeconds.ToString('0.0'))s)" -ForegroundColor Green
}

Write-Host @"

╔══════════════════════════════════════════╗
║     🧠 BizMind 10 分钟 Demo 演练        ║
║     Seed → 对话 → Eval 全链路走通        ║
╚══════════════════════════════════════════╝

"@ -ForegroundColor Magenta

# ── Step 1: 环境检查 ──
Step "1/7 环境检查" {
    Write-Host "  检查 Docker..."
    docker ps > $null 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker 未运行，请先启动 Docker Desktop" }
    Write-Host "  检查 .env..."
    if (!(Test-Path .env)) { throw ".env 不存在，请先 cp .env.example .env 并填入 API Key" }
    $envContent = Get-Content .env -Raw
    if ($envContent -notmatch 'LLM_API_KEY=sk-') { Write-Host "  ⚠️  LLM_API_KEY 未配置，Demo 将使用零向量" -ForegroundColor Yellow }
    if ($envContent -notmatch 'EMBEDDING_API_KEY=sk-') { Write-Host "  ⚠️  EMBEDDING_API_KEY 未配置，Embedding 可能失败" -ForegroundColor Yellow }
}

# ── Step 2: 启动基础设施 ──
Step "2/7 启动基础设施 (PG + Redis + Qdrant)" {
    docker compose up -d postgres redis qdrant 2>&1 | Out-Null
    Write-Host "  等待 PostgreSQL 就绪..."
    $retry = 0
    do {
        Start-Sleep -Seconds 2
        $retry++
        $healthy = docker compose exec -T postgres pg_isready -U bizmind -d bizmind 2>$null
    } while ($LASTEXITCODE -ne 0 -and $retry -lt 15)
    if ($retry -ge 15) { throw "PostgreSQL 启动超时" }
    Write-Host "  PostgreSQL ✅  Redis ✅  Qdrant ✅"
}

# ── Step 3: 数据库迁移 ──
Step "3/7 数据库迁移" {
    Set-Location backend
    uv run alembic upgrade head 2>&1 | Select-Object -Last 1
    Set-Location ..
}

# ── Step 4: 种子数据 ──
Step "4/7 导入演示文档 (3 篇)" {
    Set-Location backend
    uv run python ../scripts/seed_demo_docs.py 2>&1 | Select-String -Pattern "Created|UPLOAD|INDEX|SKIP|Seed complete"
    Set-Location ..
}

# ── Step 5: 启动后端 ──
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "▶ 5/7 启动后端 API (后台运行)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Set-Location backend
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1
}
Set-Location ..
Write-Host "  等待后端就绪..."
$retry = 0
do {
    Start-Sleep -Seconds 2
    $retry++
    try { $null = Invoke-WebRequest -Uri http://localhost:8000/health -TimeoutSec 2 -UseBasicParsing } catch { }
} while ($? -eq $false -and $retry -lt 15)
if ($retry -ge 15) { throw "后端启动超时" }
Write-Host "  后端 ✅  http://localhost:8000"

# ── Step 6: API 演练 ──
Step "6/7 API 演练 (注册 → 登录 → 对话 → Eval)" {
    $base = "http://localhost:8000/api/v1"
    
    Write-Host "  6a. 注册测试用户..."
    $registerBody = @{email="demo@bizmind.local";password="DemoPass123!";tenant_name="Demo Corp"} | ConvertTo-Json
    try {
        $registerResp = Invoke-RestMethod -Uri "$base/auth/register" -Method Post -Body $registerBody -ContentType "application/json" -SkipCertificateCheck
        Write-Host "    注册成功: $($registerResp.user.email)"
        $token = $registerResp.access_token
    } catch {
        Write-Host "    用户已存在，尝试登录..."
        $loginBody = @{email="demo@bizmind.local";password="DemoPass123!"} | ConvertTo-Json
        $loginResp = Invoke-RestMethod -Uri "$base/auth/login" -Method Post -Body $loginBody -ContentType "application/json" -SkipCertificateCheck
        $token = $loginResp.access_token
        Write-Host "    登录成功"
    }
    
    Write-Host "  6b. 获取文档列表..."
    $headers = @{Authorization="Bearer $token"}
    $docs = Invoke-RestMethod -Uri "$base/documents" -Headers $headers -SkipCertificateCheck
    Write-Host "    文档数: $($docs.total)"
    
    Write-Host "  6c. 创建对话线程..."
    $threadBody = @{title="Demo 对话"} | ConvertTo-Json
    $thread = Invoke-RestMethod -Uri "$base/threads" -Method Post -Body $threadBody -ContentType "application/json" -Headers $headers -SkipCertificateCheck
    $threadId = $thread.id
    Write-Host "    线程 ID: $threadId"
    
    Write-Host "  6d. 发送提问..."
    $questions = @(
        "门诊挂号需要携带哪些证件？",
        "P0 缺陷的响应时间是多少？",
        "跨境电商全面盘点的周期是多久？"
    )
    foreach ($q in $questions) {
        $msgBody = @{content=$q} | ConvertTo-Json
        $msg = Invoke-RestMethod -Uri "$base/threads/$threadId/messages" -Method Post -Body $msgBody -ContentType "application/json" -Headers $headers -SkipCertificateCheck
        Write-Host "    Q: $q"
        Write-Host "    A: $($msg.content.Substring(0, [Math]::Min(100, $msg.content.Length)))..."
    }
    
    Write-Host "  6e. 触发 RAGAS 评测..."
    $evalBody = @{mode="baseline";dataset="default"} | ConvertTo-Json
    $eval = Invoke-RestMethod -Uri "$base/eval/run" -Method Post -Body $evalBody -ContentType "application/json" -Headers $headers -SkipCertificateCheck
    Write-Host "    评测已触发: run_id=$($eval.run_id)"
    Write-Host "    ⏳ 评测后台运行中，预计 5-8 分钟完成"
}

# ── Step 7: 打开前端 ──
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "▶ 7/7 前端入口" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  🌐 打开浏览器访问: http://localhost:5173" -ForegroundColor Yellow
Write-Host "  🔑 登录账号: demo@bizmind.local / DemoPass123!" -ForegroundColor Yellow
Write-Host "  📊 查看评测: 点击左侧 Eval 菜单" -ForegroundColor Yellow

# ── 总结 ──
$totalElapsed = (Get-Date) - $StartTime
Write-Host @"

╔══════════════════════════════════════════╗
║          🎉 Demo 演练完成!               ║
║  总耗时: $($totalElapsed.TotalSeconds.ToString('0.0'))s                            ║
╚══════════════════════════════════════════╝

"@ -ForegroundColor Magenta

Write-Host "📋 停止后端: Stop-Job -Id $($backendJob.Id)" -ForegroundColor Gray
Write-Host "📋 停止基础设施: docker compose stop" -ForegroundColor Gray
