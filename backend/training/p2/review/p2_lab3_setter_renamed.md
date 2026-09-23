<!-- p2-review | case=p2_lab3_setter_renamed | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab3_setter_renamed

**Lab 3: Type Hinting and Encapsulation** · `single_failure` · setter named set_videos instead of set_video_count

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/youtube_channel.py
+++ student/youtube_channel.py
@@ -26,5 +26,5 @@
         return self.__video_count
 
-    def set_video_count(self, count: int) -> None:
+    def set_videos(self, count: int) -> None:
         """Update video count, ignoring negative values."""
         if count >= 0:
@@ -38,5 +38,5 @@
     print(f"Name: {channel.get_name()}, Videos: {channel.get_video_count()}")
     channel.set_name("UVU CS Department")
-    channel.set_video_count(200)
+    channel.set_videos(200)
     print(channel)
```

## What the grader reported

- `getters_setters` (Getter and setter methods enforce validation guards against negative counts): `E    +  where False = hasattr(<youtube_channel.YouTubeChannel object at 0x10b55c2f0>, 'set_video_count')`
- Passing: YouTubeChannel protects attributes using private (_ and __) naming encapsulation, Explicit type hints added to parameters and return types on constructor and __str__()

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements encapsulation and type hints, but there is a naming discrepancy in your methods.

**Getter and setter methods enforce validation guards against negative counts**: The test suite is looking for a method named 'set_video_count', but it cannot find it in your class.
- 💡 Does the name of your method for updating the video count match the name expected by the test suite?

**Next step:** Review the method names in your YouTubeChannel class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `getters_setters`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: accurate and points to the name.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "You have implemented encapsulation and type hints, but the test cannot find one of the required methods.",
  "items": [
    {
      "test_key": "getters_setters",
      "what_went_wrong": "The test looks for a method named set_video_count and cannot find it.",
      "hint": "Does the name of your method for updating the video count match the name the assignment gives?"
    }
  ],
  "next_step": "Review the method names in your YouTubeChannel class."
}
```
