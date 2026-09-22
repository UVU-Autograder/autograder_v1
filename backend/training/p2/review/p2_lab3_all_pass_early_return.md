<!-- p2-review | case=p2_lab3_all_pass_early_return | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab3_all_pass_early_return

**Lab 3: Type Hinting and Encapsulation** · `all_pass` · valid alternative: guard clause with early return in the setter

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/youtube_channel.py
+++ student/youtube_channel.py
@@ -28,6 +28,7 @@
     def set_video_count(self, count: int) -> None:
         """Update video count, ignoring negative values."""
-        if count >= 0:
-            self.__video_count = count
+        if count < 0:
+            return
+        self.__video_count = count
```

## What the grader reported

- All automated checks passed.
- Passing: YouTubeChannel protects attributes using private (_ and __) naming encapsulation, Getter and setter methods enforce validation guards against negative counts, Explicit type hints added to parameters and return types on constructor and __str__()

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! Your submission passed all the automated tests and followed the required concepts.

**Next step:** Consider how you might extend this class to include a method that calculates the average views per video using type hints.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The extension referred to views, which this class does not have. Now about the student's own choice (guard clause).

status: todo

```json
{
  "summary": "Congratulations! Every test passes, including the setter guard.",
  "items": [],
  "next_step": "Your setter uses an early return for negative counts. Can you compare it with writing the same rule as one if block, and decide which reads better as more rules are added?"
}
```
