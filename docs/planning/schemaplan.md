Revised CS 1410 Backend Schema Expansion Plan
Summary
Use the CS 1410 assignment report to expand the backend model beyond the current “one pytest file, flat pytest-only scoring items” shape. The goal is to support current CS 1410 assignments with minimal assignment changes, while still keeping assignment_configs.config_json canonical and avoiding frontend work in this slice.

The most important change is to treat the config as a richer assignment contract: submitted-file manifest, execution dependencies, support-file injection, multiple pytest artifacts, manual rubric placeholders, and optional rubric grouping. Relational tables should remain projections/query aids, not the source of truth.

Key Backend Changes
Extend AssignmentConfigV1 into a more flexible v1-compatible contract:
Allow multiple pytest*file artifacts instead of exactly one.
Add submission or bundle.file_requirements support for exact files, OR choices, optional files, wildcard-like patterns, and max submitted files.
Add root-folder normalization policy, defaulting to “auto-detect one top-level folder and flatten.”
Add execution.dependencies, such as pillow, pygame, tabulate, and pytest.
Add support_artifacts references for instructor-owned files copied into the execution workspace.
Add output_artifacts expectations for generated files such as bears2.jpg and bears3.jpg.
Add optional rubric_groups[] for display organization while keeping scoring items flat.
Add manual_rubric_items[] for reflections, code quality, and other non-pytest grading rows.
Add optional stdin_scenarios[] for deterministic console input tests later.
Keep assignment setup globally shared:
One courses row per course.
One shared assignments row per course assignment.
One canonical assignment_configs.config_json.
Staff section scope should control official run authority later, not create per-teacher assignment copies.
Replace or evolve derived test_cases into a more general derived projection:
Preferred: add a new scoring_items projection table with config_item_key, label, points, extra_credit, item_type, nullable pytest_marker, nullable rubric_group_key, and display_order.
Keep test_cases temporarily if needed for compatibility, but new work should use scoring_items.
Pytest-backed items derive marker ag*<key>.
Manual items have no marker and are excluded from automated scoring.
Keep assignment_artifacts as the file-body metadata table:
Permit many pytest artifacts.
Permit support files.
Permit multiple model solution files.
Do not store raw config JSON as an artifact.
CS 1410 Coverage Targets
Lab 1:
Code plus generated image outputs.
Requires bears2.py, bears3.py, bears2.jpg, bears3.jpg.
Needs output artifact validation and likely Pillow.
Labs 3, 4, 7:
Need OR file requirements for reflection .md or .pdf.
Add manual rubric placeholders for reflection grading.
Recommend nudging future instructions toward Markdown only.
Lab 6:
Needs pygame, user-provided image asset handling, and likely manual grading placeholder.
Mark as difficult/headless-limited unless assignment is lightly adjusted.
Dessert Shop 3:
Needs “student test suite validation” support later: run student tests against known-good and known-bad implementations.
For now, model this as a special pytest/meta-test assignment mode in config.
Dessert Shop 4-10:
Need up to 11 required submitted files.
Need tabulate.
Need multiple pytest artifacts.
DS 5-10 need deterministic stdin mocking support for interactive loops.
Immediate Implementation Slice
Do not touch frontend files.
Update docs to reflect the broader backend config direction:
docs/technical_specs.md
docs/backend_implementation/decisions.md
docs/backend_implementation/storage_and_test_plan.md
docs/planning/backlog.md
Update backend schema/config validation:
Relax exactly-one-pytest-file validation.
Add config models for file requirements, dependencies, support artifacts, output artifacts, rubric groups, manual rubric items, and stdin scenarios.
Add validation for duplicate keys, unknown group/test references, invalid OR requirements, invalid dependency names, and artifact references.
Add or migrate derived projection:
Prefer adding scoring_items via Alembic.
Regenerate scoring_items from both automated tests[] and manual_rubric_items[].
Keep existing test_cases behavior only where current tests still need it.
Add CS 1410 seed/example:
Course cs1410, title CS 1410: Object-Oriented Programming.
Assignment lab-1-image-processing, title Lab 1: Image Processing.
Four scoring items: part1_files, part1_output, part2_files, part2_output.
Rubric groups for Part 1 and Part 2.
Required files: bears2.py, bears3.py, bears2.jpg, bears3.jpg.
Dependency: pillow.
Pytest artifact display filename: tests.py.
Two model solution artifact metadata rows: bears2.py, bears3.py.
Do not track starter files for Lab 1 in this immediate seed unless support-file copying is implemented in the same slice.
Tests
Config validation tests:
Accept multiple pytest artifacts.
Accept exact required files.
Accept OR file requirements for reflection-style assignments.
Accept dependency lists.
Accept rubric groups referencing scoring keys.
Accept manual rubric items without pytest markers.
Reject duplicate scoring/manual/group keys.
Reject rubric groups referencing unknown scoring items.
Reject output artifacts referencing missing submitted/generated files.
Persistence tests:
Alembic migration creates any new projection table.
Seeding is idempotent.
CS 1400 and CS 1410 both seed correctly.
CS 1410 Lab 1 derives four automated scoring items.
Manual rubric items, when present in future fixtures, derive non-pytest scoring projections.
Sandbox API tests:
CS 1410 appears in course list when active and sandbox-enabled.
Lab 1 detail exposes student-safe required files, scoring items, rubric groups, and upload constraints.
Lab 1 detail does not expose raw config JSON, storage refs, model solution metadata, or file bodies.
Existing checks should still pass:
python -m pytest backend\tests --basetemp=.pytest-tmp
python -m compileall backend\app backend\tests -q
Assumptions
assignment_configs.config_json remains canonical.
Config schema expansion is preferred over a large relational redesign.
New relational tables are allowed only for derived projections that improve querying/API responses.
Frontend is untouched in this slice.
CS 1410 assignments should be supported with minimal instruction changes, but Markdown-only reflections, standardized Lab 6 assets, and testable input abstractions should be recommended for future assignment cleanup.
