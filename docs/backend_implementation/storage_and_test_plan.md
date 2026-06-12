# Storage And Test Architecture Plan

This file is the canonical M1 plan for assignment config storage, grading assets, pytest scoring, and derived test projections. The canonical config schema is auto-generated and stored in [config_v1.schema.json](file:///c:/Users/Jaxon/coding/autograder_v1/docs/schemas/config_v1.schema.json).

## Canonical Storage Model

- PostgreSQL stores product metadata and the canonical internal grading definition in `assignment_configs.config_json`.
- `assignment_configs.config_json` is app-owned and wizard-authored in M1. Raw `config.json` import, export, and direct editing are out of scope.
- Assignment file bodies live behind the `assignment_artifacts` storage abstraction, not inside config JSON and not as database blobs.
- M1 assignment artifact types are `pytest_file`, `model_solution`, and `support_file`.
- `AssignmentArtifact` metadata stays lightweight: assignment linkage, stable artifact key, artifact type, generated storage reference, optional sanitized display filename, and validation metadata as needed.
- `config_json` is not an `AssignmentArtifact` class. The canonical config lives in `assignment_configs.config_json`.
- Student submissions, extracted files, Judge0 payloads, pytest tracebacks, generated feedback bodies, and execution workspaces remain ephemeral and must not become assignment artifacts or long-lived database records.

## Assignment Test Model

- M1 allows one or more `pytest_file` artifacts per assignment.
- UI-visible test cases are scoring items from `assignment_configs.config_json`, not separate physical test files.
- Each config scoring entry has at least:
  - stable `key`
  - human-facing `label`
  - `points`
  - `extra_credit`
- Config test keys and marker suffixes use the same stable slug. The pytest marker is derived as `ag_<key>` and is not stored separately. For example, `key: "handles_empty_input"` maps to `@pytest.mark.ag_handles_empty_input`.
- One scoring item may map to multiple pytest functions when those functions share the same `ag_<key>` marker.
- Default scoring is implicit: a scoring item contributes its `points` only when all pytest functions with its derived marker pass. Non-extra-credit items define the base total; passed extra-credit items add points above that base total.
- Assignments that require "complete at least X of these Y objectives" use an optional `completion_requirements` section that names existing scoring-item keys and a `minimum_passed` count. Completion requirements report whether the objective threshold is met; they do not replace scoring-item points.
- Hidden tests are not supported in M1. All M1 scoring entries are visible in staff and sandbox result surfaces.
- `test_cases` and `scoring_items` rows are derived projections used only for UI, validation, and query convenience. They are regenerated from canonical config and are never editable grading truth.

Example optional completion requirement:

```json
"completion_requirements": [
  {
    "key": "complete_three_practice_objectives",
    "label": "Complete at least three practice objectives",
    "test_keys": ["loops", "strings", "lists", "conditionals", "functions"],
    "minimum_passed": 3
  }
]
```

## Runtime Flow

1. Staff create or edit assignment grading setup through the wizard.
2. The backend validates and stores the canonical grading definition in `assignment_configs.config_json`.
3. Staff upload or edit the assignment pytest files, model solution files, and support files through assignment artifact storage.
4. Strict preflight validation verifies config-to-artifact-to-marker consistency before model-solution validation or grading:
   - supported `schema_version`
   - duplicate config keys
   - missing `ag_<key>` markers in the pytest files
   - missing assignment pytest artifacts
   - invalid point values
   - missing or invalid `extra_credit` booleans
   - invalid `completion_requirements` references or thresholds
   - missing bundle entrypoint or required-file rules
   - unsupported artifact types
5. Derived `test_cases` and `scoring_items` rows are regenerated from `assignment_configs.config_json` after setup changes.
6. Official and sandbox grading copy assignment artifacts plus the student bundle into an ephemeral execution workspace.
7. Judge0/Kata runs pytest in the isolated workspace.
8. Pytest results are mapped back to config scoring entries by `ag_<key>` marker.
9. Staff or sandbox responses are shaped from grounded pytest results and sanitized metadata.
10. Ephemeral workspaces, copied assignment artifacts, student files, Judge0 execution artifacts, tracebacks, and generated feedback bodies are cleaned up according to the zero-retention contract.

## Non-Goals

- No raw config import, export, download, or direct editing in M1.
- No file-per-test-case requirement.
- No database-authored test bodies.
- No hidden tests in M1.
- No persistent student submissions, raw filenames, tracebacks, Judge0 payloads, detailed feedback bodies, or sandbox artifacts.
- No separate simple test-case editor in M1.
- No manual grade overrides, plagiarism workflows, multi-language execution, compiled-language build pipelines, or Canvas grade passback in the M1 config contract (manual grading is supported only via non-executed rubric placeholders).
