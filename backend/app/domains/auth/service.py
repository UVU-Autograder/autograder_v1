"""Auth and Admin Access Control Service.

Provides deep service methods for staff role grants, course/section administration,
and system monitoring metrics, removing direct DB querying from route handlers.
"""
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domains.assignments.models import Assignment
from app.domains.auth.models import Role, StaffAccess, User
from app.domains.courses.models import Course, Section
from app.domains.runs.models import RunSummary

# --- Access Control Service ---

def list_users(db: Session) -> list[User]:
    """Retrieve all users ordered by email."""
    return list(db.scalars(select(User).order_by(User.email)).all())


def list_staff_access(db: Session) -> list[StaffAccess]:
    """Retrieve all staff access records ordered by ID."""
    return list(db.scalars(select(StaffAccess).order_by(StaffAccess.id)).all())


def ensure_section_for_course_grant(db: Session, course_id: int) -> int:
    """Return an active section ID for course grants; create placeholder if needed."""
    section = db.scalar(
        select(Section)
        .where(Section.course_id == course_id, Section.is_active.is_(True))
        .order_by(Section.id)
    )
    if section is not None:
        return section.id

    section = Section(course_id=course_id, crn="00000", is_active=True)
    db.add(section)
    db.flush()
    return section.id


def get_or_create_user_and_grant_access(
    db: Session,
    email: str,
    name: str | None,
    role_name: str,
    course_id: int,
) -> int:
    """Helper to provision user and grant role access for a course."""
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

    section_id = ensure_section_for_course_grant(db, course_id)

    existing = db.scalar(
        select(StaffAccess)
        .where(
            StaffAccess.user_id == user.id,
            StaffAccess.role_id == role.id,
            StaffAccess.course_id == course_id,
            StaffAccess.section_id == section_id,
        )
    )
    if not existing:
        access = StaffAccess(
            user_id=user.id,
            role_id=role.id,
            course_id=course_id,
            section_id=section_id,
            is_active=True,
        )
        db.add(access)
    elif not existing.is_active:
        existing.is_active = True

    db.flush()
    return user.id


def grant_staff_access(
    db: Session,
    email: str,
    display_name: str | None,
    role_name: str,
    course_id: int | None = None,
    section_id: int | None = None,
) -> StaffAccess:
    """Grant staff role access."""
    clean_email = email.strip().lower()
    if not clean_email.endswith("@uvu.edu"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staff access must be granted to @uvu.edu addresses.",
        )

    role_lower = role_name.lower()
    if role_lower == "admin":
        pass
    elif role_lower in ("instructor", "teacher"):
        if course_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="course_id is required for instructor access grants.",
            )
        if section_id is None:
            section_id = ensure_section_for_course_grant(db, course_id)
    else:
        if course_id is None or section_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="course_id and section_id are required for staff access grants.",
            )

    if section_id is not None:
        section = db.get(Section, section_id)
        if section is None or (course_id is not None and section.course_id != course_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="section_id must belong to the given course_id.",
            )

    user = db.scalar(select(User).where(User.email == clean_email))
    if not user:
        user = User(email=clean_email, display_name=display_name, is_active=True)
        db.add(user)
        db.flush()

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
            StaffAccess.section_id == section_id,
        )
    )
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This staff access grant already exists.",
        )

    access = StaffAccess(
        user_id=user.id,
        role_id=role.id,
        course_id=course_id,
        section_id=section_id,
        is_active=True,
    )
    db.add(access)
    db.commit()
    db.refresh(access)
    return access


def revoke_staff_access(db: Session, access_id: int) -> None:
    """Revoke (deactivate) a staff access grant."""
    access = db.get(StaffAccess, access_id)
    if not access:
        raise HTTPException(status_code=404, detail="Access record not found.")
    access.is_active = False
    db.commit()


# --- Course & Section Admin Service ---

def list_admin_courses(db: Session) -> list[dict]:
    """Retrieve course administrative summaries."""
    courses = db.scalars(select(Course).order_by(Course.code)).all()
    results = []
    for c in courses:
        section_count = db.scalar(
            select(func.count(Section.id)).where(Section.course_id == c.id)
        ) or 0
        assignment_count = db.scalar(
            select(func.count(Assignment.id)).where(Assignment.course_id == c.id)
        ) or 0

        results.append({
            "id": c.id,
            "code": c.code,
            "title": c.title,
            "term": c.term,
            "is_active": c.is_active,
            "instructor_id": c.instructor_id,
            "instructor_email": c.instructor.email if c.instructor else None,
            "ia_id": c.ia_id,
            "ia_email": c.ia.email if c.ia else None,
            "default_concepts": c.default_concepts or [],
            "section_count": section_count,
            "assignment_count": assignment_count,
        })
    return results


