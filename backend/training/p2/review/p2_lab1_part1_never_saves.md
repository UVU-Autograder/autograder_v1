<!-- p2-review | case=p2_lab1_part1_never_saves | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab1_part1_never_saves

**Lab 1: Image Processing** · `single_failure` · bears2.py builds the grayscale image but never calls save()

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/bears2.py
+++ student/bears2.py
@@ -43,3 +43,3 @@
         new_pixel_map[x, y] = (gray, gray, gray)
 
-new_image.save(file_out_path)
+# new_image.save(file_out_path)
```

## What the grader reported

- `part1_output` (bears2.py filters bears_copy.jpg into a valid non-trivial bears2.jpg): `E    +    where exists = WindowsPath('C:/Users/Jaxon/AppData/Local/Temp/ag_grade__pjoluwa/execution/bears2.jpg').exists`
- Passing: Part 1 script (bears2.py) and generated filter image (bears2.jpg) exist, Part 2 script (bears3.py) and generated composite image (bears3.jpg) exist, Submitted bears3.jpg opens as a valid non-trivial composite image

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your scripts are correctly processing the images, but the first script is not saving the output file.

**bears2.py filters bears_copy.jpg into a valid non-trivial bears2.jpg**: The autograder cannot find the file 'bears2.jpg' because it was never saved to the disk.
- 💡 Look at the bottom of your bears2.py script; is there a line of code that actually writes the 'new_image' to a file?

**Next step:** Review the `new_image.save()` method in your `bears2.py` file.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `part1_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint and next step named save() (the fix). Now compares with bears3.py, which saves its image.

status: accepted

```json
{
  "summary": "Your grayscale conversion runs, but Part 1 never produces its output file.",
  "items": [
    {
      "test_key": "part1_output",
      "what_went_wrong": "After running bears2.py, the test could not find bears2.jpg.",
      "hint": "Can you compare the end of bears2.py with the end of bears3.py? What does bears3.py do with its finished image?"
    }
  ],
  "next_step": "Review the last lines of bears2.py."
}
```
