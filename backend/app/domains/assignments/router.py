from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import DbSession, require_staff
from app.domains.assignments.schemas import StaffAssignmentSetup, StaffAssignmentSetupUpdate
from app.domains.assignments.service import get_staff_setup, update_staff_setup

router = APIRouter(
    prefix="/staff/courses/{course_id}/assignments",
    tags=["staff-assignments"],
    dependencies=[Depends(require_staff)],
)


@router.get("/{assignment_id}/setup", response_model=StaffAssignmentSetup)
def read_assignment_setup(
    course_id: str,
    assignment_id: str,
    db: DbSession,
) -> StaffAssignmentSetup:
    setup = get_staff_setup(db, course_id, assignment_id)
    if setup is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    return setup


@router.put("/{assignment_id}/setup", response_model=StaffAssignmentSetup)
def write_assignment_setup(
    course_id: str,
    assignment_id: str,
    payload: StaffAssignmentSetupUpdate,
    db: DbSession,
) -> StaffAssignmentSetup:
    setup = update_staff_setup(db, course_id, assignment_id, payload)
    if setup is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    return setup
