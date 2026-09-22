from datetime import datetime

from pydantic import BaseModel


class OfficialRunResponse(BaseModel):
    run_id: str
    status: str
    workflow_type: str
    total_submission_count: int
    created_at: datetime
