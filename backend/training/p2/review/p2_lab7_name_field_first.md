<!-- p2-review | case=p2_lab7_name_field_first | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab7_name_field_first

**Lab 7: Modeling College Students with Data Classes** · `cascading_failure` · name declared before id, so ordering compares names and positional args land in the wrong fields

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/student.py
+++ student/student.py
@@ -8,6 +8,6 @@
     """Models a college student using a dataclass with ID ordering."""
 
+    name: str
     id: int
-    name: str
     major: str
     courses: list[str] = field(default_factory=list, compare=False)
```

## What the grader reported

- `dataclass` (Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list)): `E    +  where 'Alice' = Student(name=101, id='Alice', major='CS', courses=[]).id`
- `ordering` (Student dataclass sort_index orders list of Student instances by student ID): `E     Use -v to get more diff`
- Passing: Student defines enroll(course_name) to append courses and total_courses() count method, main() entrypoint instantiates Student records, tests course enrollment, and outputs summary

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

You have successfully implemented the enrollment logic and the main entrypoint, but there are issues with how the Student dataclass fields are defined and ordered.

**Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list)**: The student ID is being assigned to the name field instead of the id field.
- 💡 Check the order of the arguments you are passing to the Student constructor in your main function compared to the order of fields defined in the class.

**Student dataclass sort_index orders list of Student instances by student ID**: The list is not sorting correctly by the numerical ID.
- 💡 How does the dataclass determine sort order when multiple fields are present?

**Next step:** Review the order of fields in your Student class definition.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dataclass`, `ordering`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The first hint sent the student to main's arguments, which are right; the field order in the class is the bug. Ordering follows from it.

status: accepted

```json
{
  "summary": "Your enroll logic and main entrypoint work, but the Student fields are in an order that mixes up id and name.",
  "items": [
    {
      "test_key": "dataclass",
      "what_went_wrong": "Student(101, 'Alice', 'CS') stored 101 as the name and 'Alice' as the id.",
      "hint": "A dataclass takes positional arguments in the order its fields are declared. Compare your field order with the order main passes them in."
    },
    {
      "test_key": "ordering",
      "what_went_wrong": "Sorting orders the students by name instead of by id, because of the same field order.",
      "hint": "This follows from the field order: a dataclass compares fields from the top down."
    }
  ],
  "next_step": "Review the order of the fields in the Student class."
}
```
