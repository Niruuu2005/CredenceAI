# CredenceAI — Start developer mode (backend + frontend)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "CredenceAI Developer Mode" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000  Frontend: http://localhost:3000" -ForegroundColor Gray

# Ensure env files exist
$backendEnv = Join-Path $Root "backend\.env"
$backendDev = Join-Path $Root "backend\.env.development"
if (-not (Test-Path $backendEnv) -and (Test-Path $backendDev)) {
    Copy-Item $backendDev $backendEnv
    Write-Host "Created backend/.env from .env.development"
}

$frontendEnv = Join-Path $Root "frontend\.env"
$frontendDev = Join-Path $Root "frontend\.env.development"
if (-not (Test-Path $frontendEnv) -and (Test-Path $frontendDev)) {
    Copy-Item $frontendDev $frontendEnv
    Write-Host "Created frontend/.env from .env.development"
}

$backendJob = Start-Job -ScriptBlock {
    param($Root)
    Set-Location (Join-Path $Root "backend")
    $env:PYTHONPATH = "src"
    $env:APP_ENV = "development"
    if (Test-Path ".venv\Scripts\Activate.ps1") { . .\.venv\Scripts\Activate.ps1 }
    alembic upgrade head 2>$null
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
} -ArgumentList $Root

Start-Sleep -Seconds 3
Set-Location (Join-Path $Root "frontend")
if (-not (Test-Path "node_modules")) { npm install }
npm run dev

Stop-Job $backendJob -ErrorAction SilentlyContinue
Remove-Job $backendJob -ErrorAction SilentlyContinue
