<!-- p2-review | case=p2_lab1_blank_output | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab1_blank_output

**Lab 1: Image Processing** · `single_failure` · bears2.py computes gray but never writes it into the new pixel map (all-black image)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/bears2.py
+++ student/bears2.py
@@ -41,5 +41,5 @@
         gray = int(0.299*red + 0.587*green + 0.114*blue)
             # Assigning new color value for each pixel based on grayscale formula
-        new_pixel_map[x, y] = (gray, gray, gray)
+        gray_pixel = (gray, gray, gray)
 
 new_image.save(file_out_path)
```

## What the grader reported

- `part1_output` (bears2.py filters bears_copy.jpg into a valid non-trivial bears2.jpg): `E    +    where {(0, 0, 0)} = set([(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), ...])`
- Passing: Part 1 script (bears2.py) and generated filter image (bears2.jpg) exist, Part 2 script (bears3.py) and generated composite image (bears3.jpg) exist, Submitted bears3.jpg opens as a valid non-trivial composite image

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your scripts successfully generate the required files, but the output image for Part 1 is not being updated correctly.

**bears2.py filters bears_copy.jpg into a valid non-trivial bears2.jpg**: The resulting image appears to be a single solid color (all pixels are identical).
- 💡 In your nested loops for the new image, are you actually assigning the calculated `gray_pixel` to the `new_pixel_map`?

**Next step:** Review the nested loops in bears2.py where you iterate through the image dimensions.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `part1_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the fix ('assign gray_pixel to new_pixel_map'). Now asks the student to trace where the gray value goes.

status: accepted

```json
{
  "summary": "Your scripts run and create their files, but the Part 1 image comes out blank.",
  "items": [
    {
      "test_key": "part1_output",
      "what_went_wrong": "bears2.jpg is a single solid color, so none of the gray values reached the new image.",
      "hint": "Can you trace what happens to the gray value at the end of each pass through the inner loop? Which image does it end up in?"
    }
  ],
  "next_step": "Review the nested loops in bears2.py."
}
```
