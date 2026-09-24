<!-- p2-review | case=p2_lab3_single_underscore_count | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab3_single_underscore_count

**Lab 3: Type Hinting and Encapsulation** · `single_failure` · video count uses _video_count (protected) instead of __video_count (private)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/youtube_channel.py
+++ student/youtube_channel.py
@@ -8,9 +8,9 @@
         """Initialize channel name and video count."""
         self._name: str = name
-        self.__video_count: int = max(0, video_count)
+        self._video_count: int = max(0, video_count)
 
     def __str__(self) -> str:
         """Return formatted string representation of channel."""
-        return f"Channel: {self._name}, Videos: {self.__video_count}"
+        return f"Channel: {self._name}, Videos: {self._video_count}"
 
     def get_name(self) -> str:
@@ -24,10 +24,10 @@
     def get_video_count(self) -> int:
         """Return private video count."""
-        return self.__video_count
+        return self._video_count
 
     def set_video_count(self, count: int) -> None:
         """Update video count, ignoring negative values."""
         if count >= 0:
-            self.__video_count = count
+            self._video_count = count
```

## What the grader reported

- `encapsulation` (YouTubeChannel protects attributes using private (_ and __) naming encapsulation): `E    +  and   False = hasattr(<youtube_channel.YouTubeChannel object at 0x000001962D1327B0>, '__video_count')`
- Passing: Getter and setter methods enforce validation guards against negative counts, Explicit type hints added to parameters and return types on constructor and __str__()

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements type hints and validation guards, but there is an issue with attribute encapsulation.

**YouTubeChannel protects attributes using private (_ and __) naming encapsulation**: The test expected to find a private attribute named __video_count, but it could not find it.
- 💡 How does the naming convention for private attributes change when you use double underscores versus a single underscore?

**Next step:** Review the naming conventions for private and private-mangled attributes in the class definition.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `encapsulation`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint was close to an either/or; next_step said 'private-mangled'. Now points to the convention and the student's own attribute.

status: accepted

```json
{
  "summary": "Your type hints and validation guards work, but the video count is not encapsulated the way the assignment asks.",
  "items": [
    {
      "test_key": "encapsulation",
      "what_went_wrong": "The test expects a private __video_count attribute and could not find one.",
      "hint": "How does the assignment mark an attribute as private, and how is your video count attribute named?"
    }
  ],
  "next_step": "Review the naming conventions for protected and private attributes in the assignment."
}
```
