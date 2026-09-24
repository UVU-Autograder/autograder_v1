# smoke_test.ps1 — quick deployment health check for UVU Autograder host
# Usage: .\scripts\smoke_test.ps1 [-Host "127.0.0.1"]

param (
    [string]$TargetHost = "127.0.0.1"
)

$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$script:pass = 0
$script:fail = 0

function Check-Endpoint($label, $url, $expectStatus) {
    try {
        $response = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        $code = [int]$response.StatusCode
    } catch {
        if ($_.Exception.Response) {
            $code = [int]$_.Exception.Response.StatusCode
        } else {
            $code = 0
        }
    }

    if ($code -eq $expectStatus) {
        Write-Host "  [OK] ${label}: HTTP $code" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "  [FAIL] ${label}: HTTP $code (expected $expectStatus)" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host "=== UVU Autograder Smoke Test ===" -ForegroundColor Cyan
Write-Host "Host: $TargetHost`n"

Write-Host "[Backend API]" -ForegroundColor Yellow
Check-Endpoint "Health endpoint" "http://${TargetHost}:8000/health" 200
Check-Endpoint "API via Nginx" "http://${TargetHost}/health" 200

Write-Host "[Frontend]" -ForegroundColor Yellow
Check-Endpoint "Sandbox page" "http://${TargetHost}/sandbox" 200
Check-Endpoint "Login redirect" "http://${TargetHost}/staff/login" 200

if ($TargetHost -eq "127.0.0.1" -or $TargetHost -eq "localhost") {
    Write-Host "[Docker Services]" -ForegroundColor Yellow
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $composeFile = Join-Path $RepoRoot "docker-compose.yml"
        $psOutput = docker compose -f $composeFile ps 2>$null
        $unhealthy = ($psOutput | Select-String -Pattern "Restarting|unhealthy|Exited \([1-9]").Count
        $total = (docker compose -f $composeFile ps -q 2>$null).Count
        if ($total -eq 0) {
            Write-Host "  [FAIL] Docker services are stopped (0 containers running)" -ForegroundColor Red
            $script:fail++
        } elseif ($unhealthy -eq 0) {
            Write-Host "  [OK] All $total containers healthy" -ForegroundColor Green
            $script:pass++
        } else {
            Write-Host "  [FAIL] $unhealthy container(s) unhealthy or restarting" -ForegroundColor Red
            $script:fail++
        }
    } else {
        Write-Host "  - Docker not available (skipped)" -ForegroundColor Gray
    }
}

$totalChecks = $script:pass + $script:fail
Write-Host "`nResult: $($script:pass)/$totalChecks checks passed"

if ($script:fail -gt 0) {
    exit 1
} else {
    exit 0
}
