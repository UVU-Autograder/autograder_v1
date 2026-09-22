<!-- p2-review | case=p2_lab3_concept_property | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab3_concept_property

**Lab 3: Type Hinting and Encapsulation** · `concept_violation` · adds a @property (properties, Module 3) in a Module 2 lab; tests pass

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/youtube_channel.py
+++ student/youtube_channel.py
@@ -13,4 +13,8 @@
         """Return formatted string representation of channel."""
         return f"Channel: {self._name}, Videos: {self.__video_count}"
+
+    @property
+    def name(self) -> str:
+        return self._name
 
     def get_name(self) -> str:
```

## What the grader reported

- All automated checks passed.
- Passing: YouTubeChannel protects attributes using private (_ and __) naming encapsulation, Getter and setter methods enforce validation guards against negative counts, Explicit type hints added to parameters and return types on constructor and __str__()
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [youtube_channel.py] Concept 'properties' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Great job! Your code successfully passed all the automated tests and met the core requirements.

**Next step:** Review the allowed concepts list to ensure your implementation strictly follows the project constraints.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft said 'met the core requirements' and gave a vague next step. Now names the concept and a way to rework it.

status: todo

```json
{
  "summary": "All the tests pass and your encapsulation works.",
  "items": [],
  "next_step": "Your class adds a @property, which comes in Module 3. Review this module's allowed concepts and use your get_name method instead for now."
}
```
