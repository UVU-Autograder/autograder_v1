<!-- p2-review | case=p2_lab7_all_pass_plus_equals | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab7_all_pass_plus_equals

**Lab 7: Modeling College Students with Data Classes** · `all_pass` · valid alternative: enroll with += [course]

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/student.py
+++ student/student.py
@@ -15,5 +15,5 @@
     def enroll(self, course: str) -> None:
         """Enroll student in a course by adding course number to list."""
-        self.courses.append(course)
+        self.courses += [course]
 
     def total_courses(self) -> int:
```

## What the grader reported

- All automated checks passed.
- Passing: Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list), Student defines enroll(course_name) to append courses and total_courses() count method, Student dataclass sort_index orders list of Student instances by student ID, main() entrypoint instantiates Student records, tests course enrollment, and outputs summary

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Great job! Your implementation successfully meets all the requirements for the Student dataclass and the main testing logic.

**Next step:** Consider how you might use inheritance to create a 'GraduateStudent' class that extends the base Student class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Generic extension replaced with one about the student's own choice (+= [course]).

status: todo

```json
{
  "summary": "Great job! Every test passes, including ordering and the main output.",
  "items": [],
  "next_step": "Your enroll uses += [course] instead of append, and both work here. Can you find out whether += changes the existing list or builds a new one?"
}
```
