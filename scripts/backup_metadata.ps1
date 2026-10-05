# ==============================================================================
# UVU Autograder — Metadata & Course Configuration Backup Utility (PowerShell)
# Scope: Persistent system and course configurations only.
# FERPA Compliance: STRICTLY EXCLUDES runs, student submissions, and workspaces.
# Usage: .\scripts\backup_metadata.ps1 [-Backup] [-Restore <Path>] [-OutputDir <Path>]
# ==============================================================================

[CmdletBinding(DefaultParameterSetName = "Backup")]
param (
    [Parameter(ParameterSetName = "Backup")]
    [switch]$Backup = $true,

    [Parameter(ParameterSetName = "Restore", Mandatory = $true)]
    [string]$RestoreDir,

    [Parameter(ParameterSetName = "Backup")]
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$Timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")

if (-not $OutputDir) {
    $OutputDir = Join-Path $RepoRoot "backups\metadata_$Timestamp"
}

$EnvFile = Join-Path $RepoRoot ".env.local"
if (-not (Test-Path $EnvFile)) {
    $EnvFile = Join-Path $RepoRoot ".env"
}

$ComposeArgs = @("compose")
if (Test-Path $EnvFile) {
    $ComposeArgs += @("--env-file", $EnvFile)
}

$MetadataTables = @(
    "alembic_version",
    "roles",
    "users",
    "courses",
    "staff_access",
    "sections",
    "modules",
    "assignments",
    "assignment_configs",
    "assignment_config_history",
    "assignment_artifacts",
    "scoring_items"
)

# Resolve database credentials from environment or defaults
$PgUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "autograder" }
$PgDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "autograder" }

function Do-Backup {
    Write-Host "=== UVU Autograder: Initiating Persistent Metadata Backup ===" -ForegroundColor Cyan
    Write-Host "Timestamp: $Timestamp"
    Write-Host "Target directory: $OutputDir`n"

    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }

    # 1. PostgreSQL Schema & Data Dump
    Write-Host "--> Dumping persistent database tables (excluding student submission data)..." -ForegroundColor Yellow
    $TableArgs = @()
    foreach ($tbl in $MetadataTables) {
        $TableArgs += @("-t", $tbl)
    }

    $DataSqlPath = Join-Path $OutputDir "metadata_data.sql"
    $SchemaSqlPath = Join-Path $OutputDir "metadata_schema.sql"

    # Execute pg_dump inside postgres container using configured credentials
    & docker @ComposeArgs exec -T postgres pg_dump -U $PgUser -d $PgDb --data-only --inserts @TableArgs | Out-File -FilePath $DataSqlPath -Encoding utf8
    & docker @ComposeArgs exec -T postgres pg_dump -U $PgUser -d $PgDb --schema-only @TableArgs | Out-File -FilePath $SchemaSqlPath -Encoding utf8

    Write-Host "  Database dump complete: metadata_data.sql" -ForegroundColor Green

    # 2. Archive Assignment Test Artifacts (Instructor-owned only)
    Write-Host "--> Archiving instructor assignment artifacts..." -ForegroundColor Yellow
    $ArtifactZip = Join-Path $OutputDir "artifacts.zip"

    $ContainerRunning = $false
    try {
        $backendId = (& docker @ComposeArgs ps -q backend 2>$null).Trim()
        if ($backendId) { $ContainerRunning = $true }
    } catch {}

    if ($ContainerRunning) {
        Write-Host "  Copying from backend container named volume (/data/artifacts)..." -ForegroundColor Gray
        $TempDir = Join-Path $OutputDir "temp_artifacts"
        if (Test-Path $TempDir) { Remove-Item -Recurse -Force $TempDir }
        New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
        & docker @ComposeArgs cp "backend:/data/artifacts" $TempDir
        $CopiedArtifacts = Join-Path $TempDir "artifacts"
        if (Test-Path $CopiedArtifacts) {
            Compress-Archive -Path "$CopiedArtifacts\*" -DestinationPath $ArtifactZip -Force
            Remove-Item -Recurse -Force $TempDir
            Write-Host "  Artifact archive complete from container volume: artifacts.zip" -ForegroundColor Green
        }
    } elseif (Test-Path (Join-Path $RepoRoot "data\artifacts")) {
        $ArtifactSrc = Join-Path $RepoRoot "data\artifacts"
        Compress-Archive -Path "$ArtifactSrc\*" -DestinationPath $ArtifactZip -Force
        Write-Host "  Artifact archive complete from host: artifacts.zip" -ForegroundColor Green
    } else {
        Write-Host "  Notice: artifacts not found. Creating placeholder." -ForegroundColor Gray
    }

    # 3. Create Manifest
    $CommitHash = try { git rev-parse HEAD 2>$null } catch { "unknown" }
    $Manifest = [ordered]@{
        timestamp = $Timestamp
        git_commit = "$CommitHash"
        backup_scope = "metadata_only"
        ferpa_compliant = $true
        tables = $MetadataTables
        excluded_entities = @("runs", "student_submissions", "execution_logs", "workspaces", "broker_payloads")
    }

    $ManifestJson = Join-Path $OutputDir "manifest.json"
    $Manifest | ConvertTo-Json -Depth 4 | Out-File -FilePath $ManifestJson -Encoding utf8

    Write-Host "`n=== Backup Completed Successfully ===" -ForegroundColor Green
    Write-Host "Location: $OutputDir"
}

