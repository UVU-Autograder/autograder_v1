from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.dependencies import DbSession, assert_course_section_access, require_staff
from app.domains.auth.models import User
from app.domains.ingestion.schemas import OfficialRunResponse
from app.domains.ingestion.service import IngestError, ingest_official_canvas_zip

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
    section_id: int = Form(...),
    current_user: User = Depends(require_staff),
) -> OfficialRunResponse:
    assert_course_section_access(
        db, current_user, course_code=course_id, section_id=section_id
    )

    content = await file.read()
    try:
        run = ingest_official_canvas_zip(
            db,
            course_id=course_id,
            assignment_id=assignment_id,
            section_id=section_id,
            actor_user_id=current_user.id,
            filename=file.filename or "",
            content=content,
        )
    except IngestError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return OfficialRunResponse(
        run_id=str(run.id),
        status=run.status,
        workflow_type=run.workflow_type,
        total_submission_count=run.total_submission_count,
        created_at=run.created_at,
    )
