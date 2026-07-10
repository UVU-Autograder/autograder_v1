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
    module_name: str | None = None


class StaffAssignmentListResponse(BaseModel):
    course_id: str
    assignments: list[StaffAssignmentSummary]


class ModuleConfig(BaseModel):
    id: int | None = None
    name: str
    concepts: list[str] = Field(default_factory=list)


class CourseConceptsUpdate(BaseModel):
    default_concepts: list[str]
    modules: list[ModuleConfig] = Field(default_factory=list)


class CourseConceptsResponse(BaseModel):
    course_id: str
    default_concepts: list[str]
    modules: list[ModuleConfig] = Field(default_factory=list)


class StaffSectionSummary(BaseModel):
    id: int
    crn: str
    is_active: bool


class StaffSectionListResponse(BaseModel):
    course_id: str
    sections: list[StaffSectionSummary]

