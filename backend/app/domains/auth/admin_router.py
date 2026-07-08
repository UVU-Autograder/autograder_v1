from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC

from app.core.dependencies import DbSession, require_role
from app.domains.auth.models import User, Role, StaffAccess
from app.domains.courses.models import Course, Section
from app.domains.assignments.models import Assignment
from app.domains.runs.models import RunSummary

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
    role_name: str  # admin, instructor, IA
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

# --- Routes ---

# Courses

@router.get("/courses", response_model=list[CourseAdminDetail])
def get_courses_admin(db: DbSession):
    courses = db.scalars(select(Course).order_by(Course.code)).all()
    results = []
    for c in courses:
        section_count = db.scalar(
            select(func.count(Section.id)).where(Section.course_id == c.id)
        ) or 0
        assignment_count = db.scalar(
            select(func.count(Assignment.id)).where(Assignment.course_id == c.id)
        ) or 0
        
        results.append(
            CourseAdminDetail(
                id=c.id,
                code=c.code,
                title=c.title,
                term=c.term,
                is_active=c.is_active,
                instructor_id=c.instructor_id,
                instructor_email=c.instructor.email if c.instructor else None,
                ia_id=c.ia_id,
                ia_email=c.ia.email if c.ia else None,
                default_concepts=c.default_concepts or [],
                section_count=section_count,
                assignment_count=assignment_count,
            )
        )
    return results

def _get_or_create_user_and_grant_access(
    db: Session,
    email: str,
    name: str | None,
    role_name: str,
    course_id: int,
) -> int:
    clean_email = email.strip().lower()
    if not clean_email.endswith("@uvu.edu"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staff access must be granted to @uvu.edu addresses.",
        )
        
    user = db.scalar(select(User).where(User.email == clean_email))
    if not user:
        user = User(email=clean_email, display_name=name, is_active=True)
        db.add(user)
        db.flush()
    elif name and not user.display_name:
        user.display_name = name
        
    role = db.scalar(select(Role).where(Role.name == role_name))
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_name}' does not exist.",
        )
        
    existing = db.scalar(
        select(StaffAccess)
        .where(
            StaffAccess.user_id == user.id,
            StaffAccess.role_id == role.id,
            StaffAccess.course_id == course_id,
        )
    )
    if not existing:
        access = StaffAccess(
            user_id=user.id,
            role_id=role.id,
            course_id=course_id,
            is_active=True,
        )
        db.add(access)
    elif not existing.is_active:
        existing.is_active = True
        
    db.flush()
    return user.id


@router.post("/courses", response_model=CourseAdminDetail, status_code=status.HTTP_201_CREATED)
def create_course_admin(payload: CourseCreate, db: DbSession):
    existing = db.scalar(select(Course).where(Course.code == payload.code.strip().lower()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course code '{payload.code}' already exists.",
        )
    
    course = Course(
        code=payload.code.strip().lower(),
        title=payload.title.strip(),
        term=payload.term.strip(),
        default_concepts=payload.default_concepts,
        is_active=True,
    )
    db.add(course)
    db.flush()

    if payload.instructor_email:
        instructor_id = _get_or_create_user_and_grant_access(
            db, payload.instructor_email, payload.instructor_name, "instructor", course.id
        )
        course.instructor_id = instructor_id

    if payload.ia_email:
        ia_id = _get_or_create_user_and_grant_access(
            db, payload.ia_email, payload.ia_name, "IA", course.id
        )
        course.ia_id = ia_id

    db.commit()
    db.refresh(course)
    
    # Calculate section and assignment counts (which are 0)
    return CourseAdminDetail(
        id=course.id,
        code=course.code,
        title=course.title,
        term=course.term,
        is_active=course.is_active,
        instructor_id=course.instructor_id,
        instructor_email=course.instructor.email if course.instructor else None,
        ia_id=course.ia_id,
        ia_email=course.ia.email if course.ia else None,
        default_concepts=course.default_concepts or [],
        section_count=0,
        assignment_count=0,
    )

@router.put("/courses/{course_id}", response_model=CourseAdminDetail)
def update_course_admin(course_id: int, payload: CourseUpdate, db: DbSession):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
        
    if payload.code is not None:
        new_code = payload.code.strip().lower()
        if new_code != course.code:
            existing = db.scalar(select(Course).where(Course.code == new_code))
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Course code '{new_code}' already exists.",
                )
            course.code = new_code
            
    if payload.title is not None:
        course.title = payload.title.strip()
    if payload.term is not None:
        course.term = payload.term.strip()
    if payload.default_concepts is not None:
        course.default_concepts = payload.default_concepts
    if payload.is_active is not None:
        course.is_active = payload.is_active
    if payload.instructor_id is not None:
        if payload.instructor_id == 0:
            course.instructor_id = None
        else:
            instructor = db.get(User, payload.instructor_id)
            if not instructor:
                raise HTTPException(status_code=400, detail="Instructor user not found.")
            course.instructor_id = payload.instructor_id
    elif payload.instructor_email is not None:
        if not payload.instructor_email.strip():
            course.instructor_id = None
        else:
            instructor_id = _get_or_create_user_and_grant_access(
                db, payload.instructor_email, payload.instructor_name, "instructor", course.id
            )
            course.instructor_id = instructor_id

    if payload.ia_id is not None:
        if payload.ia_id == 0:
            course.ia_id = None
        else:
            ia = db.get(User, payload.ia_id)
            if not ia:
                raise HTTPException(status_code=400, detail="IA user not found.")
            course.ia_id = payload.ia_id
    elif payload.ia_email is not None:
        if not payload.ia_email.strip():
            course.ia_id = None
        else:
            ia_id = _get_or_create_user_and_grant_access(
                db, payload.ia_email, payload.ia_name, "IA", course.id
            )
            course.ia_id = ia_id
            
    db.commit()
    db.refresh(course)
    
    section_count = db.scalar(
        select(func.count(Section.id)).where(Section.course_id == course.id)
    ) or 0
    assignment_count = db.scalar(
        select(func.count(Assignment.id)).where(Assignment.course_id == course.id)
    ) or 0
    
    return CourseAdminDetail(
        id=course.id,
        code=course.code,
        title=course.title,
        term=course.term,
        is_active=course.is_active,
        instructor_id=course.instructor_id,
        instructor_email=course.instructor.email if course.instructor else None,
        ia_id=course.ia_id,
        ia_email=course.ia.email if course.ia else None,
        default_concepts=course.default_concepts or [],
        section_count=section_count,
        assignment_count=assignment_count,
    )

