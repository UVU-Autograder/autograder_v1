<!-- p2-review | case=p2_ds4_candy_method_typo | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_candy_method_typo

**Dessert Shop 4: Abstraction** · `cascading_failure` · Candy defines calculate_costs (typo), so the abstract method is never implemented

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -21,5 +21,5 @@
         self.price_per_pound = price_per_pound
 
-    def calculate_cost(self) -> float:
+    def calculate_costs(self) -> float:
         return round(self.candy_weight * self.price_per_pound, 2)
```

## What the grader reported

- `tax_percent` (DessertItem tax_percent attribute defaults to 7.25%): `E   TypeError: Can't instantiate abstract class Candy without an implementation for abstract method 'calculate_cost'`
- `calculate_cost` (calculate_cost() computes price per weight, dozen, and scoops for subclasses): `E   TypeError: Can't instantiate abstract class Candy without an implementation for abstract method 'calculate_cost'`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E   TypeError: Can't instantiate abstract class Candy without an implementation for abstract method 'calculate_cost'`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E   TypeError: Can't instantiate abstract class Candy without an implementation for abstract method 'calculate_cost'`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost()

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully defines the abstract base class, but several tests are failing because the Candy class cannot be instantiated.

**DessertItem tax_percent attribute defaults to 7.25%**: The Candy class cannot be instantiated because it does not provide an implementation for the abstract method 'calculate_cost'.
- 💡 How does the method name in your Candy class compare to the abstract method name defined in DessertItem?

**calculate_cost() computes price per weight, dozen, and scoops for subclasses**: This failure follows from the missing implementation of the abstract method in the Candy class.
- 💡 Check the spelling of your cost calculation method in the Candy class.

**calculate_tax() computes tax based on item cost and tax_percent**: This failure follows from the missing implementation of the abstract method in the Candy class.
- 💡 Ensure all subclasses of an abstract class implement all abstract methods.

**Order methods order_cost() and order_tax() aggregate total prices accurately**: This failure follows from the missing implementation of the abstract method in the Candy class.
- 💡 Review the Candy class to ensure it correctly overrides the required abstract method.

**Next step:** Examine the method name in the Candy class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `tax_percent`, `calculate_cost`, `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): 4 items cut to 3; one root cause (the method name in Candy) explained once, the rest follow from it.

status: accepted

```json
{
  "summary": "Your abstract base class is set up correctly. Every failure here comes from one small problem in the Candy class.",
  "items": [
    {
      "test_key": "calculate_cost",
      "what_went_wrong": "Python refuses to create a Candy because it still sees the abstract calculate_cost method as unimplemented.",
      "hint": "Put the method name in Candy next to the abstract method name in DessertItem. Are they exactly the same, letter for letter?"
    },
    {
      "test_key": "tax_percent",
      "what_went_wrong": "This test also creates a Candy, so it fails for the same reason.",
      "hint": "This follows from the calculate_cost problem. Fix that first."
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order includes a Candy, so the totals fail for the same reason.",
      "hint": "This clears once a Candy can be created."
    }
  ],
  "next_step": "Compare the method names in Candy with the ones DessertItem marks as abstract, then rerun the tests."
}
```