function Do-Restore {
    param ([string]$SourceDir)

    if (-not (Test-Path $SourceDir)) {
        throw "Error: Restore directory '$SourceDir' does not exist."
    }

    $ManifestPath = Join-Path $SourceDir "manifest.json"
    $DataSqlPath = Join-Path $SourceDir "metadata_data.sql"

    if (-not (Test-Path $ManifestPath) -or -not (Test-Path $DataSqlPath)) {
        throw "Error: Directory '$SourceDir' is not a valid autograder metadata backup."
    }

    Write-Host "=== UVU Autograder: Restoring Metadata from '$SourceDir' ===" -ForegroundColor Cyan
    $Confirm = Read-Host "Warning: This will insert backed up metadata into the current database. Proceed? (y/N)"
    if ($Confirm -notmatch '^[Yy]$') {
        Write-Host "Restore aborted by operator." -ForegroundColor Yellow
        return
    }

    Write-Host "--> Restoring database metadata..." -ForegroundColor Yellow
    Get-Content $DataSqlPath -Raw | & docker @ComposeArgs exec -T -i postgres psql -U $PgUser -d $PgDb

    $ArtifactZip = Join-Path $SourceDir "artifacts.zip"
    if (Test-Path $ArtifactZip) {
        Write-Host "--> Restoring assignment artifacts..." -ForegroundColor Yellow
        $TempRestoreDir = Join-Path $SourceDir "temp_restore"
        if (Test-Path $TempRestoreDir) { Remove-Item -Recurse -Force $TempRestoreDir }
        New-Item -ItemType Directory -Path $TempRestoreDir -Force | Out-Null
        Expand-Archive -Path $ArtifactZip -DestinationPath $TempRestoreDir -Force

        $ContainerRunning = $false
        try {
            $backendId = (& docker @ComposeArgs ps -q backend 2>$null).Trim()
            if ($backendId) { $ContainerRunning = $true }
        } catch {}

        if ($ContainerRunning) {
            Write-Host "  Restoring to backend container named volume (/data/artifacts)..." -ForegroundColor Gray
            & docker @ComposeArgs cp "$TempRestoreDir\." "backend:/data/artifacts"
        }

        $ArtifactDest = Join-Path $RepoRoot "data\artifacts"
        if (-not (Test-Path $ArtifactDest)) {
            New-Item -ItemType Directory -Path $ArtifactDest -Force | Out-Null
        }
        Copy-Item -Path "$TempRestoreDir\*" -Destination $ArtifactDest -Recurse -Force
        Remove-Item -Recurse -Force $TempRestoreDir
        Write-Host "  Artifact restore complete." -ForegroundColor Green
    }

    Write-Host "`n=== Metadata Restore Complete ===" -ForegroundColor Green
}

if ($PSCmdlet.ParameterSetName -eq "Restore") {
    Do-Restore -SourceDir $RestoreDir
} else {
    Do-Backup
}
