# Storage And Test Architecture Plan

This file is the canonical plan for assignment config storage, grading assets, pytest scoring, and derived test projections. The canonical config schema is auto-generated and stored in [config_v1.schema.json](../schemas/config_v1.schema.json).

## Canonical Storage Model

- PostgreSQL stores product metadata and the canonical internal grading definition in `assignment_configs.config_json`.
- `assignment_configs.config_json` is app-owned and wizard-authored. The wizard is the authoring surface; config is an internal API/storage detail.
- Assignment file bodies live behind the `assignment_artifacts` storage abstraction, not inside config JSON and not as database blobs.
- Assignment artifact types are `pytest_file`, `model_solution`, and `support_file`.
- `AssignmentArtifact` metadata stays lightweight: assignment linkage, stable artifact key, artifact type, generated storage reference, optional sanitized display filename, and validation metadata as needed.
- `config_json` is not an `AssignmentArtifact` class. The canonical config lives in `assignment_configs.config_json`.
- Student submissions, extracted files, Judge0 payloads, pytest tracebacks, generated feedback bodies, and execution workspaces remain ephemeral. Official review/export artifacts may exist ≤24h or until staff cleanup; sandbox artifacts are wiped immediately after results (see canonical retention lifecycle in [technical_specs.md](../core/technical_specs.md#2-core-features)).

## Assignment Test Model

- One or more `pytest_file` artifacts per assignment are allowed.
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
- All scoring entries are visible in staff and sandbox result surfaces.
- `scoring_items` rows are derived projections used for UI, validation, and query convenience. They are regenerated from canonical config and are never editable grading truth.
- Manual rubric items (non-executed) are supported; backend persist + export regeneration exist; completing the in-app staff grader workflow is an active backlog item (see [backlog.md](../planning/backlog.md)).

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
4. Strict preflight validation verifies config-to-artifact-to-marker consistency before model-solution validation, and the same preflight runs for sandbox and official student grading pipelines. Preflight checks include:
   - supported `schema_version`
   - duplicate config keys
   - missing `ag_<key>` markers in the pytest files
   - missing assignment pytest artifacts
   - invalid point values
   - missing or invalid `extra_credit` booleans
   - invalid `completion_requirements` references or thresholds
   - missing bundle entrypoint or required-file rules
   - any required bundle path without a real `model_solution` artifact
   - execution dependencies outside the configured preinstalled allowlist
   - unsupported artifact types
5. Derived `scoring_items` rows are regenerated from `assignment_configs.config_json` after setup changes.
6. Official and sandbox grading place the student bundle and assignment artifacts into an ephemeral execution workspace.
7. Judge0/Kata requires Python 3.11+, imports every declared preinstalled dependency, then runs pytest in the isolated workspace via `execute_pytest_in_judge0`.
8. Pytest results are mapped back to config scoring entries by `ag_<key>` marker.
9. Staff or sandbox responses are shaped from grounded pytest results and sanitized metadata. Sandbox Local LLM explanations (when enabled) must not re-grade.
10. Workspaces and execution artifacts are cleaned up per the retention contract (sandbox immediate; official ≤24h or staff cleanup; Judge0/Kata immediate after retrieval).

## Non-Goals

- No file-per-test-case requirement.
- No database-authored test bodies.
- No persistent student submissions, raw filenames, tracebacks, Judge0 payloads, detailed feedback bodies, or sandbox download artifacts.
- No Canvas grade passback API in the config/storage contract (manual Canvas CSV import remains assumed).
