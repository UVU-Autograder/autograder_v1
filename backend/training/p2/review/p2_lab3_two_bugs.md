<!-- p2-review | case=p2_lab3_two_bugs | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab3_two_bugs

**Lab 3: Type Hinting and Encapsulation** · `single_failure` · two independent bugs: count is protected not private, and __str__ lost its return hint

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/youtube_channel.py
+++ student/youtube_channel.py
@@ -8,9 +8,9 @@
         """Initialize channel name and video count."""
         self._name: str = name
-        self.__video_count: int = max(0, video_count)
+        self._video_count: int = max(0, video_count)
 
-    def __str__(self) -> str:
+    def __str__(self):
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

- `encapsulation` (YouTubeChannel protects attributes using private (_ and __) naming encapsulation): `E    +  and   False = hasattr(<youtube_channel.YouTubeChannel object at 0x108f942f0>, '__video_count')`
- `type_hints` (Explicit type hints added to parameters and return types on constructor and __str__()): `E    +    where <class 'inspect.Signature'> = inspect.Signature`
- Passing: Getter and setter methods enforce validation guards against negative counts

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements validation guards for video counts, but there are issues with attribute encapsulation and type hinting.

**YouTubeChannel protects attributes using private (_ and __) naming encapsulation**: The attribute for video count is not using the required private naming convention.
- 💡 How can you rename your video count attribute to use the double underscore prefix to ensure it is private?

**Explicit type hints added to parameters and return types on constructor and __str__()**: The __str__ method is missing a return type hint.
- 💡 What type of data does the __str__ method return, and how do you specify that in the function signature?

**Next step:** Review the YouTubeChannel class methods to ensure all required attributes and return types are correctly annotated.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `encapsulation`, `type_hints`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Both hints gave the fix. Two separate problems now, each pointing to where to look, and a next step to do them one at a time.

status: todo

```json
{
  "summary": "Your validation guards work. There are two separate things to fix: how the video count is named, and one missing type hint.",
  "items": [
    {
      "test_key": "encapsulation",
      "what_went_wrong": "The test expects a private __video_count attribute and could not find one.",
      "hint": "How does the assignment mark an attribute as private, and how is your video count attribute named?"
    },
    {
      "test_key": "type_hints",
      "what_went_wrong": "The __str__ method has no return type hint.",
      "hint": "Compare the first line of __str__ with the first line of get_name. What is missing?"
    }
  ],
  "next_step": "Fix one at a time: start with the video count attribute, rerun the tests, then look at __str__."
}
```
