from pydantic import BaseModel, Field


class StaffCourseSummary(BaseModel):
    id: str
    title: str
    term: str
    assignment_count: int = Field(ge=0)


class StaffCourseListResponse(BaseModel):
    courses: list[StaffCourseSummary]


class StaffAssignmentSummary(BaseModel):
    id: str
    course_id: str
    title: str
    language: str
    sandbox_enabled: bool
    base_points: int = Field(ge=0)
    extra_credit_points: int = Field(ge=0)


class StaffAssignmentListResponse(BaseModel):
    course_id: str
    assignments: list[StaffAssignmentSummary]
