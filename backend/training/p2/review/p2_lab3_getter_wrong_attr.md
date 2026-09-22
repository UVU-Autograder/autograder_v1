<!-- p2-review | case=p2_lab3_getter_wrong_attr | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab3_getter_wrong_attr

**Lab 3: Type Hinting and Encapsulation** · `single_failure` · get_video_count returns the name

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/youtube_channel.py
+++ student/youtube_channel.py
@@ -24,5 +24,5 @@
     def get_video_count(self) -> int:
         """Return private video count."""
-        return self.__video_count
+        return self._name
 
     def set_video_count(self, count: int) -> None:
```

## What the grader reported

- `getters_setters` (Getter and setter methods enforce validation guards against negative counts): `E    +    where get_video_count = <youtube_channel.YouTubeChannel object at 0x108db82f0>.get_video_count`
- Passing: YouTubeChannel protects attributes using private (_ and __) naming encapsulation, Explicit type hints added to parameters and return types on constructor and __str__()

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

You have successfully implemented encapsulation and type hints, but there is an issue with how the video count is being retrieved.

**Getter and setter methods enforce validation guards against negative counts**: The `get_video_count` method is returning the channel name string instead of the numerical video count.
- 💡 Which attribute should the `get_video_count` method actually return to satisfy the test?

**Next step:** Review the return statement in the `get_video_count` method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `getters_setters`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint asked which attribute to return (the fix). Now compares with get_name.

status: todo

```json
{
  "summary": "You have implemented encapsulation and type hints, but get_video_count gives back the wrong value.",
  "items": [
    {
      "test_key": "getters_setters",
      "what_went_wrong": "get_video_count() returned 'Updated', the channel name, where the test expects 5.",
      "hint": "Compare the return line of get_video_count with the return line of get_name. Which attribute does each one read?"
    }
  ],
  "next_step": "Review the return line of get_video_count."
}
```
