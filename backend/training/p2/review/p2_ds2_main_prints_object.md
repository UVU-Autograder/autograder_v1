<!-- p2-review | case=p2_ds2_main_prints_object | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_main_prints_object

**Dessert Shop 2: Using Classes in main** · `single_failure` · main prints the item object instead of its name

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -12,5 +12,5 @@
 
     for item in order:
-        print(item.name)
+        print(item)
 
     print("Total number of items in order:", len(order))
```

## What the grader reported

- `main_output` (dessertshop.py main() constructs Order items and prints formatted receipt): `E    +  where False = any(<generator object test_main_output.<locals>.<genexpr> at 0x00000209D53C2420>)`
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae), Order class defines order list, add() method, and len() support

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy and Order class logic are working correctly, but the final output is missing a specific item.

**dessertshop.py main() constructs Order items and prints formatted receipt**: The printed output does not contain the expected 'candy corn' item.
- 💡 When you iterate through the order and print each item, does the `DessertItem` class (or its subclasses) have a method to define how the name should be displayed?

**Next step:** Review the `DessertItem` class and consider how the `__str__` method might affect the printed output.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft pointed to __str__, which is the wrong direction for DS2. The print in main's loop is the bug; the hint now sends the student to run main and compare.

> v8 revision: removed the literal item name and exact line pointer; trimmed to one sentence per field

status: accepted

```json
{
  "summary": "Your class hierarchy and Order class work, but the receipt in main does not show the item names.",
  "items": [
    {
      "test_key": "main_output",
      "what_went_wrong": "The printed output is missing the names of the items in the order.",
      "hint": "If you run dessertshop.py yourself, what does the loop in main print for each item?"
    }
  ],
  "next_step": "Review the loop in main in dessertshop.py."
}
```
