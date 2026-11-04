# Author and validate assignments

[System](../system.md#assignment-setup-and-scoring) owns scoring behavior. Full course content stays in Canvas.

## Staff workflow

1. Open/create a course assignment as an authorized instructor/admin. Configure title, language (`python` or `cpp`), markdown description/instructions, required files, stable scoring keys/points, rubric groups, completion requirements ("Pass at least X of Y" objectives), manual items and concept denylists. `assignments.description` serves as the authoritative relational storage for student workspace instructions and AI feedback prompts, while `assignment_configs.config["description"]` retains a synchronized snapshot for frozen grading packages and sandbox run records.
2. Write the primary `tests.py` suite on **Tests & Rubric** ([Python test runtime](#python-test-runtime)); **View Python helpers** shows the injected helper module, and **Tests with AI** opens the test authoring assistant with the same helper context. On **Model Solution**, [create or edit reference files](#model-solution-files) in the browser, or upload existing files.
3. Save assignment setup and file contents, then choose **Test Model Solution** on **Model Solution**. This runs preflight before queuing reference execution through Judge0. Successful Python reference validation makes `inventory_status` `ready` ([system scoring](../system.md#assignment-setup-and-scoring)).
4. Exercise synthetic sandbox/official submissions, manual completion and exports; obtain instructor calibration for correct, incorrect and partial-credit work.

IAs read setup without editing it. Student workspace editing is separate from instructor grading assets.

Official intake validates and copies the configured test/support assets before dispatch. Missing files, stored-hash mismatches, type mismatches, conflicting basenames, non-ready inventory and the reserved runner destinations reject intake. The admitted configuration, rubric, concepts and grading bytes remain fixed for the entire batch; corrections apply to a new upload, not a queued or partly graded batch. Models are checked for readiness but their bytes are excluded from the execution package. Helper precedence remains configured instructor helper, existing student helper, then captured built-in fallback.

## Python test runtime

Prefer ordinary pytest in `tests.py`:

```python
import pytest
import account


@pytest.mark.ag_deposit
def test_deposit(capsys):
    account.Account("A").deposit(10)
    # use capsys / bounded_output for stdout; monkeypatch for input()
```

The grading sandbox injects [`python_autograder_helpers.py`](../../backend/app/db/seeds/shared/python_autograder_helpers.py) automatically and already bounds pytest `capsys` capture. Instructors can open the exact injected file with **View Python helpers** next to `tests.py`; the AI test assistant receives the same source and usage notes.

Import from that helper only when required:

| Situation | Helper |
| --- | --- |
| Student filename collides with stdlib/pip (e.g. `packaging.py`) | `import_student_modules` |
| Student code calls `input()` during import | `with_input_blocked` |
| Long multi-prompt CLI sequences | `sequential_input_mock` (or plain `monkeypatch`) |

Do not write `from autograder_capture import BoundedOutput` in new suites—use `capsys` or the `bounded_output` fixture. Canvas filename suffixes are normalized at official intake; that alone is not a reason to import helpers.

## Model solution files

On **Model Solution**, enter a **New File Name** matching a required solution filename (for example, `main.py`), then choose **Create File**. Write the reference code and choose **Save** inside the editor. **Edit Code** opens existing supported source/text files, including C++ source and headers, with syntax highlighting based on the filename. Editor support for a file extension does not imply grading support for that language; see [current language scope](../system.md#assignment-setup-and-scoring).

Creation accepts the extensions in the [editor's filename map](../../frontend/features/assignments/workspace/file-utils.ts), including `.py`, `.cpp`, `.h`, `.hpp`, `.json`, `.md`, and `.txt`, regardless of extension case. Filenames must be nonempty, at most 255 characters, and unique across assignment artifacts regardless of case. Paths, invalid filename characters, `..`, and reserved harness names (`runner.py`, `conftest.py`, `ag_test_helpers.py`) are rejected. Upload other file types with **Upload File**; binary files and unsupported extensions have no **Edit Code** action. ZIP model solution uploads are rejected with an instruction to upload individual solution files; the backend also rejects ZIP contents disguised with another extension. Existing stored ZIPs must be replaced with individual required model files for validation.

The editor's **Save** persists that file and its grading configuration reference together. Uploads also register their file references immediately, and deleting a model/support file removes its reference. No extra assignment save is needed for those file changes. **Cancel** or the close button discards unsaved editor changes; canceling a new file creates no artifact. A failed save leaves the draft open for retry. The assignment header's **Save** separately persists setup and the primary test suite; **Discard** reloads setup and does not undo file saves, uploads, or deletions. Editing an existing support file preserves its artifact type.

Uploading the same filename replaces that file while preserving its key and type; different filenames, including files sharing a basename such as `main.py` and `main.txt`, receive separate keys. The API rejects attempts to reuse an existing artifact key for a different type. It also rejects deletion of the sole configured non-pytest artifact: add a replacement first so setup remains valid and editable.

The [artifact service](../../backend/app/domains/assignments/service.py) updates stored file metadata and `config.artifacts` in the same database transaction, preserving other assignment settings. The [reference bundle builder](../../backend/app/domains/assignments/engine.py) selects models from that saved configuration. Offline mock mode retains file contents and references until the page is reloaded; it simulates validation and does not run Judge0.

Save pending setup/test changes and file edits before choosing **Test Model Solution**; the button is disabled while setup has unsaved changes. A failed status request reports an error and enables retry rather than leaving validation stuck. The result panel describes the last validation run; after changing saved files, rerun validation. Changes to configured instructor files invalidate an existing Python reference inventory; revalidate before accepting new sandbox or official submissions. Setup saves preserve existing completion requirements and execution language, including settings without dedicated controls in the editor. See [reference inventory](../system.md#assignment-setup-and-scoring) for readiness rules.

## Seed workflow

The [CS1410 catalog](../../backend/app/db/seeds/cs1410_catalog.json) owns all 17 titles/module placements, and the [CS1400 catalog](../../backend/app/db/seeds/cs1400_catalog.json) defines 44 course assignments across 14 modules. [Packages](../../backend/app/db/seeds/) contain configs, markdown descriptions (`description.md`), explicit tests, standalone models and resources.

Use [AssignmentConfigV1](../../backend/app/domains/assignments/schemas.py) and an [actual config](../../backend/app/db/seeds/simple-python-functions/config.json). Use `scoring_items`, `completion_requirements` (for "pass at least X of Y" objectives), top-level dependencies and `pytest_file`/`model_solution`/`support_file` artifacts. Each scoring key maps to a pytest marker:

```python
@pytest.mark.ag_calculate_cost
def test_calculate_cost():
    assert Candy("Candy Corn", 1.5, 0.25).calculate_cost() == pytest.approx(0.38)
```

Add catalog/package references, required model/resources and marked tests; declare helpers as support artifacts. Keep progressive Dessert Shop models assignment-local and expected assertions visible. Verify the intended package resolved: missing packages can fall back to `simple-python-functions`.

Run [seed integrity](../../backend/tests/test_seed_integrity.py)/[model validation](../../backend/tests/test_assignment_validation.py) checks in an isolated database, then real synthetic grading.

## Calibration

A green model solution proves the reference passes current tests; it does not prove incorrect solutions fail the intended keys. Calibrate with canonical and alternate valid models, known mistakes, empty/boundary inputs, wrong interfaces, concept-policy violations, and—when required—student-authored pytest paths (passing, failing, none discovered, import shadowing). Keep failing mutations visible as unresolved gaps rather than dropping them from reports. The [mutation catalog](../../backend/eval/mutations.py) and [eval README](../../backend/eval/README.md) help, but AI case generation often uses a local subprocess instead of Judge0—treat those results as candidates, not runtime-parity proof. Course-owner acceptance remains separate from automated seed checks.

Default I/O helpers normalize whitespace/blank lines. Mark secret regression checks with `is_private` (visibility control, not same-process secrecy). Deferred hints, comparison modes and related follow-ups live under [system integrity](../system.md#integrity-and-trust-boundaries).

## Essential test pitfalls

[Shared helpers](../../backend/app/db/seeds/shared/) handle import shadowing, isolated student-authored pytest and headless Pygame. Check runtime protocols structurally and accommodate permitted Enum/string forms. Set dummy SDL before pygame imports; bound event loops. Automated state checks cannot replace manual visual/reflection criteria. Preserve binary resources and required bundle files.

Model/mutation success establishes tested scope, not instructor acceptance.
