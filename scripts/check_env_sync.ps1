# check_env_sync.ps1 — verify .env has every variable from .env.example
# Usage: .\scripts\check_env_sync.ps1 [-ActivePath "path/to/.env"]

param (
    [string]$ActivePath = ""
)

$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$ExamplePath = Join-Path $RepoRoot ".env.example"
if (-not $ActivePath) {
    $ActivePath = Join-Path $RepoRoot ".env"
}

if (-not (Test-Path $ExamplePath)) {
    Write-Error ".env.example not found at $ExamplePath"
    exit 1
}

if (-not (Test-Path $ActivePath)) {
    Write-Error ".env file not found at $ActivePath`nCopy .env.example to .env and configure secrets before deploying."
    exit 1
}

$errors = 0

function Get-EnvKeys($filePath) {
    $keys = @()
    Get-Content $filePath | ForEach-Object {
        $line = $_.Trim()
        if ($line -match '^[A-Z_][A-Z0-9_]*=') {
            $key = ($line -split '=', 2)[0]
            $keys += $key
        }
    }
    return ($keys | Sort-Object -Unique)
}

$exampleKeys = Get-EnvKeys $ExamplePath
$activeKeys = Get-EnvKeys $ActivePath

$missing = $exampleKeys | Where-Object { $_ -notin $activeKeys }
if ($missing) {
    Write-Host "MISSING from $ActivePath (present in .env.example):" -ForegroundColor Red
    foreach ($k in $missing) {
        Write-Host "  - $k" -ForegroundColor Red
        $errors++
    }
}

Get-Content $ActivePath | ForEach-Object {
    $line = $_.Trim()
    if ($line -match '^[A-Z_][A-Z0-9_]*=') {
        $parts = $line -split '=', 2
        $key = $parts[0]
        $val = $parts[1].Trim().Trim('"').Trim("'")
        if ($val -like "*change-me*" -or $val -like "*replace-with*") {
            Write-Host "PLACEHOLDER: $key=$val (needs a real value)" -ForegroundColor Yellow
            $errors++
        }
    }
}

if ($errors -eq 0) {
    Write-Host "OK: .env is in sync with .env.example ($($activeKeys.Count) variables checked)" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`nFAILED: $errors issue(s) found" -ForegroundColor Red
    exit 1
}
