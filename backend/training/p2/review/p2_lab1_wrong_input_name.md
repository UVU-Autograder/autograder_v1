<!-- p2-review | case=p2_lab1_wrong_input_name | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab1_wrong_input_name

**Lab 1: Image Processing** · `single_failure` · bears2.py opens bears.jpg, which does not exist (FileNotFoundError)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/bears2.py
+++ student/bears2.py
@@ -1,5 +1,5 @@
 from PIL import Image
 
-filename = 'bears_copy.jpg'
+filename = 'bears.jpg'
 filepath = f"./{filename}"
```

## What the grader reported

- `part1_output` (bears2.py filters bears_copy.jpg into a valid non-trivial bears2.jpg): `E   FileNotFoundError: [Errno 2] No such file or directory: './bears.jpg'`
- Passing: Part 1 script (bears2.py) and generated filter image (bears2.jpg) exist, Part 2 script (bears3.py) and generated composite image (bears3.jpg) exist, Submitted bears3.jpg opens as a valid non-trivial composite image

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your scripts successfully generate the required output files, but there is an issue with the file path used in the first part.

**bears2.py filters bears_copy.jpg into a valid non-trivial bears2.jpg**: The script failed because it could not find the file 'bears.jpg' at the specified path.
- 💡 Which file name does the assignment specify you should be loading as the source for the first part?

**Next step:** Check the assignment instructions for the correct source filename for bears2.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `part1_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: accurate and points to the instructions.

status: accepted

```json
{
  "summary": "Your Part 2 script works, but bears2.py cannot open its source image.",
  "items": [
    {
      "test_key": "part1_output",
      "what_went_wrong": "bears2.py stopped with FileNotFoundError because there is no file named bears.jpg.",
      "hint": "Which file name does the assignment say bears2.py should load as its source?"
    }
  ],
  "next_step": "Check the assignment instructions for the source file name used in bears2.py."
}
```
