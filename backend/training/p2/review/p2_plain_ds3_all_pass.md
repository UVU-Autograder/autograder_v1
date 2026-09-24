<!-- p2-review | case=p2_plain_ds3_all_pass | drafted_by=claude-pre-edit | prompt=v5 -->
# p2_plain_ds3_all_pass

**Dessert Shop 3: Test Cases with pytest** · `all_pass` · unchanged model solution: nothing unusual to point out

## The bug (ground truth -- the model never sees this diff)

```diff
(no change: model solution as-is)
```

## What the grader reported

- All automated checks passed.
- Passing: DS2 class hierarchy and Order class methods intact, test_dessert.py exists and defines at least 15 valid test functions, Student test suite executes cleanly and passes all assertions

## Draft by `claude-pre-edit` (written directly, no model draft), as the student would see it

Great job! Your classes pass, and every one of your own tests passes too.

**Next step:** Try writing one test you expect to fail, run pytest to see what it reports, then fix or remove it.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Plain all-pass case, added because the first adapter invented problems on clean solutions. The next step is an extension that fits the assignment and claims nothing about the student's code.

status: accepted

```json
{
  "summary": "Great job! Your classes pass, and every one of your own tests passes too.",
  "items": [],
  "next_step": "Try writing one test you expect to fail, run pytest to see what it reports, then fix or remove it."
}
```
