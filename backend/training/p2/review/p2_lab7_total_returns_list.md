<!-- p2-review | case=p2_lab7_total_returns_list | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab7_total_returns_list

**Lab 7: Modeling College Students with Data Classes** · `single_failure` · total_courses returns the list itself instead of its length

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/student.py
+++ student/student.py
@@ -19,5 +19,5 @@
     def total_courses(self) -> int:
         """Return total number of enrolled courses."""
-        return len(self.courses)
+        return self.courses
```

## What the grader reported

- `methods` (Student defines enroll(course_name) to append courses and total_courses() count method): `E    +    where total_courses = Student(id=101, name='Alice', major='CS', courses=[]).total_courses`
- Passing: Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list), Student dataclass sort_index orders list of Student instances by student ID, main() entrypoint instantiates Student records, tests course enrollment, and outputs summary

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the dataclass structure, sorting logic, and main entrypoint. However, there is an issue with the return value of one of your methods.

**Student defines enroll(course_name) to append courses and total_courses() count method**: The total_courses method is returning the list of courses instead of the count of those courses.
- 💡 How can you transform a list into an integer representing its length?

**Next step:** Review the return statement in the total_courses method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `methods`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the fix ('turn a list into its length'). Now compares the return value with what the test expects.

status: todo

```json
{
  "summary": "Your dataclass structure, sorting and main entrypoint work. One method returns the wrong kind of value.",
  "items": [
    {
      "test_key": "methods",
      "what_went_wrong": "total_courses() returned [] where the test expects 0.",
      "hint": "What type of value does the test expect from total_courses, and what type does your return line give back?"
    }
  ],
  "next_step": "Review the return line of total_courses."
}
```
