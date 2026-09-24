<!-- p2-review | case=p2_lab7_default_before_required | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab7_default_before_required

**Lab 7: Modeling College Students with Data Classes** · `import_error` · courses field (with a default) declared before major (no default): TypeError at import

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/student.py
+++ student/student.py
@@ -10,6 +10,6 @@
     id: int
     name: str
+    courses: list[str] = field(default_factory=list, compare=False)
     major: str
-    courses: list[str] = field(default_factory=list, compare=False)
 
     def enroll(self, course: str) -> None:
```

## What the grader reported

- `dataclass` (Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list)): `E   TypeError: non-default argument 'major' follows default argument 'courses'`
- `methods` (Student defines enroll(course_name) to append courses and total_courses() count method): `E   TypeError: non-default argument 'major' follows default argument 'courses'`
- `ordering` (Student dataclass sort_index orders list of Student instances by student ID): `E   TypeError: non-default argument 'major' follows default argument 'courses'`
- `main_output` (main() entrypoint instantiates Student records, tests course enrollment, and outputs summary): `E   TypeError: non-default argument 'major' follows default argument 'courses'`

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your code is currently failing to initialize because of the order of your dataclass fields.

**Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list)**: A non-default argument ('major') is being defined after an argument that has a default value ('courses').
- 💡 In Python, how does the interpreter handle arguments when a field with a default value is placed before a field without one?

**Student defines enroll(course_name) to append courses and total_courses() count method**: This failure follows from the initialization error in the dataclass definition.
- 💡 Once the class can be instantiated, will your methods work as intended?

**Student dataclass sort_index orders list of Student instances by student ID**: This failure follows from the initialization error in the dataclass definition.
- 💡 Once the class can be instantiated, will your ordering logic work as intended?

**main() entrypoint instantiates Student records, tests course enrollment, and outputs summary**: This failure follows from the initialization error in the dataclass definition.
- 💡 Once the class can be instantiated, will your main function execute correctly?

**Next step:** Review the order of your fields in the Student dataclass definition.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dataclass`, `methods`, `ordering`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): 4 items cut to 3; one root cause (field order), the rest follow.

status: accepted

```json
{
  "summary": "Your Student class cannot be created because of the order its fields are declared in.",
  "items": [
    {
      "test_key": "dataclass",
      "what_went_wrong": "Python rejects the class with \"non-default argument 'major' follows default argument 'courses'\".",
      "hint": "The error names two fields. Compare where each one is declared in Student, and which one has a default value."
    },
    {
      "test_key": "methods",
      "what_went_wrong": "This test fails for the same reason.",
      "hint": "This follows from the field order. Fix that first."
    },
    {
      "test_key": "ordering",
      "what_went_wrong": "This test fails for the same reason.",
      "hint": "This clears once Student can be created."
    }
  ],
  "next_step": "Review the order of the fields in Student. main_output fails for the same reason."
}
```
