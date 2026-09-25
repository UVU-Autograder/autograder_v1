# CS 1400 — Course Architecture & Scaffolding Guide

This document establishes the architecture, catalog contract, and assignment onboarding workflow for CS 1400 (*Fundamentals of Programming*) in the autograder.

---

## Course Overview & Settings

| Setting | Value |
|---|---|
| Course code | `cs1400` |
| Title | Fundamentals of Programming |
| Language | `python` |
| Sandbox enabled | `true` (global default) |
| Term | Spring 2026 |
| Default concepts | `["variables", "conditionals"]` |

---

## Catalog Structure (`cs1400_catalog.json`)

Course modules and assignments are canonically registered in [`backend/app/db/seeds/cs1400_catalog.json`](../../backend/app/db/seeds/cs1400_catalog.json).

```json
{
  "modules": {
    "m1": {
      "name": "Module 1: Expressions & Conditionals",
      "concepts": ["variables", "expressions", "conditionals"]
    },
    "m2": {
      "name": "Module 2: Loops & Iteration",
      "concepts": ["variables", "expressions", "conditionals", "loops", "iteration"]
    },
    "m3": {
      "name": "Module 3: Functions & Modularization",
      "concepts": ["variables", "expressions", "conditionals", "loops", "functions", "strings"]
    },
    "m4": {
      "name": "Module 4: Lists & Collections",
      "concepts": ["variables", "expressions", "conditionals", "loops", "functions", "strings", "lists", "tuples"]
    },
    "m5": {
      "name": "Module 5: Dictionaries & Sets",
      "concepts": ["variables", "expressions", "conditionals", "loops", "functions", "strings", "lists", "dictionaries", "sets"]
    },
    "m6": {
      "name": "Module 6: File I/O & Exceptions",
      "concepts": ["variables", "expressions", "conditionals", "loops", "functions", "strings", "lists", "dictionaries", "file-io", "exceptions"]
    }
  },
  "assignments": [
    {
      "module": "m1",
      "slug": "simple-python-functions",
      "title": "Simple Python Functions"
    }
  ]
}
```

---

## Database Seeding Workflow

Course and assignment seeding is handled dynamically in [`backend/app/db/seed.py`](../../backend/app/db/seed.py#L42-L100):
1. `_seed_cs1400` reads [`backend/app/db/seeds/cs1400_catalog.json`](../../backend/app/db/seeds/cs1400_catalog.json).
2. It constructs `Module` instances with accumulated concepts across sequential modules.
3. For each assignment listed in `catalog["assignments"]`:
   - An `Assignment` record is created with `canvas_ref="canvas:synthetic:<slug>"`.
   - `seed_assignment_artifacts(db, assignment, slug)` loads artifacts from `backend/app/db/seeds/<folder>/config_json.example.json`.

---

## Onboarding New CS 1400 Assignments (Upon Syllabus Receipt)

When the official UVU CS Department syllabus is delivered:

1. **Update Modules & Assignments in Catalog:**
   Add or reorder modules and assignments in [`backend/app/db/seeds/cs1400_catalog.json`](../../backend/app/db/seeds/cs1400_catalog.json).

2. **Create Assignment Seed Package:**
   Create directory `backend/app/db/seeds/<slug_with_underscores>/`:
   ```text
   backend/app/db/seeds/<assignment_slug>/
   ├── config_json.example.json   # Schema v1 assignment configuration
   ├── tests.py                   # Pytest scoring suite with assertions
   ├── model_solution.py          # Reference solution matching student entrypoint
   └── README.md                  # Assignment prompt & grading instructions
   ```

3. **Verify Seed Package Integrity:**
   Run the integrity suite:
   ```bash
   pytest tests/test_seed_integrity.py -q
   ```
   This validates:
   - `AssignmentConfigV1` schema conformance.
   - Entrypoint and file requirement presence in `model_solution`.
   - Artifact path resolution.
   - AST absence of unquoted self-referencing annotations.