@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_course_admin(course_id: int, db: DbSession):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    course.is_active = False
    db.commit()
    return

# Sections

@router.get("/courses/{course_id}/sections", response_model=list[SectionAdminDetail])
def get_sections_admin(course_id: int, db: DbSession):
    sections = db.scalars(
        select(Section)
        .where(Section.course_id == course_id)
        .order_by(Section.crn)
    ).all()
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
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
        
    existing = db.scalar(
        select(Section)
        .where(Section.course_id == course_id, Section.crn == payload.crn.strip())
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section CRN '{payload.crn}' already exists for this course.",
        )
        
    section = Section(
        course_id=course_id,
        crn=payload.crn.strip(),
        is_active=True,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return SectionAdminDetail(
        id=section.id,
        course_id=section.course_id,
        crn=section.crn,
        is_active=section.is_active,
    )

@router.put("/sections/{section_id}", response_model=SectionAdminDetail)
def update_section_admin(section_id: int, payload: SectionUpdate, db: DbSession):
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found.")
        
    if payload.crn is not None:
        new_crn = payload.crn.strip()
        if new_crn != section.crn:
            existing = db.scalar(
                select(Section)
                .where(Section.course_id == section.course_id, Section.crn == new_crn)
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Section CRN '{new_crn}' already exists for this course.",
                )
            section.crn = new_crn
            
    if payload.is_active is not None:
        section.is_active = payload.is_active
        
    db.commit()
    db.refresh(section)
    return SectionAdminDetail(
        id=section.id,
        course_id=section.course_id,
        crn=section.crn,
        is_active=section.is_active,
    )

@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_section_admin(section_id: int, db: DbSession):
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found.")
    section.is_active = False
    db.commit()
    return

# Users & Access

@router.get("/users", response_model=list[UserAdminDetail])
def get_users_admin(db: DbSession):
    users = db.scalars(select(User).order_by(User.email)).all()
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
    access_records = db.scalars(
        select(StaffAccess)
        .order_by(StaffAccess.id)
    ).all()
    
    results = []
    for access in access_records:
        results.append(
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
        )
    return results

@router.post("/access", response_model=StaffAccessResponse, status_code=status.HTTP_201_CREATED)
def grant_access_admin(payload: StaffAccessCreate, db: DbSession):
    email = payload.email.strip().lower()
    if not email.endswith("@uvu.edu"):
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staff access must be granted to @uvu.edu addresses.",
        )
        
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email, display_name=payload.display_name, is_active=True)
        db.add(user)
        db.flush()
        
    role = db.scalar(select(Role).where(Role.name == payload.role_name))
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{payload.role_name}' does not exist.",
        )
        
    existing = db.scalar(
        select(StaffAccess)
        .where(
            StaffAccess.user_id == user.id,
            StaffAccess.role_id == role.id,
            StaffAccess.course_id == payload.course_id,
            StaffAccess.section_id == payload.section_id,
        )
    )
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return StaffAccessResponse(
                id=existing.id,
                user_id=existing.user_id,
                user_email=existing.user.email,
                user_name=existing.user.display_name,
                role_id=existing.role_id,
                role_name=existing.role.name,
                course_id=existing.course_id,
                course_code=existing.course.code if existing.course else None,
                section_id=existing.section_id,
                section_crn=existing.section.crn if existing.section else None,
                is_active=existing.is_active,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This staff access grant already exists.",
        )
        
    access = StaffAccess(
        user_id=user.id,
        role_id=role.id,
        course_id=payload.course_id,
        section_id=payload.section_id,
        is_active=True,
    )
    db.add(access)
    db.commit()
    db.refresh(access)
    
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
    access = db.get(StaffAccess, access_id)
    if not access:
        raise HTTPException(status_code=404, detail="Access record not found.")
    access.is_active = False
    db.commit()
    return

# Monitoring

@router.get("/monitoring", response_model=MonitoringResponse)
def get_monitoring_admin(db: DbSession):
    active_runs = db.scalar(
        select(func.count(RunSummary.id)).where(RunSummary.status == "run")
    ) or 0
    
    queued_runs = db.scalar(
        select(func.count(RunSummary.id)).where(RunSummary.status == "queue")
    ) or 0
    
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    sandbox_last_hour = db.scalar(
        select(func.count(RunSummary.id))
        .where(
            RunSummary.workflow_type == "sandbox",
            RunSummary.created_at >= one_hour_ago,
        )
    ) or 0
    
    all_runs_with_tokens = db.execute(
        select(RunSummary.token_usage_metadata)
        .where(RunSummary.token_usage_metadata != None)
    ).scalars().all()
    
    total_tokens = 0
    for meta in all_runs_with_tokens:
        if isinstance(meta, dict):
            total_tokens += meta.get("total_tokens", 0)
            
    return MonitoringResponse(
        active_runs_count=active_runs,
        queued_runs_count=queued_runs,
        sandbox_runs_last_hour=sandbox_last_hour,
        total_token_usage=total_tokens,
    )
