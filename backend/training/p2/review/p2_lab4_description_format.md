<!-- p2-review | case=p2_lab4_description_format | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab4_description_format

**Lab 4: Properties and Validation** · `single_failure` · description says 'by' instead of 'was written by'

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/book.py
+++ student/book.py
@@ -44,5 +44,5 @@
     def description(self) -> str:
         """Read-only description property."""
-        return f"{self._title} was written by {self._author}."
+        return f"{self._title} by {self._author}"
 
     def __str__(self) -> str:
```

## What the grader reported

- `description_readonly` (description read-only property formats 'Title by Author' and raises AttributeError on write): `E   AssertionError: assert ('Harry Potter' in 'Harry Potter by J.K. Rowling' and 'J.K. Rowling' in 'Harry Potter by J.K. Rowling' and ('written by' in 'Harry Potter by J.K. Rowling' or 'was written' in 'Harry Potter by J.K. Rowling'))`
- Passing: @property title decorator validates type (str) and non-empty string constraint, @property author decorator validates type (str) and non-empty string constraint
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [book.py] Concept 'exceptions' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your title and author properties are correctly validating types and non-empty strings. However, the description property is not meeting the specific formatting requirements.

**description read-only property formats 'Title by Author' and raises AttributeError on write**: The description string does not contain the required phrase 'written by' or 'was written'.
- 💡 How can you modify the return string in your description property to include one of those specific phrases?

**Next step:** Review the description property in book.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `description_readonly`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the fix ('include one of those phrases'). Now asks for a word-by-word comparison.

status: accepted

```json
{
  "summary": "Your title and author properties validate correctly. The description text does not match the required sentence.",
  "items": [
    {
      "test_key": "description_readonly",
      "what_went_wrong": "The description is 'Harry Potter by J.K. Rowling', which does not match the format the test checks for.",
      "hint": "Can you compare the sentence your description returns with the format the assignment asks for, word by word?"
    }
  ],
  "next_step": "Review the description property in book.py."
}
```
