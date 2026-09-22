<!-- p2-review | case=p2_lab4_author_wrong_exception | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab4_author_wrong_exception

**Lab 4: Properties and Validation** · `single_failure` · empty author raises TypeError instead of ValueError

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/book.py
+++ student/book.py
@@ -38,5 +38,5 @@
             raise TypeError("Author must be a string")
         if not value:
-            raise ValueError("Author cannot be empty")
+            raise TypeError("Author cannot be empty")
         self._author = value
```

## What the grader reported

- `author_property` (@property author decorator validates type (str) and non-empty string constraint): `E   TypeError: Author cannot be empty`
- Passing: @property title decorator validates type (str) and non-empty string constraint, description read-only property formats 'Title by Author' and raises AttributeError on write
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [book.py] Concept 'exceptions' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the title and description properties, but there is an issue with the author property validation.

**@property author decorator validates type (str) and non-empty string constraint**: The test expected the author property to handle an empty string in a specific way, but it encountered a TypeError instead.
- 💡 How does your current validation logic for the author's value compare to the requirements for the title's value?

**Next step:** Review the validation logic in the author.setter method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `author_property`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft was vague ('handle it in a specific way'). Now compares with the title setter, which raises the expected error. The lab4 exceptions warning is a catalog bug and is deliberately not mentioned.

status: todo

```json
{
  "summary": "Your title and description properties work, and the author setter rejects empty strings. It uses a different kind of error than the test expects.",
  "items": [
    {
      "test_key": "author_property",
      "what_went_wrong": "Setting author to an empty string raised TypeError, and the test did not accept that exception.",
      "hint": "Compare how your title setter handles an empty string with how your author setter does. Do they raise the same kind of error?"
    }
  ],
  "next_step": "Review the author setter in book.py."
}
```
