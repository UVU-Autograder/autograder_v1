<!-- p2-review | case=p2_ds4_cookie_floor_division | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_cookie_floor_division

**Dessert Shop 4: Abstraction** · `cascading_failure` · Cookie uses // 12, so six cookies cost $0.00

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -32,5 +32,5 @@
 
     def calculate_cost(self) -> float:
-        return round((self.cookie_quantity / 12) * self.price_per_dozen, 2)
+        return round((self.cookie_quantity // 12) * self.price_per_dozen, 2)
```

## What the grader reported

- `calculate_cost` (calculate_cost() computes price per weight, dozen, and scoops for subclasses): `E     Expected: 2.0 ± 2.0e-06`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.14 ± 1.4e-07`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 7.98 ± 8.0e-06`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the cost calculation logic for specific dessert types is currently returning incorrect values, which is causing the tax and order totals to be inaccurate as well.

**calculate_cost() computes price per weight, dozen, and scoops for subclasses**: The cost for a Cookie is returning 0.0 instead of the expected value.
- 💡 How does your current math handle a quantity of 6 when the price is per dozen?

**calculate_tax() computes tax based on item cost and tax_percent**: The tax calculation is returning 0.0 because the underlying cost calculation is returning 0.0.
- 💡 If the cost calculation is fixed, will the tax calculation automatically produce the correct result?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total order cost is lower than expected.
- 💡 Since this is an aggregate total, which specific dessert types might be contributing incorrect costs to the sum?

**Next step:** Review the `calculate_cost` method in the `Cookie` class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_cost`, `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Kept the good hint; items 2 and 3 now say they follow from the Cookie cost.

> v8 revision (Claude): removed the costs and totals; hint traces a partial dozen by hand; trimmed

> p3b (Claude): shorter first item and follow-on items; trimmed to 65 words

> p4 (Claude): trimmed to 55 words or fewer; follow-on items kept brief (p3b ran 87-106 words on 3-item cascades)

> p4b (Claude): 45 words; verified: the hand-trace hint does not name the operator; diagnosis (partial dozen costs too little) matches the diff and original

status: approved

```json
{
  "summary": "Your tax rate works; the Cookie cost is off.",
  "items": [
    {
      "test_key": "calculate_cost",
      "what_went_wrong": "A Cookie costs too little for a partial dozen.",
      "hint": "Can you trace Cookie.calculate_cost by hand for half a dozen?"
    },
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "Same cause.",
      "hint": "Fix the Cookie cost first."
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order cost is low too.",
      "hint": "Same cause."
    }
  ],
  "next_step": "Review Cookie.calculate_cost."
}
```
