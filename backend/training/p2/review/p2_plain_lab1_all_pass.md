<!-- p2-review | case=p2_plain_lab1_all_pass | drafted_by=claude-pre-edit | prompt=v5 -->
# p2_plain_lab1_all_pass

**Lab 1: Image Processing** · `all_pass` · unchanged model solution: nothing unusual to point out

## The bug (ground truth -- the model never sees this diff)

```diff
(no change: model solution as-is)
```

## What the grader reported

- All automated checks passed.
- Passing: Part 1 script (bears2.py) and generated filter image (bears2.jpg) exist, bears2.py filters bears_copy.jpg into a valid non-trivial bears2.jpg, Part 2 script (bears3.py) and generated composite image (bears3.jpg) exist, Submitted bears3.jpg opens as a valid non-trivial composite image

## Draft by `claude-pre-edit` (written directly, no model draft), as the student would see it

Great job! Both parts of the lab pass their automated checks.

**Next step:** Try another filter with the same pixel loop, such as a sepia tone or an inverted image, and compare the results.

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
  "summary": "Great job! Both parts of the lab pass their automated checks.",
  "items": [],
  "next_step": "Try another filter with the same pixel loop, such as a sepia tone or an inverted image, and compare the results."
}
```
