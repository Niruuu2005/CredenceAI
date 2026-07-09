# AgentGate deploy helper (Render)
# Prereq: code pushed to GitHub; Render account connected to repo.

param(
    [string]$PublicUrl = "",
    [string]$OpenRouterKey = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "AgentGate Render deploy checklist" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Push branch hackathon/agentgate to GitHub"
Write-Host "2. Render Dashboard -> New -> Web Service"
Write-Host "3. Repo: Niruuu2005/CredenceAI, branch: hackathon/agentgate"
Write-Host "4. Root Directory: agentgate"
Write-Host "5. Runtime: Docker"
Write-Host "6. Health check path: /health"
Write-Host "7. Environment variables:"
Write-Host "   SELF_KEEPALIVE_ENABLED=true"
Write-Host "   SELF_KEEPALIVE_INTERVAL_SEC=25"
Write-Host "   LLM_ENABLED=true"
Write-Host "   OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free"
Write-Host "   OPENROUTER_API_KEY=<your-rotated-key>"
Write-Host "   PUBLIC_BASE_URL=https://<your-service>.onrender.com"
Write-Host ""
Write-Host "8. After first deploy, set PUBLIC_BASE_URL to the live URL and redeploy once."
Write-Host ""

if ($PublicUrl) {
    Write-Host "Verifying $PublicUrl ..." -ForegroundColor Yellow
    $endpoints = @(
        "$PublicUrl/health",
        "$PublicUrl/skill.md"
    )
    foreach ($url in $endpoints) {
        try {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 60
            Write-Host "OK $($r.StatusCode) $url" -ForegroundColor Green
        } catch {
            Write-Host "FAIL $url : $_" -ForegroundColor Red
        }
    }

    $body = '{"task_description":"Book flight to Paris"}'
    try {
        $r = Invoke-RestMethod -Uri "$PublicUrl/evaluate-task" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 60
        Write-Host "OK evaluate-task status=$($r.status)" -ForegroundColor Green
    } catch {
        Write-Host "FAIL evaluate-task: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Registry URLs (copy to NANDA Town form):" -ForegroundColor Cyan
if ($PublicUrl) {
    Write-Host "GET  $PublicUrl/health"
    Write-Host "POST $PublicUrl/evaluate-task"
    Write-Host "POST $PublicUrl/compare-options"
    Write-Host "GET  $PublicUrl/skill.md"
} else {
    Write-Host "Re-run: .\scripts\deploy-agentgate.ps1 -PublicUrl https://agentgate-xxx.onrender.com"
}
