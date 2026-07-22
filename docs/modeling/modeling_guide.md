# UVU Autograder — Assignment Modeling Guide

This guide defines the repository and staff-UI workflow for modeling CS 1410
assignments.

## Seed package layout

Each modeled assignment has a directory under `backend/app/db/seeds/`.
Directory names are derived from the assignment slug by replacing hyphens with
underscores: `lab-1-image-processing` becomes `lab_1_image_processing`; `ds7`
stays `ds7`.

```text
backend/app/db/seeds/<folder>/
├── config_json.example.json
├── tests.py
├── <model solution source>
└── <assignment-specific support files>
```

Shared **test plumbing** belongs in `backend/app/db/seeds/shared/` and must be
declared as a `support_file` artifact. Current examples:

- `ds_test_helpers.py`: safe imports and cumulative DS regression plumbing
- `student_test_helpers.py`: isolated execution of student-authored pytest files
- `pygame_test_helpers.py`: headless Pygame execution and AST plumbing

Do not put assignment-specific expected values or rubric decisions in shared
helpers.

## Teacher UI versus repository-owned modeling

Staff can edit different layers through these surfaces:

- The assignment setup wizard edits scoring keys, labels, points, rubric groups,
  and manual rubric items.
- **Edit pytest** opens the primary `pytest_file` (`tests.py`) in Monaco.
- The Artifacts page can edit any pytest, model-solution, or support artifact.
- `cs1410_catalog.json` and seed package creation remain repository-owned.

Keep expected values, assertion bodies, cost/tax vectors, coordinate rules, and
other scoring decisions in the assignment's `tests.py`. This keeps the test
meaning visible in the primary teacher editor. Shared support files should only
hide mechanical details such as import guards, subprocess setup, or Pygame
mocking.

Later assignments may call a shared regression composer for earlier work (for
example, DS5 checks the DS4 contract). The assignment that introduces the
contract keeps its own marker tests explicit in `tests.py`.

## Configuration contract

`config_json.example.json` is schema v1. Its key sections are:

- `bundle.entrypoint` and `bundle.file_requirements`
  define the student ZIP contract.
- `execution.dependencies` lists runtime packages.
- `artifacts` contains `pytest_file`, `model_solution`, or `support_file`
  records. Each record names the file injected into grading.
- `tests` defines autograded scoring items.
- `manual_rubric_items` defines staff-scored items.

Every `tests[].key` maps to exactly one marker in `tests.py`:

```python
@pytest.mark.ag_calculate_cost
def test_calculate_cost():
    candy = Candy("Candy Corn", 1.5, 0.25)
    assert candy.calculate_cost() == pytest.approx(0.38)
```

Keep thresholds and filenames visible at the call site when using plumbing
helpers:

```python
@pytest.mark.ag_student_tests_pass
def test_student_tests_pass():
    assert_student_pytest_passes(
        "test_dessert.py",
        minimum=15,
        timeout_seconds=10,
    )
```

## CS1410 catalog and concepts

`backend/app/db/seeds/cs1410_catalog.json` owns module names, cumulative
`Module.concepts`, assignment slugs, titles, and module placement. The effective
AST whitelist remains:

```text
course.default_concepts ∪ assignment.module.concepts
```

Module concept arrays are intentionally cumulative. Add a catalog entry for a
new assignment before adding its deep seed package.

## Model solutions

Dessert Shop assignments are progressive and their model files intentionally
remain standalone. Copy the previous `dsN` model into the next seed package,
then implement the new requirements. Do not import a shared model module:
Judge0 and the student bundle contract expect assignment-local filenames such
as `dessert.py` and `dessertshop.py`.

## New assignment checklist

1. Confirm the assignment row and module placement in `cs1410_catalog.json`.
2. Create the slug-derived seed directory.
3. Add and validate `config_json.example.json`.
4. Keep rubric assertions in `tests.py`; add only plumbing helpers as
   `support_file` artifacts.
5. Ensure every `tests[].key` has a matching `ag_<key>` marker.
6. Add a standalone model solution and required resources.
7. Run seed integrity, persistence, preflight, and model-solution validation.
8. Smoke-test one sandbox run before marking the assignment modeled.

## Modeling cautions and assignment patterns

- **Package/Module Name Collisions (DS7 / Packaging):** When a student assignment includes a file with the same name as a PyPI library (e.g. `packaging.py`), pytest CLI imports can shadow PyPI standard libraries. Use `ds_test_helpers.import_student_modules` to dynamically isolate and manage student module imports during autograding test execution without breaking pytest initialization.
- **Enum vs String Parameter Handling (DS8 / Payment Methods):** In assignments introducing custom Enum types (e.g. `PayType`), student code may strictly validate inputs (`isinstance(method, PayType)` vs `"CARD"` string literals). Tests for payment method getters/setters should handle both `Enum` instances (`PayType.CARD`) and string literals (`"CARD"`) to accommodate student implementation variations without false negatives.
- **Structural Duck-Typing Protocols (DS10 / Combinable):** When testing Python `Protocol` interfaces (e.g. `@runtime_checkable` `Combinable`), verify duck-typing behavior (`can_combine` and `combine` methods) structurally rather than requiring explicit class inheritance on student classes (`Candy`, `Cookie`). Split regression checks into focused marked pytest functions for isolated scoring.

