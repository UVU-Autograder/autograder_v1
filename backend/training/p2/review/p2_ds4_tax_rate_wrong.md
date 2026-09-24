<!-- p2-review | case=p2_ds4_tax_rate_wrong | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_tax_rate_wrong

**Dessert Shop 4: Abstraction** · `cascading_failure` · tax_percent defaults to 8.25 instead of 7.25

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -5,5 +5,5 @@
     def __init__(self, name: str = ""):
         self.name = name
-        self.tax_percent: float = 7.25
+        self.tax_percent: float = 8.25
 
     @abstractmethod
```

## What the grader reported

- `tax_percent` (DessertItem tax_percent attribute defaults to 7.25%): `E    +  where 8.25 = <dessert.Candy object at 0x0000020137C886E0>.tax_percent`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.14 ± 1.4e-07`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 0.57 ± 5.7e-07`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), calculate_cost() computes price per weight, dozen, and scoops for subclasses

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the DessertItem class and the Order calculations are mostly correct, but there is an issue with the default tax rate and how taxes are aggregated.

**DessertItem tax_percent attribute defaults to 7.25%**: The default tax_percent attribute is set to 8.25 instead of the required 7.25.
- 💡 What value should the tax_percent attribute in the DessertItem class default to?

**calculate_tax() computes tax based on item cost and tax_percent**: The tax calculation for a single item is returning a value higher than expected.
- 💡 How does the current tax_percent value affect the result of the calculate_tax method?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total tax for the order is higher than expected.
- 💡 If the individual item taxes are incorrect due to the tax rate, how will that affect the sum in order_tax?

**Next step:** Review the DessertItem class definition to verify the default value of tax_percent.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `tax_percent`, `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The summary blamed 'how taxes are aggregated' (they are not); one root cause, the default rate, with the tax and totals following from it.

status: accepted

```json
{
  "summary": "Your cost calculations and Order methods work. Every tax value is a little high, and they all come from one default.",
  "items": [
    {
      "test_key": "tax_percent",
      "what_went_wrong": "A new Candy has tax_percent 8.25; the test expects the default to be 7.25.",
      "hint": "Double check your code: where does DessertItem set tax_percent, and does it match the rate in the assignment?"
    },
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "The Cookie tax is 0.17 instead of 0.14 because it uses that rate.",
      "hint": "This follows from the tax_percent problem. Fix that first."
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order tax is 0.67 instead of 0.57 for the same reason.",
      "hint": "This clears once the default rate is right."
    }
  ],
  "next_step": "Review where tax_percent is set in the DessertItem class."
}
```
