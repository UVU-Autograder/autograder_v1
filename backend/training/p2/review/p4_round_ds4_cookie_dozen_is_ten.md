<!-- p2-review | case=p4_round_ds4_cookie_dozen_is_ten | drafted_by=gemma4-12b-qat | prompt=v9 -->
# p4_round_ds4_cookie_dozen_is_ten

**Dessert Shop 4: Abstraction** · `cascading_failure` · cookie cost divides by 10 instead of 12

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -32,5 +32,5 @@
 
     def calculate_cost(self) -> float:
-        return round((self.cookie_quantity / 12) * self.price_per_dozen, 2)
+        return round((self.cookie_quantity / 10) * self.price_per_dozen, 2)
```

## What the grader reported

- `calculate_cost` (calculate_cost() computes price per weight, dozen, and scoops for subclasses): `E     Expected: 2.0 ± 2.0e-06`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.14 ± 1.4e-07`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 7.98 ± 8.0e-06`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%

## Draft by `gemma4-12b-qat` (prompt v9), as the student would see it

Your implementation of the cost and tax calculations is producing incorrect totals.

**calculate_cost() computes price per weight, dozen, and scoops for subclasses**: The cost calculation for cookies does not correctly account for the quantity relative to a dozen.
- 💡 How many cookies are in a dozen, and how should that be used to determine the cost of a specific quantity?

**calculate_tax() computes tax based on item cost and tax_percent**: The tax amount is being calculated incorrectly for individual items.
- 💡 Should the tax be rounded at the individual item level or only at the final total?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The final order totals are not matching the expected sums.
- 💡 If the individual costs or taxes are slightly off, how does that affect the final sum?

**Next step:** Review the math logic in the Cookie.calculate_cost method.

Automatic checks on the draft: **FAIL** -- 109 words; targets stay at 65 or fewer (the prompt's limit is 80, and the model writes longer than its targets); 109 words with three items; keep follow-on items brief (55 or fewer, the model writes longer than its targets)

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_cost`, `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4 pre-edit (Claude): Higher direction verified; the dozen-conversion hint names no divisor or operator; tax and order items correctly follow from the cost.

> p4b (Claude): 45 words; verified higher direction; dozen hint names no divisor; test_keys and diagnosis match original.

status: approved

```json
{
  "summary": "Your abstract class and default tax rate work, but Cookie costs come out too high.",
  "items": [
    {
      "test_key": "calculate_cost",
      "what_went_wrong": "A Cookie's cost is higher than expected.",
      "hint": "How does Cookie.calculate_cost turn the cookie count into dozens?"
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
  "next_step": "Review Cookie.calculate_cost in dessert.py."
}
```