def create_admin_course(
    db: Session,
    code: str,
    title: str,
    term: str,
    default_concepts: list[str],
    instructor_email: str | None = None,
    instructor_name: str | None = None,
    ia_email: str | None = None,
    ia_name: str | None = None,
) -> dict:
    """Create a new course record."""
    clean_code = code.strip().lower()
    existing = db.scalar(select(Course).where(Course.code == clean_code))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Course code '{code}' already exists.",
        )

    course = Course(
        code=clean_code,
        title=title.strip(),
        term=term.strip(),
        default_concepts=default_concepts,
        is_active=True,
    )
    db.add(course)
    db.flush()

    if instructor_email:
        instructor_id = get_or_create_user_and_grant_access(
            db, instructor_email, instructor_name, "instructor", course.id
        )
        course.instructor_id = instructor_id

    if ia_email:
        ia_id = get_or_create_user_and_grant_access(
            db, ia_email, ia_name, "IA", course.id
        )
        course.ia_id = ia_id

    db.commit()
    db.refresh(course)

    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "term": course.term,
        "is_active": course.is_active,
        "instructor_id": course.instructor_id,
        "instructor_email": course.instructor.email if course.instructor else None,
        "ia_id": course.ia_id,
        "ia_email": course.ia.email if course.ia else None,
        "default_concepts": course.default_concepts or [],
        "section_count": 0,
        "assignment_count": 0,
    }


def update_admin_course(db: Session, course_id: int, payload_dict: dict) -> dict:
    """Update existing course configuration."""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    if payload_dict.get("code") is not None:
        new_code = payload_dict["code"].strip().lower()
        if new_code != course.code:
            existing = db.scalar(select(Course).where(Course.code == new_code))
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Course code '{new_code}' already exists.",
                )
            course.code = new_code

    if payload_dict.get("title") is not None:
        course.title = payload_dict["title"].strip()
    if payload_dict.get("term") is not None:
        course.term = payload_dict["term"].strip()
    if payload_dict.get("default_concepts") is not None:
        course.default_concepts = payload_dict["default_concepts"]
    if payload_dict.get("is_active") is not None:
        course.is_active = payload_dict["is_active"]

    if payload_dict.get("instructor_id") is not None:
        if payload_dict["instructor_id"] == 0:
            course.instructor_id = None
        else:
            instructor = db.get(User, payload_dict["instructor_id"])
            if not instructor:
                raise HTTPException(status_code=400, detail="Instructor user not found.")
            course.instructor_id = payload_dict["instructor_id"]
    elif payload_dict.get("instructor_email") is not None:
        if not payload_dict["instructor_email"].strip():
            course.instructor_id = None
        else:
            instructor_id = get_or_create_user_and_grant_access(
                db, payload_dict["instructor_email"], payload_dict.get("instructor_name"), "instructor", course.id
            )
            course.instructor_id = instructor_id

    if payload_dict.get("ia_id") is not None:
        if payload_dict["ia_id"] == 0:
            course.ia_id = None
        else:
            ia = db.get(User, payload_dict["ia_id"])
            if not ia:
                raise HTTPException(status_code=400, detail="IA user not found.")
            course.ia_id = payload_dict["ia_id"]
    elif payload_dict.get("ia_email") is not None:
        if not payload_dict["ia_email"].strip():
            course.ia_id = None
        else:
            ia_id = get_or_create_user_and_grant_access(
                db, payload_dict["ia_email"], payload_dict.get("ia_name"), "IA", course.id
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

    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "term": course.term,
        "is_active": course.is_active,
        "instructor_id": course.instructor_id,
        "instructor_email": course.instructor.email if course.instructor else None,
        "ia_id": course.ia_id,
        "ia_email": course.ia.email if course.ia else None,
        "default_concepts": course.default_concepts or [],
        "section_count": section_count,
        "assignment_count": assignment_count,
    }


def deactivate_admin_course(db: Session, course_id: int) -> None:
    """Deactivate a course."""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    course.is_active = False
    db.commit()


def list_admin_sections(db: Session, course_id: int) -> list[Section]:
    """List sections for a given course."""
    return list(
        db.scalars(
            select(Section)
            .where(Section.course_id == course_id)
            .order_by(Section.crn)
        ).all()
    )


def create_admin_section(db: Session, course_id: int, crn: str) -> Section:
    """Create a new section for a course."""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    clean_crn = crn.strip()
    existing = db.scalar(
        select(Section)
        .where(Section.course_id == course_id, Section.crn == clean_crn)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Section CRN '{clean_crn}' already exists for this course.",
        )

    section = Section(
        course_id=course_id,
        crn=clean_crn,
        is_active=True,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


def update_admin_section(db: Session, section_id: int, crn: str | None, is_active: bool | None) -> Section:
    """Update section CRN or active state."""
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found.")

    if crn is not None:
        new_crn = crn.strip()
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

    if is_active is not None:
        section.is_active = is_active

    db.commit()
    db.refresh(section)
    return section


def deactivate_admin_section(db: Session, section_id: int) -> None:
    """Deactivate a section."""
    section = db.get(Section, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found.")
    section.is_active = False
    db.commit()


# --- System Monitoring Service ---

def get_admin_monitoring_metrics(db: Session) -> dict:
    """Aggregate aggregate monitoring metrics."""
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
        .where(RunSummary.token_usage_metadata.isnot(None))
    ).scalars().all()


    total_tokens = 0
    for meta in all_runs_with_tokens:
        if isinstance(meta, dict):
            total_tokens += meta.get("total_tokens", 0)

    from app.domains.runs.retention import health
    from app.domains.runs.dispatch_worker import healthy as dispatch_healthy
    from app.domains.runs.queue_admission import _count

    return {
        **health(db),
        "dispatch_service_healthy": dispatch_healthy(),
        "waiting_executions": _count(db, "waiting"),
        "active_executions": _count(db, "active"),
        "active_runs_count": active_runs,
        "queued_runs_count": queued_runs,
        "sandbox_runs_last_hour": sandbox_last_hour,
        "total_token_usage": total_tokens,
    }
