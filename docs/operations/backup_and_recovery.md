# UVU Autograder — Metadata Backup & Disaster Recovery Guide

This guide establishes the backup scope, retention boundaries, automation, and disaster recovery procedures for the **UVU Autograder**.

---

## 1. FERPA Retention Boundary & Backup Scope

To strictly uphold university FERPA policies and the 24-hour physical data destruction lifecycle, backups are strictly scoped to **persistent configuration and instructor metadata only**.

### Included in Backups (Persistent Assets)
- **Database Tables**:
  - `roles`: Predefined authorization roles (`admin`, `instructor`, `IA`).
  - `users`: Staff identities and Azure OID bindings.
  - `staff_access`: Course and section role scoping.
  - `courses`: Course definitions, titles, terms, and concept taxonomies.
  - `sections`: Course section numbers and CRNs.
  - `modules`: Course modules and progressive concepts.
  - `assignments`: Assignment definitions, languages, Canvas refs, and sandbox settings.
  - `assignment_configs`: JSON configuration structures, grading rules, and test markers.
  - `assignment_artifacts`: Metadata for instructor-provided test suites and templates.
  - `alembic_version`: Database migration tracking state.
- **Filesystem Storage**:
  - `data/artifacts/`: Instructor-owned pytest suites, starter templates, and assignment assets.

### Strictly Excluded from Backups (Ephemeral / Student PII)
> [!CAUTION]
> Under no circumstances may student code or ephemeral grading outputs be backed up. Backing up student submissions violates FERPA minimization and retention policies.

- **Excluded Database Tables**:
  - `runs`: Student sandbox and official batch grading records.
  - `student_submissions`: Identifiable student code files and scores.
  - `execution_logs`: Console output, tracebacks, and AST diagnostics.
- **Excluded Storage**:
  - `data/workspaces/*`: Ephemeral container mounts and unpacked student files.
  - Celery/Redis queue state and task results.
  - Downloadable feedback zip files and grade export CSVs.

---

## 2. Executing a Metadata Backup

### On the Dell Host (Linux / Bash)
Run the automated backup script from the repository root:
```bash
./scripts/backup_metadata.sh --backup
```
By default, backups are written to `backups/metadata_<timestamp>/` containing:
- `metadata_data.sql`: INSERT statements for persistent metadata tables.
- `metadata_schema.sql`: DDL schema definitions for metadata tables.
- `artifacts.tar.gz`: Compressed archive of instructor test files.
- `manifest.json`: Verification manifest recording timestamp, git commit, table list, and FERPA exclusions.

### Specifying Custom Backup Locations
```bash
./scripts/backup_metadata.sh --output-dir /secure/storage/autograder_backup_$(date +%Y%m%d)
```

### On Windows / PowerShell
```powershell
.\scripts\backup_metadata.ps1
```

---

## 3. Automated Backup Scheduling (Cron)

On the workstation host, configure an automated daily metadata backup via `cron`:

```bash
# Open crontab for user dev
crontab -e
```

Add the following entry to execute daily at 2:00 AM:
```cron
0 2 * * * /home/dev/autograder_v1/scripts/backup_metadata.sh --output-dir /home/dev/backups/metadata_$(date +\%Y\%m\%d) >> /home/dev/backups/backup.log 2>&1
```

---

## 4. Disaster Recovery & Restoration Procedure

In the event of a host failure, corrupted database volume, or clean hardware migration:

### Step 1: Ensure Base Stack & Migrations Are Active
Before restoring data, the database container must be running and migrated to the current schema:
```bash
cd /home/dev/autograder_v1
docker compose up -d postgres
docker compose run --rm -T --no-deps --entrypoint alembic backend upgrade head
```

### Step 2: Execute the Restore Script
Provide the path to the verified backup directory:
```bash
./scripts/backup_metadata.sh --restore ./backups/metadata_20260923_163000
```
*(On Windows: `.\scripts\backup_metadata.ps1 -RestoreDir .\backups\metadata_20260923_163000`)*

The script will:
1. Verify the integrity of `manifest.json` and ensure it is a `metadata_only` backup.
2. Prompt the operator for confirmation.
3. Pipe `metadata_data.sql` into PostgreSQL.
4. Extract `artifacts.tar.gz` into `data/artifacts/`.

### Step 3: Verify Post-Restore Health
1. Verify course catalog and staff grants:
   ```bash
   docker compose exec -T backend python -c "from app.db.session import SessionLocal; from app.domains.courses.models import Course; db = SessionLocal(); print(f'Courses loaded: {db.query(Course).count()}')"
   ```
2. Verify that no ephemeral runs were restored (count must be 0):
   ```bash
   docker compose exec -T backend python -c "from app.db.session import SessionLocal; from app.domains.runs.models import Run; db = SessionLocal(); print(f'Runs present: {db.query(Run).count()}')"
   ```
3. Start the application stack:
   ```bash
   docker compose --env-file .env.local -f docker-compose.yml -f docker-compose.kata.yml up -d
   sudo systemctl restart autograder-frontend.service
   ```
4. Confirm `curl -fsS http://127.0.0.1/api/health` returns `{"status":"ok"}`.
