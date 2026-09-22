<!-- p2-review | case=p2_ds4_sundae_super_cost_unrounded_topping | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_sundae_super_cost_unrounded_topping

**Dessert Shop 4: Abstraction** · `cascading_failure` · Sundae multiplies the topping price by the scoop count

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -53,5 +53,5 @@
     def calculate_cost(self) -> float:
         base_cost = super().calculate_cost()
-        return round(base_cost + self.topping_price, 2)
+        return round(base_cost + self.topping_price * self.scoop_count, 2)
```

## What the grader reported

- `calculate_cost` (calculate_cost() computes price per weight, dozen, and scoops for subclasses): `E     Expected: 3.36 ± 3.4e-06`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 7.98 ± 8.0e-06`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_tax() computes tax based on item cost and tax_percent

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the cost calculation logic is producing values higher than expected, which is affecting the total order calculations.

**calculate_cost() computes price per weight, dozen, and scoops for subclasses**: The cost for the Sundae is being calculated as 5.94 instead of 3.36.
- 💡 How is the topping price being factored into the total cost in the Sundae class?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total order cost is higher than the expected 7.98.
- 💡 Since this depends on individual item costs, does the Sundae cost calculation align with the requirements?

**Next step:** Review the calculate_cost method in the Sundae class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_cost`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Kept the good hint; order_totals now says it follows from the Sundae cost.

status: todo

```json
{
  "summary": "Candy, Cookie and IceCream costs are right. The Sundae cost is too high, and the order total follows from it.",
  "items": [
    {
      "test_key": "calculate_cost",
      "what_went_wrong": "A Sundae costs 5.94; the test expects 3.36.",
      "hint": "How is the topping price being factored into the total cost in the Sundae class? Can you work out a 3-scoop sundae by hand?"
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order cost is 10.56 instead of 7.98 because it includes the Sundae.",
      "hint": "This follows from the Sundae problem. Fix that first."
    }
  ],
  "next_step": "Review the calculate_cost method in the Sundae class."
}
```
