<!-- p2-review | case=p2_lab3_set_name_local | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab3_set_name_local

**Lab 3: Type Hinting and Encapsulation** · `single_failure` · set_name assigns a local variable, so the name never changes

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/youtube_channel.py
+++ student/youtube_channel.py
@@ -20,5 +20,5 @@
     def set_name(self, name: str) -> None:
         """Update channel name."""
-        self._name = name
+        _name = name
 
     def get_video_count(self) -> int:
```

## What the grader reported

- `getters_setters` (Getter and setter methods enforce validation guards against negative counts): `E     + Initial`
- Passing: YouTubeChannel protects attributes using private (_ and __) naming encapsulation, Explicit type hints added to parameters and return types on constructor and __str__()

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements encapsulation and type hints, but there is an issue with how the name is updated.

**Getter and setter methods enforce validation guards against negative counts**: The name of the channel remains 'Initial' even after the setter method is called to change it to 'Updated'.
- 💡 Inside your set_name method, are you updating the class attribute or just creating a local variable?

**Next step:** Review the set_name method in the YouTubeChannel class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `getters_setters`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint was an either/or with the answer in it. Now compares the setter line with the same line in __init__.

status: todo

```json
{
  "summary": "Your encapsulation and type hints work, but set_name does not change the name.",
  "items": [
    {
      "test_key": "getters_setters",
      "what_went_wrong": "The name is still 'Initial' after calling set_name('Updated').",
      "hint": "Compare the line inside set_name with the matching line in __init__. What is different?"
    }
  ],
  "next_step": "Review the set_name method in the YouTubeChannel class."
}
```
