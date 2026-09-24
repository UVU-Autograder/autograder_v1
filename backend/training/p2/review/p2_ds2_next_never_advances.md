<!-- p2-review | case=p2_ds2_next_never_advances | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_next_never_advances

**Dessert Shop 2: Using Classes in main** · `cascading_failure` · __next__ never increments the index: the for loop never ends (time limit)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -51,4 +51,3 @@
             raise StopIteration
         item = self.order[self._index]
-        self._index += 1
         return item
```

## What the grader reported

- `execution_error` (Submission could not run): `Time limit exceeded`

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy is correctly implemented, but the Order class and main execution are encountering timeout issues.

**Order class defines order list, add() method, and len() support**: The test timed out while trying to convert the Order object into a list.
- 💡 How does your __iter__ method behave when it is called multiple times, and does it correctly reset the index?

**dessertshop.py main() constructs Order items and prints formatted receipt**: The main execution timed out during the loop that prints item names.
- 💡 If the iteration logic in the Order class is causing an infinite loop, how might that affect the main function's execution time?

**Next step:** Review the __iter__ and __next__ methods in the Order class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_class`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft blamed __iter__ resetting the index; the loop never ends because __next__ never moves forward. Hint now asks what changes between calls.

> Updated after 4159d52 (Claude): The whole run now hits the time limit, so the grader reports one execution_error instead of two test failures. Rewritten around that.

status: todo

```json
{
  "summary": "Your class hierarchy is written, but the submission never finished running: something loops forever.",
  "items": [
    {
      "test_key": "execution_error",
      "what_went_wrong": "The run was stopped with \"Time limit exceeded\", so none of the tests could finish.",
      "hint": "Can you trace __next__ for an order with two items? Does anything change between one call and the next?"
    }
  ],
  "next_step": "Review the __next__ method in the Order class, then run dessertshop.py yourself to check it finishes."
}
```
