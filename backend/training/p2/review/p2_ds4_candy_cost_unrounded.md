<!-- p2-review | case=p2_ds4_candy_cost_unrounded | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_candy_cost_unrounded

**Dessert Shop 4: Abstraction** · `single_failure` · Candy.calculate_cost does not round

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -22,5 +22,5 @@
 
     def calculate_cost(self) -> float:
-        return round(self.candy_weight * self.price_per_pound, 2)
+        return self.candy_weight * self.price_per_pound
```

## What the grader reported

- `calculate_cost` (calculate_cost() computes price per weight, dozen, and scoops for subclasses): `E     Expected: 0.38 ± 3.8e-07`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 7.98 ± 8.0e-06`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_tax() computes tax based on item cost and tax_percent

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the dessert cost calculations is nearly correct, but there are some discrepancies in how rounding is applied during intermediate steps.

**calculate_cost() computes price per weight, dozen, and scoops for subclasses**: The cost for the Candy item is being calculated as 0.375 instead of the expected 0.38.
- 💡 Should the rounding occur inside the individual item's cost calculation or only at the final order total?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total order cost is slightly lower than expected.
- 💡 How does rounding each individual item's cost affect the final sum of the order?

**Next step:** Review the requirements for when to apply the round() function in the calculate_cost methods.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_cost`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint was an either/or with the answer in it, and next_step named round(). Now points to comparing Candy with the classes that work.

status: todo

```json
{
  "summary": "Your abstract class and most of your cost calculations are working. Candy's cost is very close but not quite what the test expects.",
  "items": [
    {
      "test_key": "calculate_cost",
      "what_went_wrong": "Candy's cost comes out as 0.375, but the test expects 0.38.",
      "hint": "Double check your code: compare Candy.calculate_cost with the calculate_cost methods that pass. What do they do to the result before returning it?"
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order cost is 7.97 instead of 7.98 because of the Candy cost.",
      "hint": "This follows from the Candy problem. Fix that first."
    }
  ],
  "next_step": "Compare calculate_cost across your four dessert classes."
}
```
