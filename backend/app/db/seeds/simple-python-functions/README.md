# Simple Python Functions Grading Example

This folder shows a complete grading setup for a small Python functions assignment.

## Assignment Goal

Students submit a ZIP/project bundle containing:

```text
student_functions.py
```

The submitted file must define:

- `add_numbers(a, b)`
- `reverse_words(text)`
- `count_vowels(text)`

## Files In This Example

- `config.json`: seed value for `assignment_configs.config_json`.
- `assignment_tests.py`: the pytest file artifact for the assignment.
- `model_solution.py`: instructor-owned model solution file body. During model-solution validation, this body is placed at the required bundle path `student_functions.py`.
- `pytest.ini`: support-file example that registers the app grading markers.

In production, `config.json` would be stored in `assignment_configs.config_json`. The Python and INI files would be stored through `assignment_artifacts` using generated opaque storage references.

## Student Bundle Shape

After global ZIP safety checks and any supported intake normalization, this assignment expects the ephemeral workspace to contain:

```text
workspace/
  student_functions.py
```

During grading, the backend copies assignment-owned artifacts into that same ephemeral workspace:

```text
workspace/
  student_functions.py
  assignment_tests.py
  pytest.ini
```

The grader runs pytest against `assignment_tests.py`. The model solution is validated through the same Judge0/Kata path before staff use the setup for grading; for that validation, the model solution body is copied into the ephemeral workspace as `student_functions.py`.

## Marker And Result Mapping

| Config key       | Pytest marker      | Points | Extra credit | Result mapping                                                           |
| ---------------- | ------------------ | ------ | ------------ | ------------------------------------------------------------------------ |
| `add_numbers`    | `ag_add_numbers`   | 5      | No           | All tests with this marker pass for the scoring item to pass.            |
| `reverse_words`  | `ag_reverse_words` | 10     | No           | Multiple pytest functions share this marker and map to one scoring item. |
| `count_vowels`   | `ag_count_vowels`  | 10     | No           | All tests with this marker pass for the scoring item to pass.            |

If any pytest function with a scoring marker fails, the scoring item for that marker is failed. The app then maps marker-level outcomes back to `config_json.tests[]`, computes the base total from non-extra-credit items, and adds passed extra-credit items on top.

## Expected Model Solution Score

The provided `model_solution.py` should pass all scoring markers:

```text
add_numbers: 5 / 5
reverse_words: 10 / 10
count_vowels: 10 / 10
total: 25 / 25
```

## Preflight Expectations

Before model-solution validation or grading, strict preflight should verify:

- `schema_version` is supported.
- `tests[].key` values are unique.
- each `tests[].key` maps to marker `ag_<key>`.
- each configured marker appears in `assignment_tests.py`.
- the single assignment pytest artifact exists.
- each scoring item has a valid non-negative point value.
- each scoring item has an explicit `extra_credit` boolean.
- bundle requirements include the expected `student_functions.py` entrypoint.
