<!-- p2-review | case=p2_ds4_sundae_no_topping | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_sundae_no_topping

**Dessert Shop 4: Abstraction** · `cascading_failure` · Sundae cost leaves out the topping

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -53,5 +53,5 @@
     def calculate_cost(self) -> float:
         base_cost = super().calculate_cost()
-        return round(base_cost + self.topping_price, 2)
+        return round(base_cost, 2)
```

## What the grader reported

- `calculate_cost` (calculate_cost() computes price per weight, dozen, and scoops for subclasses): `E     Expected: 3.36 ± 3.4e-06`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 7.98 ± 8.0e-06`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_tax() computes tax based on item cost and tax_percent

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the dessert cost calculations is currently missing some components, which is affecting the total order totals.

**calculate_cost() computes price per weight, dozen, and scoops for subclasses**: The cost for a Sundae is being calculated as 2.07 instead of 3.36.
- 💡 How does the Sundae class incorporate the price of the topping into its total cost?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total order cost is lower than expected.
- 💡 If the individual item costs are incorrect, how will that impact the final sum in the Order class?

**Next step:** Review the Sundae.calculate_cost method in dessert.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_cost`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint named the topping (the fix). Now asks which part of the price 2.07 covers.

status: todo

```json
{
  "summary": "Candy, Cookie and IceCream costs are right. The Sundae cost is low, and the order total follows from it.",
  "items": [
    {
      "test_key": "calculate_cost",
      "what_went_wrong": "A Sundae costs 2.07; the test expects 3.36.",
      "hint": "Which part of a sundae's price does 2.07 account for, and which part is missing from Sundae.calculate_cost?"
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order cost is 6.69 instead of 7.98 because it includes the Sundae.",
      "hint": "This follows from the Sundae problem. Fix that first."
    }
  ],
  "next_step": "Review the calculate_cost method in the Sundae class."
}
```
