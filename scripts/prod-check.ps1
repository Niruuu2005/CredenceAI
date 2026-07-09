# CredenceAI — Validate production configuration before deploy
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "CredenceAI Production Config Check" -ForegroundColor Cyan

$errors = @()

$backendEnv = Join-Path $Root "backend\.env"
if (-not (Test-Path $backendEnv)) {
    $errors += "backend/.env not found — copy from backend/.env.production"
} else {
    $content = Get-Content $backendEnv -Raw
    if ($content -match "APP_ENV=(local|development)") {
        $errors += "APP_ENV must be 'production' in backend/.env"
    }
    if ($content -match "MOCK_SERVICES=true") {
        $errors += "MOCK_SERVICES must be false in production"
    }
    if ($content -notmatch "JWT_SECRET=.{16,}") {
        $errors += "JWT_SECRET must be set to a strong value (16+ chars)"
    }
}

$vercelJson = Join-Path $Root "frontend\vercel.json"
if (Test-Path $vercelJson) {
    $vj = Get-Content $vercelJson -Raw | ConvertFrom-Json
    $apiRewrite = $vj.rewrites | Where-Object { $_.source -like "/api/*" }
    if (-not $apiRewrite) {
        $errors += "frontend/vercel.json missing /api rewrite to Render"
    }
}

if ($errors.Count -eq 0) {
    Write-Host "All checks passed." -ForegroundColor Green
    exit 0
} else {
    Write-Host "Issues found:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    exit 1
}
