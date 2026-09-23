<!-- p2-review | case=p2_lab3_str_no_return_hint | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab3_str_no_return_hint

**Lab 3: Type Hinting and Encapsulation** · `single_failure` · __str__ missing its -> str return annotation

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/youtube_channel.py
+++ student/youtube_channel.py
@@ -10,5 +10,5 @@
         self.__video_count: int = max(0, video_count)
 
-    def __str__(self) -> str:
+    def __str__(self):
         """Return formatted string representation of channel."""
         return f"Channel: {self._name}, Videos: {self.__video_count}"
```

## What the grader reported

- `type_hints` (Explicit type hints added to parameters and return types on constructor and __str__()): `E    +    where <class 'inspect.Signature'> = inspect.Signature`
- Passing: YouTubeChannel protects attributes using private (_ and __) naming encapsulation, Getter and setter methods enforce validation guards against negative counts

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements encapsulation and validation guards. However, there is a missing type hint in one of the required methods.

**Explicit type hints added to parameters and return types on constructor and __str__()**: The __str__ method is missing a return type hint.
- 💡 How can you specify the return type for the __str__ method using Python's type hinting syntax?

**Next step:** Review the __str__ method in the YouTubeChannel class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `type_hints`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint asked how to write the return type (the fix). Now compares with get_name, which has one.

status: accepted

```json
{
  "summary": "Your encapsulation and validation guards work. One method is missing part of its type hints.",
  "items": [
    {
      "test_key": "type_hints",
      "what_went_wrong": "The __str__ method has no return type hint.",
      "hint": "Compare the first line of __str__ with the first line of get_name. What does get_name have that __str__ does not?"
    }
  ],
  "next_step": "Review the first line of the __str__ method."
}
```
