<!-- p2-review | case=p2_lab3_name_public | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab3_name_public

**Lab 3: Type Hinting and Encapsulation** · `single_failure` · name stored as public self.name instead of self._name

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/youtube_channel.py
+++ student/youtube_channel.py
@@ -7,18 +7,18 @@
     def __init__(self, name: str = "", video_count: int = 0) -> None:
         """Initialize channel name and video count."""
-        self._name: str = name
+        self.name: str = name
         self.__video_count: int = max(0, video_count)
 
     def __str__(self) -> str:
         """Return formatted string representation of channel."""
-        return f"Channel: {self._name}, Videos: {self.__video_count}"
+        return f"Channel: {self.name}, Videos: {self.__video_count}"
 
     def get_name(self) -> str:
         """Return the protected channel name."""
-        return self._name
+        return self.name
 
     def set_name(self, name: str) -> None:
         """Update channel name."""
-        self._name = name
+        self.name = name
 
     def get_video_count(self) -> int:
```

## What the grader reported

- `encapsulation` (YouTubeChannel protects attributes using private (_ and __) naming encapsulation): `E    +  where False = hasattr(<youtube_channel.YouTubeChannel object at 0x1096342f0>, '_name')`
- Passing: Getter and setter methods enforce validation guards against negative counts, Explicit type hints added to parameters and return types on constructor and __str__()

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements type hints and validation guards for the video count.

**YouTubeChannel protects attributes using private (_ and __) naming encapsulation**: The test expected to find a protected attribute named '_name', but it could not find it on the object.
- 💡 How can you rename the 'name' attribute to follow the naming convention for protected members?

**Next step:** Review the naming conventions for private and protected attributes in the assignment instructions.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `encapsulation`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint said to rename it (the fix). Now points to the convention the student already used for the video count.

status: todo

```json
{
  "summary": "Your type hints and video count guard work, but the channel name is not encapsulated the way the assignment asks.",
  "items": [
    {
      "test_key": "encapsulation",
      "what_went_wrong": "The test expects a protected _name attribute and could not find one.",
      "hint": "Look at how you named the video count attribute. What naming convention does the assignment ask you to use for the name?"
    }
  ],
  "next_step": "Review the naming conventions for protected and private attributes in the assignment."
}
```
