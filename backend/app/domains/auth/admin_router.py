from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.core.dependencies import DbSession, require_role
from app.domains.auth.service import (
    create_admin_course,
    create_admin_section,
    deactivate_admin_course,
    deactivate_admin_section,
    get_admin_monitoring_metrics,
    grant_staff_access,
    list_admin_courses,
    list_admin_sections,
    list_staff_access,
    list_users,
    revoke_staff_access,
    update_admin_course,
    update_admin_section,
)

router = APIRouter(
    prefix="/staff/admin",
    tags=["staff-admin"],
    dependencies=[Depends(require_role(["admin"]))],
)

# --- Schemas ---

class CourseCreate(BaseModel):
    code: str
    title: str
    term: str
    default_concepts: list[str] = []
    instructor_email: str | None = None
    instructor_name: str | None = None
    ia_email: str | None = None
    ia_name: str | None = None


class CourseUpdate(BaseModel):
    code: str | None = None
    title: str | None = None
    term: str | None = None
    default_concepts: list[str] | None = None
    is_active: bool | None = None
    instructor_id: int | None = None
    ia_id: int | None = None
    instructor_email: str | None = None
    instructor_name: str | None = None
    ia_email: str | None = None
    ia_name: str | None = None


class CourseAdminDetail(BaseModel):
    id: int
    code: str
    title: str
    term: str
    is_active: bool
    instructor_id: int | None = None
    instructor_email: str | None = None
    ia_id: int | None = None
    ia_email: str | None = None
    default_concepts: list[str]
    section_count: int
    assignment_count: int


class SectionCreate(BaseModel):
    crn: str


class SectionUpdate(BaseModel):
    crn: str | None = None
    is_active: bool | None = None


class SectionAdminDetail(BaseModel):
    id: int
    course_id: int
    crn: str
    is_active: bool


class UserAdminDetail(BaseModel):
    id: int
    email: str
    display_name: str | None
    is_active: bool


class StaffAccessCreate(BaseModel):
    email: str
    display_name: str | None = None
    role_name: str
    course_id: int | None = None
    section_id: int | None = None


class StaffAccessResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    user_name: str | None
    role_id: int
    role_name: str
    course_id: int | None
    course_code: str | None
    section_id: int | None
    section_crn: str | None
    is_active: bool


class MonitoringResponse(BaseModel):
    active_runs_count: int
    queued_runs_count: int
    sandbox_runs_last_hour: int
    total_token_usage: int
    cleanup_service_healthy: bool = False
    cleanup_last_checked_at: str | None = None
    cleanup_failed_runs: int = 0
    cleanup_overdue_runs: int = 0
    cleanup_orphan_errors: int = 0
    dispatch_service_healthy: bool = False
    waiting_executions: int = 0
    active_executions: int = 0


# --- Routes ---

# Courses

@router.get("/courses", response_model=list[CourseAdminDetail])
def get_courses_admin(db: DbSession):
    return [CourseAdminDetail(**c) for c in list_admin_courses(db)]


@router.post("/courses", response_model=CourseAdminDetail, status_code=status.HTTP_201_CREATED)
def create_course_admin(payload: CourseCreate, db: DbSession):
    res = create_admin_course(
        db=db,
        code=payload.code,
        title=payload.title,
        term=payload.term,
        default_concepts=payload.default_concepts,
        instructor_email=payload.instructor_email,
        instructor_name=payload.instructor_name,
        ia_email=payload.ia_email,
        ia_name=payload.ia_name,
    )
    return CourseAdminDetail(**res)


@router.put("/courses/{course_id}", response_model=CourseAdminDetail)
def update_course_admin(course_id: int, payload: CourseUpdate, db: DbSession):
    res = update_admin_course(db, course_id, payload.model_dump(exclude_unset=True))
    return CourseAdminDetail(**res)


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_course_admin(course_id: int, db: DbSession):
    deactivate_admin_course(db, course_id)


# Sections

@router.get("/courses/{course_id}/sections", response_model=list[SectionAdminDetail])
def get_sections_admin(course_id: int, db: DbSession):
    sections = list_admin_sections(db, course_id)
    return [
        SectionAdminDetail(
            id=s.id,
            course_id=s.course_id,
            crn=s.crn,
            is_active=s.is_active,
        )
        for s in sections
    ]


@router.post("/courses/{course_id}/sections", response_model=SectionAdminDetail, status_code=status.HTTP_201_CREATED)
def create_section_admin(course_id: int, payload: SectionCreate, db: DbSession):
    section = create_admin_section(db, course_id, payload.crn)
    return SectionAdminDetail(
        id=section.id,
        course_id=section.course_id,
        crn=section.crn,
        is_active=section.is_active,
    )


@router.put("/sections/{section_id}", response_model=SectionAdminDetail)
def update_section_admin(section_id: int, payload: SectionUpdate, db: DbSession):
    section = update_admin_section(db, section_id, payload.crn, payload.is_active)
    return SectionAdminDetail(
        id=section.id,
        course_id=section.course_id,
        crn=section.crn,
        is_active=section.is_active,
    )


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_section_admin(section_id: int, db: DbSession):
    deactivate_admin_section(db, section_id)


# Users & Access

@router.get("/users", response_model=list[UserAdminDetail])
def get_users_admin(db: DbSession):
    users = list_users(db)
    return [
        UserAdminDetail(
            id=u.id,
            email=u.email,
            display_name=u.display_name,
            is_active=u.is_active,
        )
        for u in users
    ]


@router.get("/access", response_model=list[StaffAccessResponse])
def get_access_admin(db: DbSession):
    access_records = list_staff_access(db)
    return [
        StaffAccessResponse(
            id=access.id,
            user_id=access.user_id,
            user_email=access.user.email,
            user_name=access.user.display_name,
            role_id=access.role_id,
            role_name=access.role.name,
            course_id=access.course_id,
            course_code=access.course.code if access.course else None,
            section_id=access.section_id,
            section_crn=access.section.crn if access.section else None,
            is_active=access.is_active,
        )
        for access in access_records
    ]


@router.post("/access", response_model=StaffAccessResponse, status_code=status.HTTP_201_CREATED)
def grant_access_admin(payload: StaffAccessCreate, db: DbSession):
    role_lower = payload.role_name.lower()
    if role_lower != "admin":
        if role_lower in ("instructor", "teacher"):
            if payload.course_id is None:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="course_id is required for instructor access grants.",
                )
        else:
            if payload.section_id is None or payload.course_id is None:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="course_id and section_id are required for staff access grants.",
                )

    access = grant_staff_access(
        db=db,
        email=payload.email,
        display_name=payload.display_name,
        role_name=payload.role_name,
        course_id=payload.course_id,
        section_id=payload.section_id,
    )
    return StaffAccessResponse(
        id=access.id,
        user_id=access.user_id,
        user_email=access.user.email,
        user_name=access.user.display_name,
        role_id=access.role_id,
        role_name=access.role.name,
        course_id=access.course_id,
        course_code=access.course.code if access.course else None,
        section_id=access.section_id,
        section_crn=access.section.crn if access.section else None,
        is_active=access.is_active,
    )


@router.delete("/access/{access_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_access_admin(access_id: int, db: DbSession):
    revoke_staff_access(db, access_id)


# Monitoring

@router.get("/monitoring", response_model=MonitoringResponse)
def get_monitoring_admin(db: DbSession):
    metrics = get_admin_monitoring_metrics(db)
    return MonitoringResponse(**metrics)
