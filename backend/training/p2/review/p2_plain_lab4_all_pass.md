<!-- p2-review | case=p2_plain_lab4_all_pass | drafted_by=claude-pre-edit | prompt=v5 -->
# p2_plain_lab4_all_pass

**Lab 4: Properties and Validation** · `all_pass` · unchanged model solution: nothing unusual to point out

## The bug (ground truth -- the model never sees this diff)

```diff
(no change: model solution as-is)
```

## What the grader reported

- All automated checks passed.
- Passing: @property title decorator validates type (str) and non-empty string constraint, @property author decorator validates type (str) and non-empty string constraint, description read-only property formats 'Title by Author' and raises AttributeError on write

## Draft by `claude-pre-edit` (written directly, no model draft), as the student would see it

Great job! Your title, author and description properties all pass their tests.

**Next step:** Try adding a year property that only accepts a four-digit number, using the same validation pattern as title and author.

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
  "summary": "Great job! Your title, author and description properties all pass their tests.",
  "items": [],
  "next_step": "Try adding a year property that only accepts a four-digit number, using the same validation pattern as title and author."
}
```
