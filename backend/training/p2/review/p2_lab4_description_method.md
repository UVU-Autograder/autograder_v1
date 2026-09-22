<!-- p2-review | case=p2_lab4_description_method | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab4_description_method

**Lab 4: Properties and Validation** · `single_failure` · description defined as a plain method (no @property)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/book.py
+++ student/book.py
@@ -41,5 +41,4 @@
         self._author = value
 
-    @property
     def description(self) -> str:
         """Read-only description property."""
```

## What the grader reported

- `description_readonly` (description read-only property formats 'Title by Author' and raises AttributeError on write): `E   TypeError: argument of type 'method' is not a container or iterable`
- Passing: @property title decorator validates type (str) and non-empty string constraint, @property author decorator validates type (str) and non-empty string constraint
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [book.py] Concept 'exceptions' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your title and author properties are correctly validating types and constraints. However, there is an issue with how the description property is being accessed.

**description read-only property formats 'Title by Author' and raises AttributeError on write**: The test received a method object instead of a string value when trying to check the description.
- 💡 How does the presence of parentheses in your description definition affect how it is accessed as a property?

**Next step:** Review the difference between a standard method and a method decorated with @property.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `description_readonly`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint was confusing and the next step named @property (the fix). Now compares description with author, which is set up correctly.

status: todo

```json
{
  "summary": "Your title and author properties validate correctly. The description is not behaving like the other two.",
  "items": [
    {
      "test_key": "description_readonly",
      "what_went_wrong": "my_book.description gave back a method instead of a string.",
      "hint": "Compare how description is defined with how author is defined. What does author have directly above its def line?"
    }
  ],
  "next_step": "Review the description definition in book.py."
}
```
