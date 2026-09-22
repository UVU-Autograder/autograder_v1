<!-- p2-review | case=p2_ds1_concept_abc | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_concept_abc

**Dessert Shop 1: Inheritance Superclass** · `concept_violation` · DessertItem inherits ABC (abstract classes, Module 6) in a Module 3 project; tests pass

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -1,3 +1,6 @@
-class DessertItem:
+from abc import ABC
+
+
+class DessertItem(ABC):
     def __init__(self, name: str = ""):
         self.name = name
```

## What the grader reported

- All automated checks passed.
- Passing: DessertItem base class defines name attribute with default '', Candy inherits DessertItem and defines candy_weight & price_per_pound, Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen, IceCream inherits DessertItem and defines scoop_count & price_per_scoop, Sundae inherits IceCream and defines topping_name & topping_price
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [dessert.py] Concept 'abstract-classes' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Great job! Your implementation of the inheritance hierarchy for the dessert shop is complete and passed all tests.

**Next step:** Review the allowed concepts list to see how to handle class structures without using abstract base classes.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Removed 'complete' (the prompt says never to call the work complete when there is a concept warning); the next step points back to the allowed concepts.

status: todo

```json
{
  "summary": "All the tests pass and your inheritance hierarchy works.",
  "items": [],
  "next_step": "Your DessertItem uses ABC, which comes later in the course. Review this module's allowed concepts and rework DessertItem as a plain base class."
}
```
