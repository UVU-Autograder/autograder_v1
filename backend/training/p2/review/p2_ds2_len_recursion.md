<!-- p2-review | case=p2_ds2_len_recursion | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_len_recursion

**Dessert Shop 2: Using Classes in main** · `cascading_failure` · __len__ returns len(self), which calls __len__ forever (RecursionError)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -41,5 +41,5 @@
 
     def __len__(self) -> int:
-        return len(self.order)
+        return len(self)
 
     def __iter__(self) -> "Order":
```

## What the grader reported

- `order_class` (Order class defines order list, add() method, and len() support): `!!! Recursion detected (same locals & position)`
- `main_output` (dessertshop.py main() constructs Order items and prints formatted receipt): `E   AssertionError: dessertshop.py execution failed: maximum recursion depth exceeded`
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae)

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy is correctly implemented, but there is a logic error in how the length of the order is being calculated.

**Order class defines order list, add() method, and len() support**: The __len__ method is calling itself recursively instead of accessing the underlying list.
- 💡 What should the __len__ method actually return to provide the count of items in the order?

**dessertshop.py main() constructs Order items and prints formatted receipt**: The program crashes with a RecursionError when trying to print the total number of items.
- 💡 How does the error in your __len__ method affect the rest of the program's execution?

**Next step:** Review the __len__ method in the Order class in dessert.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_class`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): what_went_wrong gave the fix ('instead of accessing the underlying list'). Now describes the RecursionError and asks the student to trace the return line.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your class hierarchy is correctly implemented, but asking an Order for its length never finishes.",
  "items": [
    {
      "test_key": "order_class",
      "what_went_wrong": "len(order) fails with a RecursionError: maximum recursion depth exceeded.",
      "hint": "When Python runs len(order), it calls your __len__. Can you trace what the return line of __len__ asks Python to do next?"
    },
    {
      "test_key": "main_output",
      "what_went_wrong": "main crashes with the same RecursionError when it prints the item count.",
      "hint": "This follows from the __len__ problem. Fix that first."
    }
  ],
  "next_step": "Review the __len__ method in the Order class in dessert.py."
}
```
