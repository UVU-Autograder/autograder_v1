import io
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile

from app.core.dependencies import DbSession, require_staff
from app.domains.auth.models import User
from app.domains.ingestion.schemas import OfficialRunResponse
from app.domains.ingestion.extractor import safe_extract_zip, group_canvas_files
from app.domains.assignments.service import get_assignment_for_course
from app.domains.runs.models import RunSummary

router = APIRouter(
    prefix="/staff/courses/{course_id}/assignments/{assignment_id}/submissions",
    tags=["staff-submissions"],
    dependencies=[Depends(require_staff)],
)


@router.post("/ingest", response_model=OfficialRunResponse)
async def ingest_canvas_submissions(
    course_id: str,
    assignment_id: str,
    db: DbSession,
    file: UploadFile = File(...),
    current_user: User = Depends(require_staff),
) -> OfficialRunResponse:
    # 1. Validate file extension/mime-type
    filename = file.filename or ""
    if not filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only ZIP files are accepted.",
        )

    # 2. Read content and validate size
    from app.core.settings import get_settings
    settings = get_settings()

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Upload size limit exceeded. Max size allowed is {settings.max_upload_bytes / (1024*1024):.1f}MB.",
        )

    # 3. Verify that assignment exists
    assignment = get_assignment_for_course(db, course_id, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")

    # 4. Perform extraction checks synchronously to block unsafe uploads
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        try:
            safe_extract_zip(content, tmp_path)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or unsafe ZIP file: {str(e)}",
            )

        # 5. Parse files to ensure at least some match the Canvas pattern
        grouped_files, unmatched = group_canvas_files(tmp_path)
        if not grouped_files:
            raise HTTPException(
                status_code=400,
                detail="The ZIP file does not contain recognized Canvas submissions. Ensure filenames match Canvas export format.",
            )

    # 6. Create database run record
    run = RunSummary(
        workflow_type="official",
        actor_user_id=current_user.id,
        assignment_id=assignment.id,
        status="queue",
        total_submission_count=len(grouped_files),
        success_count=0,
        warning_count=0,
        failure_count=0,
        timeout_count=0,
        failure_summary={},
        token_usage_metadata={},
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # 7. Save validated ZIP file to disk for asynchronous processing
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    workspaces_dir.mkdir(parents=True, exist_ok=True)

    zip_dest = workspaces_dir / f"official_{run.id}.zip"
    zip_dest.write_bytes(content)

    return OfficialRunResponse(
        run_id=str(run.id),
        status=run.status,
        workflow_type=run.workflow_type,
        total_submission_count=run.total_submission_count,
        created_at=run.created_at,
    )
