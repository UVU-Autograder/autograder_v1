<!-- p2-review | case=p2_ds2_two_bugs | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_two_bugs

**Dessert Shop 2: Using Classes in main** · `cascading_failure` · two bugs, only one caught: main prints objects (main_output); the Candy price regression is not tested, so feedback must not mention it

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -8,5 +8,5 @@
         super().__init__(name)
         self.candy_weight = candy_weight
-        self.price_per_pound = price_per_pound
+        self.price_per_pound = candy_weight
 
 
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -12,5 +12,5 @@
 
     for item in order:
-        print(item.name)
+        print(item)
 
     print("Total number of items in order:", len(order))
```

## What the grader reported

- `main_output` (dessertshop.py main() constructs Order items and prints formatted receipt): `E    +  where False = any(<generator object test_main_output.<locals>.<genexpr> at 0x1044a6180>)`
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae), Order class defines order list, add() method, and len() support

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy and Order class logic are working correctly, but the final output is missing a specific item.

**dessertshop.py main() constructs Order items and prints formatted receipt**: The printed output does not contain the 'candy corn' item.
- 💡 When you iterate through the order and print each item, does the `DessertItem` class (or its subclasses) have a method that defines how the name should be displayed?

**Next step:** Review the `DessertItem` class and its subclasses to see how the `print()` function interacts with them.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft pointed to __str__. The reported failure is main printing objects; the untested Candy price bug is correctly not mentioned.

> Stale after 4159d52 (tightened tests): the grader now reports different failing items: ds1_regression, main_output. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your Order class works, but the receipt main prints is missing the dessert names.",
  "items": [
    {
      "test_key": "main_output",
      "what_went_wrong": "The output does not contain 'candy corn', so the loop is not printing item names.",
      "hint": "Double check your code: run dessertshop.py and look at what the print in the for loop shows for each item. What would you need to print to see the name?"
    }
  ],
  "next_step": "Review the print statement inside main's for loop."
}
```
