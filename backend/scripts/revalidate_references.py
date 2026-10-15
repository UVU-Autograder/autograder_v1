"""Re-run reference validation for every assignment whose reference inventory is not ready.

Any change to the grader's runner or helper, a pinned dependency, or an instructor
file changes an assignment's execution fingerprint (assignments/inventory.py), and
the sandbox then refuses uploads with "Assignment requires instructor reference
validation before grading" until the model solution is graded again. This queues
the same task as the staff "Validate model solution" button, for each assignment
that needs it, and can wait for the outcome. It reads instructor files only.

From the stack's checkout on the Dell (no rebuild needed; the script is piped in):

    docker exec -i uvu-autograder-backend-1 python - --dry-run < backend/scripts/revalidate_references.py
    docker exec -i uvu-autograder-backend-1 python - --wait < backend/scripts/revalidate_references.py
"""

from __future__ import annotations

import argparse
import sys
import time

from sqlalchemy import select

from app.db.session import SessionLocal
from app.domains.assignments.inventory import inventory_status
from app.domains.assignments.models import Assignment
from app.domains.assignments.validation import run_preflight_validation
from app.domains.runs.tasks import get_run_result, get_run_state, set_run_state, validate_assignment_model_solution


def assignments_needing_validation(course: str | None, slug: str | None = None) -> list[tuple[str, str, str]]:
    """(course code, slug, inventory status) for every assignment that is not ready."""
    out = []
    with SessionLocal() as db:
        for assignment in db.scalars(select(Assignment)).all():
            if assignment.config is None or (course and assignment.course.code != course):
                continue
            if slug and assignment.slug != slug:
                continue
            try:
                status = inventory_status(db, assignment)
            except Exception as exc:  # noqa: BLE001 - report it, keep going
                status = f"error ({type(exc).__name__})"
            if status != "ready":
                out.append((assignment.course.code, assignment.slug, status))
    return sorted(out)


def queue(course_code: str, slug: str) -> list[str]:
    """Queue validation exactly as the staff endpoint does; returns preflight errors instead."""
    with SessionLocal() as db:
        errors = run_preflight_validation(db, course_code, slug)
    if errors:
        return errors
    set_run_state(f"val:{course_code}:{slug}", "queue")
    validate_assignment_model_solution.delay(course_code, slug)
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--course", help="only this course code, e.g. cs1410")
    parser.add_argument("--assignment", help="only this assignment slug, e.g. lab5")
    parser.add_argument("--dry-run", action="store_true", help="list what needs validation and stop")
    parser.add_argument("--wait", action="store_true", help="wait for every queued validation to finish")
    parser.add_argument("--timeout", type=float, default=900, help="seconds to wait in total (default 900)")
    args = parser.parse_args()

    pending = assignments_needing_validation(args.course, args.assignment)
    print(f"{len(pending)} assignment(s) need reference validation")
    for course_code, slug, status in pending:
        print(f"  {course_code}/{slug}: {status}")
    if args.dry_run or not pending:
        return 0

    queued = []
    for course_code, slug, _ in pending:
        errors = queue(course_code, slug)
        if errors:
            print(f"  NOT QUEUED {course_code}/{slug}: preflight failed: {'; '.join(errors)[:300]}")
        else:
            queued.append((course_code, slug))
    print(f"queued {len(queued)} validation(s)")
    if not args.wait:
        return 0

    deadline = time.monotonic() + args.timeout
    remaining = set(queued)
    failed = 0
    while remaining and time.monotonic() < deadline:
        for course_code, slug in sorted(remaining):
            run_id = f"val:{course_code}:{slug}"
            state = (get_run_state(run_id) or {}).get("state")
            if state not in ("complete", "failure"):
                continue
            remaining.discard((course_code, slug))
            result = get_run_result(run_id) or {}
            if state == "complete":
                print(f"  ok   {course_code}/{slug} ({result.get('score')}/{result.get('max_score')})")
            else:
                failed += 1
                print(f"  FAIL {course_code}/{slug}: {'; '.join(result.get('errors') or [])[:300]}")
        time.sleep(3)
    for course_code, slug in sorted(remaining):
        failed += 1
        print(f"  TIMEOUT {course_code}/{slug}: still running; check the staff page or run with --dry-run later")
    print(f"done: {len(queued) - failed} validated, {failed} not")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
