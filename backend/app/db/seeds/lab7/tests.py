"""Autograding test suite for Lab 7: Data Classes."""

import contextlib
import io

import pytest
from python_autograder_helpers import import_student_modules


@pytest.mark.ag_dataclass
def test_dataclass() -> None:
    """Verify @dataclass(order=True) with correct typed fields and default_factory list."""
    (student_mod,) = import_student_modules("student")
    Student = student_mod.Student

    s1 = Student(101, "Alice", "CS")
    assert s1.id == 101
    assert s1.name == "Alice"
    assert s1.major == "CS"
    assert isinstance(s1.courses, list)
    assert len(s1.courses) == 0

    s2 = Student(102, "Bob", "SE")
    assert s1.courses is not s2.courses, "courses list must use default_factory so instances do not share lists"


@pytest.mark.ag_methods
def test_methods() -> None:
    """Verify enroll() and total_courses() methods on Student."""
    (student_mod,) = import_student_modules("student")
    Student = student_mod.Student

    s = Student(101, "Alice", "CS")
    assert s.total_courses() == 0

    s.enroll("CS 1410")
    s.enroll("CS 2300")
    assert s.total_courses() == 2
    assert "CS 1410" in s.courses
    assert "CS 2300" in s.courses


@pytest.mark.ag_ordering
def test_ordering() -> None:
    """Verify comparison operators and ID sorting on Student dataclass."""
    (student_mod,) = import_student_modules("student")
    Student = student_mod.Student

    s1 = Student(101, "Alice", "CS")
    s2 = Student(102, "Bob", "SE")
    s3 = Student(100, "Charlie", "DS")

    assert s3 < s1
    assert s2 > s1

    sorted_list = sorted([s1, s2, s3])
    assert [s.id for s in sorted_list] == [100, 101, 102]


@pytest.mark.ag_main_output
def test_main_output() -> None:
    """Verify main() function executes and outputs Student test details."""
    (student_mod,) = import_student_modules("student")
    assert hasattr(student_mod, "main"), "student.py missing main function"

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        student_mod.main()

    stdout = f.getvalue()
    assert "Alice" in stdout or "courses" in stdout or "Student(" in stdout, (
        "main() output missing expected Student print statements"
    )
