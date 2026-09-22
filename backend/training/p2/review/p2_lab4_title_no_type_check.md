<!-- p2-review | case=p2_lab4_title_no_type_check | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab4_title_no_type_check

**Lab 4: Properties and Validation** · `single_failure` · set_title validates emptiness but not type

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/book.py
+++ student/book.py
@@ -18,6 +18,4 @@
     def set_title(self, value: str) -> None:
         """Setter for title property with validation."""
-        if not isinstance(value, str):
-            raise TypeError("Title must be a string")
         if not value:
             raise ValueError("Title cannot be empty")
```

## What the grader reported

- `title_property` (@property title decorator validates type (str) and non-empty string constraint): `E   Failed: DID NOT RAISE <class 'TypeError'>`
- Passing: @property author decorator validates type (str) and non-empty string constraint, description read-only property formats 'Title by Author' and raises AttributeError on write
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [book.py] Concept 'exceptions' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the author property and the read-only description property. However, there is an issue with the title property's validation.

**@property title decorator validates type (str) and non-empty string constraint**: The test expected a TypeError to be raised when an invalid type was provided for the title, but no error occurred.
- 💡 How does your current title setter handle cases where the input is not a string?

**Next step:** Review the setter logic for the title property.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `title_property`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Sharper hint: compare set_title with the author setter, which does the missing check.

status: todo

```json
{
  "summary": "Your author property and read-only description work. The title setter lets through a value it should reject.",
  "items": [
    {
      "test_key": "title_property",
      "what_went_wrong": "Setting the title to a non-string did not raise a TypeError, which the test expects.",
      "hint": "Compare set_title with your author setter. What does the author setter check first that set_title does not?"
    }
  ],
  "next_step": "Review the set_title method in book.py."
}
```
