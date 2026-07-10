from pydantic import BaseModel

from app.domains.assignments.schemas import ArtifactMetadata


class ArtifactListResponse(BaseModel):
    course_id: str
    assignment_id: str
    artifacts: list[ArtifactMetadata]
