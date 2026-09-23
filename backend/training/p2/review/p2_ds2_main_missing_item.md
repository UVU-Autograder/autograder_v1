<!-- p2-review | case=p2_ds2_main_missing_item | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_main_missing_item

**Dessert Shop 2: Using Classes in main** · `single_failure` · main leaves out the Oatmeal Raisin cookie

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -9,5 +9,4 @@
     order.add(IceCream("Pistachio", 2, 0.79))
     order.add(Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29))
-    order.add(Cookie("Oatmeal Raisin", 2, 3.45))
 
     for item in order:
```

## What the grader reported

- `main_output` (dessertshop.py main() constructs Order items and prints formatted receipt): `E    +  where 6 = len(['Candy Corn', 'Gummy Bears', 'Chocolate Chip', 'Pistachio', 'Vanilla', 'Total number of items in order: 5'])`
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae), Order class defines order list, add() method, and len() support

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy and Order class logic are working correctly, but the final output is missing a line.

**dessertshop.py main() constructs Order items and prints formatted receipt**: The printed output contains 6 lines, but the test expects at least 7.
- 💡 If you look at the list of items being printed, is there a specific item or piece of information required by the prompt that isn't appearing in your loop or final print statement?

**Next step:** Review the assignment requirements for the specific items that need to be printed in the receipt.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Tightened: the hint said 'required by the prompt' (the student has no prompt) and was long. Now points to the order.add calls.

status: accepted

```json
{
  "summary": "Your class hierarchy and Order class work, but main's output is one line short.",
  "items": [
    {
      "test_key": "main_output",
      "what_went_wrong": "main printed 6 lines; the test expects at least 7.",
      "hint": "Can you count the order.add calls in main and compare them with the desserts the assignment lists?"
    }
  ],
  "next_step": "Review the order.add calls in main in dessertshop.py."
}
```
