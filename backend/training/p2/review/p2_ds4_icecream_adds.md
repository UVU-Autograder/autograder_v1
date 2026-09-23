<!-- p2-review | case=p2_ds4_icecream_adds | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_icecream_adds

**Dessert Shop 4: Abstraction** · `cascading_failure` · IceCream cost adds scoops and price instead of multiplying

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -42,5 +42,5 @@
 
     def calculate_cost(self) -> float:
-        return round(self.scoop_count * self.price_per_scoop, 2)
+        return round(self.scoop_count + self.price_per_scoop, 2)
```

## What the grader reported

- `calculate_cost` (calculate_cost() computes price per weight, dozen, and scoops for subclasses): `E     Expected: 1.58 ± 1.6e-06`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.11 ± 1.1e-07`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 7.98 ± 8.0e-06`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the cost calculation logic is currently producing incorrect values for several dessert types.

**calculate_cost() computes price per weight, dozen, and scoops for subclasses**: The cost for IceCream is being calculated by adding the number of scoops to the price per scoop, rather than multiplying them.
- 💡 How should the total cost of ice cream be derived from the number of scoops and the price per scoop?

**calculate_tax() computes tax based on item cost and tax_percent**: The tax calculation is returning a value higher than expected.
- 💡 Is the tax calculation using the correct base cost before applying the tax percentage?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total order cost and tax are incorrect.
- 💡 Since this depends on the individual item costs, which specific dessert classes should you verify first?

**Next step:** Review the calculate_cost method in the IceCream class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_cost`, `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): what_went_wrong gave the fix ('rather than multiplying'). Now states the numbers from the assertion and asks the student to work it by hand.

status: accepted

```json
{
  "summary": "Candy, Cookie and Sundae are calculating correctly. One cost calculation is off, and the tax and order totals inherit that mistake.",
  "items": [
    {
      "test_key": "calculate_cost",
      "what_went_wrong": "IceCream's cost came out as 2.79, but the test expects 1.58.",
      "hint": "Can you work out the cost of this IceCream by hand, then compare each step with the line in IceCream.calculate_cost?"
    },
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "The IceCream tax is 0.2 instead of 0.11 because it is based on the wrong cost.",
      "hint": "This follows from the calculate_cost problem. Fix that first."
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order cost is 10.81 instead of 7.98 because it includes the IceCream cost.",
      "hint": "This clears once IceCream's cost is right."
    }
  ],
  "next_step": "Review the calculate_cost method in the IceCream class."
}
```
