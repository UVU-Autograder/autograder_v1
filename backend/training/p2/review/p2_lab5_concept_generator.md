<!-- p2-review | case=p2_lab5_concept_generator | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_concept_generator

**Lab 5: Operator Overloading** · `concept_violation` · adds a generator __iter__ (generators, Module 4) in a Module 3 lab; tests pass

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -16,4 +16,8 @@
             self.dollars += self.cents // 100
             self.cents = self.cents % 100
+
+    def __iter__(self):
+        yield self.dollars
+        yield self.cents
 
     def __str__(self) -> str:
```

## What the grader reported

- All automated checks passed.
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __add__() overloads '+' operator to add dollars and cents, Money __mul__() and __rmul__() overload '*' operator for scalar multiplication, Money __eq__() overloads '==' operator comparing normalized total cents
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [money.py] Concept 'generators' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! All of your functional requirements passed the autograder tests.

**Next step:** Review the allowed concepts list to ensure your implementation avoids using restricted features like generators.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Small edit: the next step names the concept and module.

status: accepted

```json
{
  "summary": "All of your operator tests pass.",
  "items": [],
  "next_step": "Your Money class adds a generator __iter__, and generators come in Module 4. Review this module's allowed concepts and rework or remove it for now."
}
```
