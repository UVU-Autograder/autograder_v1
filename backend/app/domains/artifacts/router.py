from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import DbSession, require_staff
from app.domains.artifacts.schemas import ArtifactListResponse
from app.domains.assignments.service import list_artifacts

router = APIRouter(
    prefix="/staff/courses/{course_id}/assignments",
    tags=["staff-artifacts"],
    dependencies=[Depends(require_staff)],
)


@router.get("/{assignment_id}/artifacts", response_model=ArtifactListResponse)
def get_assignment_artifacts(
    course_id: str,
    assignment_id: str,
    db: DbSession,
) -> ArtifactListResponse:
    artifacts = list_artifacts(db, course_id, assignment_id)
    if artifacts is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    return ArtifactListResponse(
        course_id=course_id,
        assignment_id=assignment_id,
        artifacts=artifacts,
    )
