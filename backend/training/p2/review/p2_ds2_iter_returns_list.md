<!-- p2-review | case=p2_ds2_iter_returns_list | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_iter_returns_list

**Dessert Shop 2: Using Classes in main** · `cascading_failure` · __iter__ returns the list instead of the iterator (TypeError: iter() returned non-iterator)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -45,5 +45,5 @@
     def __iter__(self) -> "Order":
         self._index = 0
-        return self
+        return self.order
 
     def __next__(self) -> DessertItem:
```

## What the grader reported

- `order_class` (Order class defines order list, add() method, and len() support): `E   TypeError: iter() returned non-iterator of type 'list'`
- `main_output` (dessertshop.py main() constructs Order items and prints formatted receipt): `E   AssertionError: dessertshop.py execution failed: iter() returned non-iterator of type 'list'`
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae)

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy is correctly implemented, but there is an issue with how the Order class handles iteration.

**Order class defines order list, add() method, and len() support**: The __iter__ method is returning a list instead of an iterator.
- 💡 When implementing the iterator protocol, what should __iter__ return so that the object itself can be used in a for-loop?

**dessertshop.py main() constructs Order items and prints formatted receipt**: The main function fails because the Order object is not behaving as a proper iterator.
- 💡 How does the error in the Order class's iteration logic affect the for-loop in main?

**Next step:** Review the requirements for the iterator protocol in the Order class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_class`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the answer ('the object itself'). Now points to which object has a __next__.

status: accepted

```json
{
  "summary": "Your class hierarchy is correctly implemented, but there is an issue with how the Order class handles iteration.",
  "items": [
    {
      "test_key": "order_class",
      "what_went_wrong": "Looping over an Order fails with \"iter() returned non-iterator of type 'list'\".",
      "hint": "Python calls __iter__, then calls __next__ on whatever it returned. Which object in your class has the __next__ method?"
    },
    {
      "test_key": "main_output",
      "what_went_wrong": "main fails at its for loop for the same reason.",
      "hint": "This follows from the __iter__ problem. Fix that first."
    }
  ],
  "next_step": "Review the __iter__ method in the Order class."
}
```
