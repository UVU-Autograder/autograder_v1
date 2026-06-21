from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from fastapi.responses import StreamingResponse
import io

from app.core.dependencies import DbSession, require_staff
from app.domains.artifacts.schemas import ArtifactListResponse
from app.domains.assignments.schemas import ArtifactMetadata
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


@router.post("/{assignment_id}/artifacts", response_model=ArtifactMetadata)
async def upload_assignment_artifact(
    course_id: str,
    assignment_id: str,
    db: DbSession,
    artifact_key: str = Form(...),
    artifact_type: str = Form(...),
    file: UploadFile = File(...),
) -> ArtifactMetadata:
    content = await file.read()
    from app.domains.assignments.service import save_artifact

    artifact = save_artifact(
        db=db,
        course_code=course_id,
        assignment_slug=assignment_id,
        artifact_key=artifact_key,
        artifact_type=artifact_type,
        display_filename=file.filename or artifact_key,
        file_content=content,
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    return artifact


@router.delete("/{assignment_id}/artifacts/{artifact_key}")
def delete_assignment_artifact(
    course_id: str,
    assignment_id: str,
    artifact_key: str,
    db: DbSession,
):
    from app.domains.assignments.service import delete_artifact

    success = delete_artifact(db, course_id, assignment_id, artifact_key)
    if not success:
        raise HTTPException(status_code=404, detail="Artifact or Assignment not found.")
    return {"status": "success", "message": f"Artifact '{artifact_key}' deleted."}


@router.get("/{assignment_id}/artifacts/{artifact_key}")
def download_assignment_artifact(
    course_id: str,
    assignment_id: str,
    artifact_key: str,
    db: DbSession,
) -> StreamingResponse:
    from app.domains.assignments.service import get_artifact_content

    res = get_artifact_content(db, course_id, assignment_id, artifact_key)
    if res is None:
        raise HTTPException(status_code=404, detail="Artifact not found.")

    content, filename = res
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
