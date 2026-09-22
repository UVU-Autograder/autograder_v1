<!-- p2-review | case=p2_ds2_next_returns_list | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_next_returns_list

**Dessert Shop 2: Using Classes in main** · `cascading_failure` · __next__ returns the whole list instead of the current item

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -52,3 +52,3 @@
         item = self.order[self._index]
         self._index += 1
-        return item
+        return self.order
```

## What the grader reported

- `order_class` (Order class defines order list, add() method, and len() support): `E     Use -v to get more diff`
- `main_output` (dessertshop.py main() constructs Order items and prints formatted receipt): `E   AssertionError: dessertshop.py execution failed: 'list' object has no attribute 'name'`
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae)

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy is correctly implemented, but there are issues with how the Order class handles iteration and how items are accessed in main.

**Order class defines order list, add() method, and len() support**: The iterator is returning the entire list of items instead of individual items one by one.
- 💡 In your __next__ method, what specific element from the list should be returned instead of the list itself?

**dessertshop.py main() constructs Order items and prints formatted receipt**: The program crashed because it tried to access a .name attribute on a list object.
- 💡 How does the error in the Order class's __next__ method affect what the 'item' variable becomes during the loop in main?

**Next step:** Review the __next__ method in the Order class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_class`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the fix ('what element should be returned instead of the list'). Now asks the student to compare what __next__ picks out with what it returns.

status: todo

```json
{
  "summary": "Your class hierarchy is correctly implemented, but looping over an Order gives back the wrong thing on each step.",
  "items": [
    {
      "test_key": "order_class",
      "what_went_wrong": "Each step of the loop gives back the whole list instead of one item.",
      "hint": "In __next__ you pick out one item and then return something. Can you compare what you pick out with what you return?"
    },
    {
      "test_key": "main_output",
      "what_went_wrong": "main crashes with \"'list' object has no attribute 'name'\" because each loop item is a list.",
      "hint": "This follows from the __next__ problem. Fix that first."
    }
  ],
  "next_step": "Review the return line of the __next__ method in the Order class."
}
```
