# Ensures deployment secrets are not committed and reminds rotation if exposed.
# Exit 0 = safe to proceed; exit 1 = possible secret leak in tracked files.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$excludeGlobs = @(
    "--glob", "!.git/**",
    "--glob", "!docs/**",
    "--glob", "!scripts/render-env.template.env",
    "--glob", "!scripts/check-secrets-not-committed.ps1",
    "--glob", "!*.md"
)

$patterns = @(
    "npg_[A-Za-z0-9]{8,}",
    "rediss://default:[^@\s]+@",
    "postgresql://[^:]+:[^@]+@ep-[a-z0-9-]+\."
)

$leaks = @()
foreach ($pattern in $patterns) {
    $matches = rg -n $pattern $root @excludeGlobs 2>$null
    if ($matches) { $leaks += $matches }
}

if ($leaks.Count -gt 0) {
    Write-Error "Possible secrets in tracked files:`n$($leaks -join "`n")"
    exit 1
}

Write-Host "OK: No Neon/Upstash connection strings found in the repository."
Write-Host ""
Write-Host "If credentials were pasted in chat or logs, rotate before deploy:"
Write-Host "  Neon:   Dashboard -> project -> Reset password -> new DATABASE_URL"
Write-Host "  Upstash: Dashboard -> Redis -> Reset credentials -> new REDIS_URL"
Write-Host "  Set both only in Render -> credenceai-api -> Environment (never commit)."
