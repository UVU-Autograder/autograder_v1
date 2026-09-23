<!-- p2-review | case=p2_lab7_enroll_extend | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab7_enroll_extend

**Lab 7: Modeling College Students with Data Classes** · `cascading_failure` · enroll uses extend, so 'CS 1410' is added one character at a time

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/student.py
+++ student/student.py
@@ -15,5 +15,5 @@
     def enroll(self, course: str) -> None:
         """Enroll student in a course by adding course number to list."""
-        self.courses.append(course)
+        self.courses.extend(course)
 
     def total_courses(self) -> int:
```

## What the grader reported

- `methods` (Student defines enroll(course_name) to append courses and total_courses() count method): `E    +    where total_courses = Student(id=101, name='Alice', major='CS', courses=['C', 'S', ' ', '1', '4', '1', '0', 'C', 'S', ' ', '2', '3', '0', '0']).total_courses`
- Passing: Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list), Student dataclass sort_index orders list of Student instances by student ID, main() entrypoint instantiates Student records, tests course enrollment, and outputs summary

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the dataclass decorator, sorting logic, and the main entrypoint. However, there is an issue with how courses are being added to the list.

**Student defines enroll(course_name) to append courses and total_courses() count method**: The total_courses method is returning 14 instead of 2, suggesting that the course string is being broken into individual characters.
- 💡 What is the difference between how .append() and .extend() handle a string argument?

**Next step:** Review the enroll method in student.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `methods`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint named append versus extend (an either/or with the answer). Now asks the student to print the list and look.

status: accepted

```json
{
  "summary": "Your dataclass, sorting and main entrypoint work. Enrolling in a course adds more than one entry.",
  "items": [
    {
      "test_key": "methods",
      "what_went_wrong": "After two enrollments, total_courses() is 14, not 2.",
      "hint": "Can you print s.courses after a single enroll call? What does the list contain, and which list method put it there?"
    }
  ],
  "next_step": "Review the enroll method in student.py."
}
```
