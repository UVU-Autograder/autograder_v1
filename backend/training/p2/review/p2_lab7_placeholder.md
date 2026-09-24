<!-- p2-review | case=p2_lab7_placeholder | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab7_placeholder

**Lab 7: Modeling College Students with Data Classes** · `empty_submission` · student.py is a docstring and pass only

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/student.py
+++ student/student.py
@@ -1,47 +1,3 @@
-"""Student Dataclass - Lab 7 Model Solution."""
+"""Lab 7: Student dataclass."""
 
-from dataclasses import dataclass, field
-
-
-@dataclass(order=True)
-class Student:
-    """Models a college student using a dataclass with ID ordering."""
-
-    id: int
-    name: str
-    major: str
-    courses: list[str] = field(default_factory=list, compare=False)
-
-    def enroll(self, course: str) -> None:
-        """Enroll student in a course by adding course number to list."""
-        self.courses.append(course)
-
-    def total_courses(self) -> int:
-        """Return total number of enrolled courses."""
-        return len(self.courses)
-
-
-def main() -> None:
-    """Main testing entrypoint."""
-    s1 = Student(101, "Alice Smith", "Computer Science")
-    s2 = Student(102, "Bob Jones", "Software Engineering")
-    s3 = Student(100, "Charlie Brown", "Data Science")
-
-    s1.enroll("CS 1410")
-    s1.enroll("CS 2300")
-    s2.enroll("CS 1400")
-
-    print(s1)
-    print(f"{s1.name} total courses: {s1.total_courses()}")
-    print(s2)
-
-    print(f"s1 > s2: {s1 > s2}")
-    print(f"s3 < s1: {s3 < s1}")
-
-    students = [s1, s2, s3]
-    sorted_students = sorted(students)
-    print("Sorted students by ID:", [s.id for s in sorted_students])
-
-
-if __name__ == "__main__":
-    main()
+pass
```

## What the grader reported

- `dataclass` (Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list)): `E   AttributeError: module 'student' has no attribute 'Student'`
- `methods` (Student defines enroll(course_name) to append courses and total_courses() count method): `E   AttributeError: module 'student' has no attribute 'Student'`
- `ordering` (Student dataclass sort_index orders list of Student instances by student ID): `E   AttributeError: module 'student' has no attribute 'Student'`
- `main_output` (main() entrypoint instantiates Student records, tests course enrollment, and outputs summary): `E    +  where False = hasattr(<module 'student' from 'C:\\Users\\Jaxon\\AppData\\Local\\Temp\\ag_grade_ck70lcq6\\execution\\student.py'>, 'main')`
- The prompt carries SUBMISSION_NOTE: the code is empty or a placeholder.

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

The file is still a placeholder, and no Student class or main function has been defined yet.

**Student uses @dataclass(order=True) decorator with typed fields and field(default_factory=list)**: The test cannot find a class named Student in your file.
- 💡 How can you define a class that uses the @dataclass decorator?

**Student defines enroll(course_name) to append courses and total_courses() count method**: The test cannot find the Student class to check for methods.
- 💡 Once the class is defined, how will you add the enroll and total_courses methods?

**Student dataclass sort_index orders list of Student instances by student ID**: The test cannot find the Student class to check for ordering.
- 💡 What decorator argument allows for comparison between objects?

**main() entrypoint instantiates Student records, tests course enrollment, and outputs summary**: The test cannot find a main function in your file.
- 💡 What is the standard way to define an entrypoint for a Python script?

**Next step:** Review the assignment instructions to begin defining the Student dataclass.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dataclass`, `methods`, `ordering`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): 4 items cut to 2 for a placeholder: says so plainly and starts from the instructions. The ordering hint gave the fix and was removed.

status: accepted

```json
{
  "summary": "student.py is still a placeholder, so there is no Student class or main function yet.",
  "items": [
    {
      "test_key": "dataclass",
      "what_went_wrong": "The tests could not find a Student class in student.py.",
      "hint": "Which fields, and which decorator, does the assignment ask Student to have?"
    },
    {
      "test_key": "main_output",
      "what_went_wrong": "student.py has no main function yet.",
      "hint": "This comes after the class: main creates students and prints them."
    }
  ],
  "next_step": "Start from the assignment instructions: write the Student class first, then main, and rerun the tests as you go."
}
```
