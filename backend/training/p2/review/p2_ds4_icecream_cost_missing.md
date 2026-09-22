<!-- p2-review | case=p2_ds4_icecream_cost_missing | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_icecream_cost_missing

**Dessert Shop 4: Abstraction** · `cascading_failure` · IceCream never defines calculate_cost, so it cannot be instantiated

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -41,7 +41,4 @@
         self.price_per_scoop = price_per_scoop
 
-    def calculate_cost(self) -> float:
-        return round(self.scoop_count * self.price_per_scoop, 2)
-
 
 class Sundae(IceCream):
```

## What the grader reported

- `calculate_cost` (calculate_cost() computes price per weight, dozen, and scoops for subclasses): `E   TypeError: Can't instantiate abstract class IceCream without an implementation for abstract method 'calculate_cost'`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E   TypeError: Can't instantiate abstract class IceCream without an implementation for abstract method 'calculate_cost'`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E   TypeError: Can't instantiate abstract class IceCream without an implementation for abstract method 'calculate_cost'`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the DessertItem hierarchy is mostly correct, but there is an issue with how the IceCream class handles abstract methods.

**calculate_cost() computes price per weight, dozen, and scoops for subclasses**: The IceCream class cannot be instantiated because it does not provide an implementation for the abstract method 'calculate_cost'.
- 💡 How does a subclass of an abstract class need to behave to be instantiated?

**calculate_tax() computes tax based on item cost and tax_percent**: This failure follows from the missing implementation in the IceCream class.
- 💡 Check the IceCream class definition.

**Order methods order_cost() and order_tax() aggregate total prices accurately**: This failure follows from the missing implementation in the IceCream class.
- 💡 Check the IceCream class definition.

**Next step:** Review the IceCream class definition in dessert.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_cost`, `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Sharper first hint: compare IceCream's methods with Candy's and Cookie's.

status: todo

```json
{
  "summary": "Your DessertItem hierarchy is mostly correct, but Python will not create an IceCream, and three tests depend on it.",
  "items": [
    {
      "test_key": "calculate_cost",
      "what_went_wrong": "Python refuses to create an IceCream because it has no implementation of the abstract method calculate_cost.",
      "hint": "Can you compare the methods IceCream defines with the ones Candy and Cookie define? What does DessertItem require every subclass to have?"
    },
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "This test creates an IceCream, so it fails for the same reason.",
      "hint": "This follows from the IceCream problem. Fix that first."
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order includes an IceCream, so it fails for the same reason.",
      "hint": "This clears once an IceCream can be created."
    }
  ],
  "next_step": "Review the IceCream class definition in dessert.py."
}
```
