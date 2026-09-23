<!-- p2-review | case=p2_lab1_all_pass_main_function | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab1_all_pass_main_function

**Lab 1: Image Processing** · `all_pass` · valid alternative: bears3.py wrapped in a main() function

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/bears3.py
+++ student/bears3.py
@@ -1,3 +1,7 @@
 from PIL import Image
+
+
+def main():
+    pass
 
 filename = 'bears_copy.jpg'
@@ -45,2 +49,3 @@
 
 new_image.save(file_out_path)
+main()
```

## What the grader reported

- All automated checks passed.
- Passing: Part 1 script (bears2.py) and generated filter image (bears2.jpg) exist, bears2.py filters bears_copy.jpg into a valid non-trivial bears2.jpg, Part 2 script (bears3.py) and generated composite image (bears3.jpg) exist, Submitted bears3.jpg opens as a valid non-trivial composite image

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! Your submission successfully passed all the automated tests for both parts of the lab.

**Next step:** You could consider exploring how to use different coefficients in your grayscale formula to see how it affects the visual contrast of the image.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change: accurate and the extension fits the lab.

status: accepted

```json
{
  "summary": "Congratulations! Both parts of the lab pass their automated checks.",
  "items": [],
  "next_step": "Try different coefficients in your grayscale formula and see how they change the contrast of the image."
}
```
