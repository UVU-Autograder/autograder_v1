<!-- p2-review | case=p2_lab1_concept_type_hints | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab1_concept_type_hints

**Lab 1: Image Processing** · `concept_violation` · annotated variables (type hints, Module 2) in a Module 1 lab; output is correct

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/bears2.py
+++ student/bears2.py
@@ -9,5 +9,6 @@
 # Load the original image, and get its size and color mode.
 orig_image = Image.open(filepath)
-width, height = orig_image.size
+width: int = orig_image.size[0]
+height: int = orig_image.size[1]
 mode = orig_image.mode
```

## What the grader reported

- All automated checks passed.
- Passing: Part 1 script (bears2.py) and generated filter image (bears2.jpg) exist, bears2.py filters bears_copy.jpg into a valid non-trivial bears2.jpg, Part 2 script (bears3.py) and generated composite image (bears3.jpg) exist, Submitted bears3.jpg opens as a valid non-trivial composite image
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [bears2.py] Concept 'type-hints' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! Your submission passed all the automated tests for both parts of the assignment.

**Next step:** You might consider exploring how to use different coefficients in your grayscale formula to see how it affects the visual contrast of the image.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft ignored the concept warning. Now it does not call the work done and points back to the allowed concepts.

status: accepted

```json
{
  "summary": "Both parts of the lab pass their automated checks.",
  "items": [],
  "next_step": "Your bears2.py uses type hints (width: int), which come in Module 2. Review this module's allowed concepts and write those lines without them for now."
}
```
