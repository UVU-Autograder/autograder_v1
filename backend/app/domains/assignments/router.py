from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import DbSession, require_role, require_staff
from app.domains.assignments.schemas import (
    StaffAssignmentSetup,
    StaffAssignmentSetupUpdate,
    AssignmentCreate,
)
from app.domains.assignments.service import (
    get_staff_setup,
    update_staff_setup,
    create_assignment,
    deactivate_assignment,
    build_staff_setup,
)

router = APIRouter(
    prefix="/staff/courses/{course_id}/assignments",
    tags=["staff-assignments"],
    dependencies=[Depends(require_staff)],
)


@router.post(
    "",
    response_model=StaffAssignmentSetup,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(["admin", "instructor"]))],
)
def create_new_assignment(
    course_id: str,
    payload: AssignmentCreate,
    db: DbSession,
) -> StaffAssignmentSetup:
    try:
        assignment = create_assignment(db, course_id, payload)
        return build_staff_setup(assignment)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role(["admin", "instructor"]))],
)
def delete_assignment(
    course_id: str,
    assignment_id: str,
    db: DbSession,
):
    success = deactivate_assignment(db, course_id, assignment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found.",
        )
    return


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


@router.put(
    "/{assignment_id}/setup",
    response_model=StaffAssignmentSetup,
    dependencies=[Depends(require_role(["admin", "instructor"]))],
)
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


@router.post("/{assignment_id}/validate")
def validate_assignment(
    course_id: str,
    assignment_id: str,
    db: DbSession,
):
    from app.domains.assignments.validation import run_preflight_validation

    errors = run_preflight_validation(db, course_id, assignment_id)
    return {"passed": len(errors) == 0, "errors": errors}


@router.post("/{assignment_id}/validate-model-solution")
def validate_model_solution(
    course_id: str,
    assignment_id: str,
    db: DbSession,
):
    from app.domains.assignments.validation import run_preflight_validation

    errors = run_preflight_validation(db, course_id, assignment_id)
    if errors:
        raise HTTPException(
            status_code=400,
            detail={"message": "Preflight validation failed.", "errors": errors},
        )

    from app.domains.runs.tasks import validate_assignment_model_solution, set_run_state

    run_id = f"val:{course_id}:{assignment_id}"
    set_run_state(run_id, "queue")
    validate_assignment_model_solution.delay(course_id, assignment_id)

    return {"status": "queued", "run_id": run_id}


@router.get("/{assignment_id}/validation-status")
def get_validation_status(
    course_id: str,
    assignment_id: str,
):
    from app.domains.runs.tasks import get_run_state, get_run_result

    run_id = f"val:{course_id}:{assignment_id}"
    state_data = get_run_state(run_id)
    if state_data is None:
        return {"status": "idle", "errors": [], "score": 0, "max_score": 0}

    status = state_data.get("state", "idle")
    result_data = get_run_result(run_id)
    errors = []
    score = 0
    max_score = 0

    if result_data:
        errors = result_data.get("errors", [])
        score = result_data.get("score", 0)
        max_score = result_data.get("max_score", 0)
        # If task failed (e.g. timeout / exception) and we have state=failure,
        # ensure status is returned as failure
        if "errors" in result_data and status == "complete":
            status = "failure" if errors else "success"

    return {
        "status": status,
        "errors": errors,
        "score": score,
        "max_score": max_score,
    }
