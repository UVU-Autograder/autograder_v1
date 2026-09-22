<!-- p2-review | case=p2_ds4_no_abstractmethod | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_no_abstractmethod

**Dessert Shop 4: Abstraction** · `single_failure` · calculate_cost is not decorated with @abstractmethod

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -7,5 +7,4 @@
         self.tax_percent: float = 7.25
 
-    @abstractmethod
     def calculate_cost(self) -> float:
         pass
```

## What the grader reported

- `abstract_class` (DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost()): `E   Failed: DID NOT RAISE <class 'TypeError'>`
- Passing: DessertItem tax_percent attribute defaults to 7.25%, calculate_cost() computes price per weight, dozen, and scoops for subclasses, calculate_tax() computes tax based on item cost and tax_percent, Order methods order_cost() and order_tax() aggregate total prices accurately

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation correctly handles the cost calculations and tax percentages for all dessert types. However, there is an issue with how the abstract class is defined.

**DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost()**: The test expected a TypeError to be raised when trying to instantiate DessertItem, but it did not.
- 💡 How can you ensure that a method is strictly required to be overridden by subclasses using the correct decorator?

**Next step:** Review the @abstractmethod decorator in the DessertItem class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `abstract_class`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint and next step named @abstractmethod (the fix). Now asks what makes Python treat a method as required.

status: todo

```json
{
  "summary": "Your cost and tax calculations work for every dessert type. The abstract base class is not quite enforcing its rule.",
  "items": [
    {
      "test_key": "abstract_class",
      "what_went_wrong": "Creating a DessertItem worked, but the test expected Python to refuse because DessertItem is abstract.",
      "hint": "Look at how calculate_cost is declared in DessertItem. What makes Python treat a method as one every subclass must provide?"
    }
  ],
  "next_step": "Review how calculate_cost is declared in DessertItem."
}
```
