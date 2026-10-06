# Author and validate assignments

[System](../system.md#assignment-setup-and-scoring) owns scoring behavior. Full course content stays in Canvas.

## Staff workflow

1. Open/create a course assignment as an authorized instructor/admin. Configure markdown description/instructions, required files, stable scoring keys/points, groups, manual items and concepts. `assignments.description` serves as the authoritative relational storage for student workspace instructions and AI feedback prompts, while `assignment_configs.config["description"]` retains a synchronized snapshot for immutable config version history and sandbox run records.
2. Upload/edit pytest, model and support artifacts; Edit pytest handles the primary test, while Artifacts handles additional files.
3. Save, preflight and validate real reference files through Judge0.
4. Exercise synthetic sandbox/official submissions, manual completion and exports; obtain instructor calibration for correct, incorrect and partial-credit work.

IAs read setup without editing it. Student workspace editing is separate from instructor grading assets.

## Seed workflow

The [CS1410 catalog](../../backend/app/db/seeds/cs1410_catalog.json) owns all 17 titles/module placements. [Packages](../../backend/app/db/seeds/) contain configs, markdown descriptions (`description.md`), explicit tests, standalone models and resources. CS1400 remains a placeholder.

Use [AssignmentConfigV1](../../backend/app/domains/assignments/schemas.py) and an [actual config](../../backend/app/db/seeds/simple-python-functions/config.json). Use `scoring_items`, top-level dependencies and `pytest_file`/`model_solution`/`support_file` artifacts. Each scoring key maps to a pytest marker:

```python
@pytest.mark.ag_calculate_cost
def test_calculate_cost():
    assert Candy("Candy Corn", 1.5, 0.25).calculate_cost() == pytest.approx(0.38)
```

Add catalog/package references, required model/resources and marked tests; declare helpers as support artifacts. Keep progressive Dessert Shop models assignment-local and expected assertions visible. Verify the intended package resolved: missing packages can fall back to `simple-python-functions`.

Run [seed integrity](../../backend/tests/test_seed_integrity.py)/[model validation](../../backend/tests/test_assignment_validation.py) checks in an isolated database, then real synthetic grading. The [mutation catalog](../../backend/eval/mutations.py) and [known grader gaps](../../backend/eval/README.md) support calibration.

## Essential test pitfalls

[Shared helpers](../../backend/app/db/seeds/shared/) handle import shadowing, isolated student-authored pytest and headless Pygame. Check runtime protocols structurally and accommodate permitted Enum/string forms. Set dummy SDL before pygame imports; bound event loops. Automated state checks cannot replace manual visual/reflection criteria. Preserve binary resources and required bundle files.

Model/mutation success establishes tested scope, not instructor acceptance.
