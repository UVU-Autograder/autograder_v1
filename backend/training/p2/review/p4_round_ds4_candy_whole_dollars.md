<!-- p2-review | case=p4_round_ds4_candy_whole_dollars | drafted_by=gemma4-12b-qat | prompt=v9 -->
# p4_round_ds4_candy_whole_dollars

**Dessert Shop 4: Abstraction** · `cascading_failure` · candy cost rounded to whole dollars

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -22,5 +22,5 @@
 
     def calculate_cost(self) -> float:
-        return round(self.candy_weight * self.price_per_pound, 2)
+        return round(self.candy_weight * self.price_per_pound)
```

## What the grader reported

- `calculate_cost` (calculate_cost() computes price per weight, dozen, and scoops for subclasses): `E     Expected: 0.38 ± 3.8e-07`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.03 ± 3.0e-08`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 7.98 ± 8.0e-06`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%

## Draft by `gemma4-12b-qat` (prompt v9), as the student would see it

Your implementation of the cost calculation logic is currently returning incorrect values for several dessert types.

**calculate_cost() computes price per weight, dozen, and scoops for subclasses**: The cost calculation for candy is returning zero instead of the expected amount.
- 💡 How does the formula for weight multiplied by price per pound differ from your current return statement?

**calculate_tax() computes tax based on item cost and tax_percent**: The tax calculation is resulting in zero for some items.
- 💡 If the cost is zero, what does that imply about the resulting tax calculation?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total order cost does not match the expected sum of all items.
- 💡 Check if the individual cost calculations for each dessert type are correct, as they aggregate into this total.

**Next step:** Review the math formulas in each subclass's calculate_cost method.

Automatic checks on the draft: **FAIL** -- 110 words; targets stay at 65 or fewer (the prompt's limit is 80, and the model writes longer than its targets); 110 words with three items; keep follow-on items brief (55 or fewer, the model writes longer than its targets)

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_cost`, `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4 pre-edit (Claude): Lower direction verified; the hint asks about an existing round call's precision without giving the value; tax_percent not blamed; follow-on items are brief.

> p4b (Claude): 44 words; verified lower direction; hint asks precision of the existing round call, as approved; tax_percent not blamed.

status: approved

```json
{
  "summary": "Your abstract class and default tax rate work, but Candy costs come out too low.",
  "items": [
    {
      "test_key": "calculate_cost",
      "what_went_wrong": "A Candy's cost is much lower than expected.",
      "hint": "How precisely does Candy.calculate_cost round its result?"
    },
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "Same cause.",
      "hint": "Fix the cost first."
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "Same cause.",
      "hint": "Same fix."
    }
  ],
  "next_step": "Review Candy.calculate_cost in dessert.py."
}
```
