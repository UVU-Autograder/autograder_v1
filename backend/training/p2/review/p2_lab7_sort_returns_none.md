<!-- p2-review | case=p2_lab7_sort_returns_none | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab7_sort_returns_none

**Lab 7: Modeling College Students with Data Classes** · `single_failure` · main uses students.sort(), which returns None, then iterates the result

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/student.py
+++ student/student.py
@@ -40,5 +40,5 @@
 
     students = [s1, s2, s3]
-    sorted_students = sorted(students)
+    sorted_students = students.sort()
     print("Sorted students by ID:", [s.id for s in sorted_students])
```

## What the grader reported

- `main_output` (main() entrypoint instantiates Student records, tests course enrollment, and outputs summary): `E   TypeError: 'NoneType' object is not iterable`
- Passing: Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list), Student defines enroll(course_name) to append courses and total_courses() count method, Student dataclass sort_index orders list of Student instances by student ID

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your dataclass implementation and core methods are working correctly, but there is an issue with how the list is being sorted in the main function.

**main() entrypoint instantiates Student records, tests course enrollment, and outputs summary**: The code attempts to iterate over a 'NoneType' object instead of a list of students.
- 💡 What does the .sort() method return in Python?

**Next step:** Review the difference between the .sort() method and the sorted() function in the main() function.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Kept the good hint; next_step named sorted() (the fix).

status: accepted

```json
{
  "summary": "Your dataclass and methods work, but main fails when it sorts the students.",
  "items": [
    {
      "test_key": "main_output",
      "what_went_wrong": "main fails with \"'NoneType' object is not iterable\" right after sorting.",
      "hint": "What does the list method .sort() return? What does sorted_students hold after that line?"
    }
  ],
  "next_step": "Review the sorting line in main."
}
```
