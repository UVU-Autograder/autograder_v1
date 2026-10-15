<!-- p2-review | case=p2_lab7_enroll_missing_self | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab7_enroll_missing_self

**Lab 7: Modeling College Students with Data Classes** · `cascading_failure` · enroll defined without self

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/student.py
+++ student/student.py
@@ -13,5 +13,5 @@
     courses: list[str] = field(default_factory=list, compare=False)
 
-    def enroll(self, course: str) -> None:
+    def enroll(course: str) -> None:
         """Enroll student in a course by adding course number to list."""
         self.courses.append(course)
```

## What the grader reported

- `methods` (Student defines enroll(course_name) to append courses and total_courses() count method): `E   TypeError: Student.enroll() takes 1 positional argument but 2 were given`
- `main_output` (main() entrypoint instantiates Student records, tests course enrollment, and outputs summary): `E   TypeError: Student.enroll() takes 1 positional argument but 2 were given`
- Passing: Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list), Student dataclass sort_index orders list of Student instances by student ID

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your dataclass structure and sorting logic are working correctly, but there is an issue with how your methods are defined.

**Student defines enroll(course_name) to append courses and total_courses() count method**: The enroll method is reporting that it received two arguments when only one was expected.
- 💡 How do instance methods in a class need to receive the instance itself as the first parameter?

**main() entrypoint instantiates Student records, tests course enrollment, and outputs summary**: The main function is encountering a TypeError when trying to call the enroll method.
- 💡 If the previous error is resolved, will this call behave as expected?

**Next step:** Review the definition of the enroll method in the Student class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `methods`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the fix. Now compares enroll's def line with total_courses.

> p3b (Claude): removed the quoted call and error text; one sentence per field; trimmed

status: accepted

```json
{
  "summary": "Your dataclass and sorting work, but calling enroll fails.",
  "items": [
    {
      "test_key": "methods",
      "what_went_wrong": "enroll accepts fewer arguments than a call on a student passes.",
      "hint": "What differs between the def lines of enroll and total_courses?"
    },
    {
      "test_key": "main_output",
      "what_went_wrong": "main fails at enroll for the same reason.",
      "hint": "This follows from the enroll problem; fix that first."
    }
  ],
  "next_step": "Review the def line of enroll."
}
```
