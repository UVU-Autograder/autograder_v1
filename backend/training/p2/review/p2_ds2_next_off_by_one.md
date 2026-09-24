<!-- p2-review | case=p2_ds2_next_off_by_one | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_next_off_by_one

**Dessert Shop 2: Using Classes in main** · `cascading_failure` · __next__ stops at > instead of >=, so it reads one past the end (IndexError)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -48,5 +48,5 @@
 
     def __next__(self) -> DessertItem:
-        if self._index >= len(self.order):
+        if self._index > len(self.order):
             raise StopIteration
         item = self.order[self._index]
```

## What the grader reported

- `order_class` (Order class defines order list, add() method, and len() support): `E   IndexError: list index out of range`
- `main_output` (dessertshop.py main() constructs Order items and prints formatted receipt): `E   AssertionError: dessertshop.py execution failed: list index out of range`
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae)

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy is correctly implemented, but there is an issue with how the Order class handles iteration.

**Order class defines order list, add() method, and len() support**: The iterator attempts to access an index that is outside the bounds of the order list.
- 💡 How does the condition in your __next__ method compare to the maximum valid index of a list?

**dessertshop.py main() constructs Order items and prints formatted receipt**: The main execution fails because the iterator reaches an out-of-bounds index during the loop.
- 💡 If the first error is resolved, will this loop be able to complete successfully?

**Next step:** Review the logic in the __next__ method of the Order class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_class`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Small edit: main_output now says it follows from __next__. The hint was already good.

status: accepted

```json
{
  "summary": "Your class hierarchy is correctly implemented, but there is an issue with how the Order class handles iteration.",
  "items": [
    {
      "test_key": "order_class",
      "what_went_wrong": "Looping over an Order fails with \"IndexError: list index out of range\" at the end of the list.",
      "hint": "How does the condition in your __next__ method compare to the last valid index of a list?"
    },
    {
      "test_key": "main_output",
      "what_went_wrong": "main crashes with the same IndexError in its for loop.",
      "hint": "This follows from the __next__ problem. Fix that first."
    }
  ],
  "next_step": "Review the stopping condition in the __next__ method of the Order class."
}
```
