<!-- p2-review | case=p2_ds4_concept_dataclass | drafted_by=claude-pre-edit | prompt=v5 -->
# p2_ds4_concept_dataclass

**Dessert Shop 4: Abstraction** · `concept_violation` · adds a @dataclass (dataclasses, Module 11) in a Module 6 project; tests pass

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -1,3 +1,10 @@
 from abc import ABC, abstractmethod
+from dataclasses import dataclass
+
+
+@dataclass
+class Box:
+    size: int = 1
+
```

## What the grader reported

- All automated checks passed.
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_cost() computes price per weight, dozen, and scoops for subclasses, calculate_tax() computes tax based on item cost and tax_percent, Order methods order_cost() and order_tax() aggregate total prices accurately
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [dessert.py] Concept 'dataclasses' is not in the allowed list

## Draft by `claude-pre-edit` (written directly, no model draft), as the student would see it

All the cost and tax tests pass, and your abstract class works.

**Next step:** Your dessert.py adds a dataclass, which comes in a later module. Review this module's allowed concepts and write Box as a regular class for now, or leave it out if nothing uses it.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): New case from 4159d52 (replaces the exceptions case now that exceptions are allowed in Module 6). There is no model draft; this target was written directly.

status: todo

```json
{
  "summary": "All the cost and tax tests pass, and your abstract class works.",
  "items": [],
  "next_step": "Your dessert.py adds a dataclass, which comes in a later module. Review this module's allowed concepts and write Box as a regular class for now, or leave it out if nothing uses it."
}
```
