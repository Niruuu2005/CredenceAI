# Smoke-test a deployed CredenceAI API (Render).
# Usage:
#   .\scripts\verify-deployment.ps1 -ApiUrl "https://credenceai-api.onrender.com"
#   .\scripts\verify-deployment.ps1 -ApiUrl "https://..." -ApiKey "cred_sk_..."

param(
    [Parameter(Mandatory = $true)]
    [string]$ApiUrl,

    [string]$ApiKey = ""
)

$base = $ApiUrl.TrimEnd("/")
$healthUrl = "$base/api/health"

Write-Host "Health check: $healthUrl"
try {
    $health = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 120
    Write-Host "OK: $($health | ConvertTo-Json -Compress)"
} catch {
    Write-Error "Health check failed: $_"
    exit 1
}

if ($ApiKey) {
    $validateUrl = "$base/api/auth/validate"
    Write-Host "API key validate: $validateUrl"
    try {
        $headers = @{ "X-API-Key" = $ApiKey }
        $valid = Invoke-RestMethod -Uri $validateUrl -Method Get -Headers $headers -TimeoutSec 60
        Write-Host "OK: $($valid | ConvertTo-Json -Compress)"
    } catch {
        Write-Error "API key validation failed: $_"
        exit 1
    }

    $jobsUrl = "$base/api/jobs"
    Write-Host "Job submit: $jobsUrl"
    try {
        $body = @{
            job_type = "search_query"
            query    = "smoke test"
            input    = "smoke test"
        } | ConvertTo-Json
        $headers = @{
            "X-API-Key"    = $ApiKey
            "Content-Type" = "application/json"
        }
        $job = Invoke-RestMethod -Uri $jobsUrl -Method Post -Headers $headers -Body $body -TimeoutSec 60
        Write-Host "OK: $($job | ConvertTo-Json -Compress)"
    } catch {
        Write-Error "Job submit failed: $_"
        exit 1
    }
} else {
    Write-Host "Skipping API key tests (pass -ApiKey cred_sk_... to test auth + jobs)."
}

Write-Host "Deployment verification passed."
