<!-- p2-review | case=p2_ds4_concept_exceptions | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_concept_exceptions

**Dessert Shop 4: Abstraction** · `concept_violation` · Candy raises ValueError on negative weight (exceptions, Module 7) in a Module 6 project; tests pass

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -18,4 +18,6 @@
     def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0):
         super().__init__(name)
+        if candy_weight < 0:
+            raise ValueError("weight cannot be negative")
         self.candy_weight = candy_weight
         self.price_per_pound = price_per_pound
```

## What the grader reported

- All automated checks passed.
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_cost() computes price per weight, dozen, and scoops for subclasses, calculate_tax() computes tax based on item cost and tax_percent, Order methods order_cost() and order_tax() aggregate total prices accurately
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [dessert.py] Concept 'exceptions' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! All of your functional tests passed successfully.

**Next step:** Review the allowed concepts list to see how you can handle input validation without using exceptions.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Small edit only: the draft already avoided calling it complete and pointed back to the allowed concepts.

status: todo

```json
{
  "summary": "All of your cost and tax tests pass.",
  "items": [],
  "next_step": "Your Candy raises an exception for negative weight, and exceptions come later in the course. Review this module's allowed concepts and handle that case without them for now."
}
```
