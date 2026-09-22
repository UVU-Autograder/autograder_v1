<!-- p2-review | case=p2_lab7_courses_default_none | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab7_courses_default_none

**Lab 7: Modeling College Students with Data Classes** · `cascading_failure` · courses defaults to None, so enroll crashes on None.append

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/student.py
+++ student/student.py
@@ -11,5 +11,5 @@
     name: str
     major: str
-    courses: list[str] = field(default_factory=list, compare=False)
+    courses: list[str] = field(default=None, compare=False)
 
     def enroll(self, course: str) -> None:
```

## What the grader reported

- `dataclass` (Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list)): `E    +    where None = Student(id=101, name='Alice', major='CS', courses=None).courses`
- `methods` (Student defines enroll(course_name) to append courses and total_courses() count method): `E   TypeError: object of type 'NoneType' has no len()`
- `main_output` (main() entrypoint instantiates Student records, tests course enrollment, and outputs summary): `E   AttributeError: 'NoneType' object has no attribute 'append'`
- Passing: Student dataclass sort_index orders list of Student instances by student ID

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the Student dataclass is successfully sorting records by ID, but there is an issue with how the courses list is initialized.

**Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list)**: The courses attribute is being initialized as None instead of an empty list.
- 💡 How can you use the field() function to ensure every new Student instance starts with a fresh list?

**Student defines enroll(course_name) to append courses and total_courses() count method**: The total_courses method is attempting to call len() on a None value.
- 💡 If the dataclass initialization is fixed, how will this affect the behavior of len(self.courses)?

**main() entrypoint instantiates Student records, tests course enrollment, and outputs summary**: The enroll method is trying to call .append() on a None type.
- 💡 What must the type of self.courses be for .append() to work correctly?

**Next step:** Review the documentation for field(default_factory=list) in the dataclasses module.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dataclass`, `methods`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint and next step named field(default_factory=list) (the fix). Now points to the requirement text.

status: todo

```json
{
  "summary": "Your Student dataclass sorts by id correctly, but courses starts out as None instead of a list, and both methods trip over it.",
  "items": [
    {
      "test_key": "dataclass",
      "what_went_wrong": "A new Student's courses is None instead of an empty list.",
      "hint": "Compare how courses is declared in Student with what the requirement for the courses field says."
    },
    {
      "test_key": "methods",
      "what_went_wrong": "total_courses() fails with \"object of type 'NoneType' has no len()\".",
      "hint": "This follows from how courses is declared. Fix that first."
    },
    {
      "test_key": "main_output",
      "what_went_wrong": "enroll fails with \"'NoneType' object has no attribute 'append'\".",
      "hint": "This clears once courses starts as a list."
    }
  ],
  "next_step": "Review the courses field in the Student class."
}
```
