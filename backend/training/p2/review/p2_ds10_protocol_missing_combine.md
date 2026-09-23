<!-- p2-review | case=p2_ds10_protocol_missing_combine | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds10_protocol_missing_combine

**Dessert Shop 10: Combine Like Items** · `single_failure` · Combinable protocol declares can_combine but not combine

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/combine.py
+++ student/combine.py
@@ -9,3 +9,2 @@
 
     def can_combine(self, other: "Combinable") -> bool: ...
-    def combine(self, other: "Combinable") -> "Combinable": ...
```

## What the grader reported

- `combinable_protocol` (Combinable protocol defined in combine.py with can_combine() and combine() methods): `E    +  where False = hasattr(<class 'combine.Combinable'>, 'combine')`
- Passing: Candy implements Combinable protocol merging candy_weight for matching items, Cookie implements Combinable protocol merging cookie_quantity for matching items, Order.add() automatically combines like items when matching item is present, DS9 Order.sort() and relational comparison operators intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the logic for combining items and handles the core dessert classes correctly. However, there is a missing method definition in your protocol.

**Combinable protocol defined in combine.py with can_combine() and combine() methods**: The Combinable protocol is missing the required 'combine' method definition.
- 💡 If you look at the requirements, what specific method name must be included in the Combinable protocol in combine.py?

**Next step:** Review the Combinable protocol definition in combine.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `combinable_protocol`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint asked for the method name (the fix). Now compares the protocol with what Candy and Cookie implement.

status: accepted

```json
{
  "summary": "Your Candy and Cookie combine logic and your Order class work. The protocol definition itself is incomplete.",
  "items": [
    {
      "test_key": "combinable_protocol",
      "what_went_wrong": "The test found no combine method declared on the Combinable protocol.",
      "hint": "Can you compare the methods declared in Combinable with the two methods Candy and Cookie implement? Which one is not declared?"
    }
  ],
  "next_step": "Review the Combinable protocol in combine.py."
}
```
