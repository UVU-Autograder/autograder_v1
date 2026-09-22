<!-- p2-review | case=p2_ds1_icecream_no_parent | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_icecream_no_parent

**Dessert Shop 1: Inheritance Superclass** · `cascading_failure` · IceCream does not inherit DessertItem, so super().__init__(name) goes to object

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -18,5 +18,5 @@
 
 
-class IceCream(DessertItem):
+class IceCream:
     def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0):
         super().__init__(name)
```

## What the grader reported

- `icecream` (IceCream inherits DessertItem and defines scoop_count & price_per_scoop): `E    +  where False = issubclass(IceCream, DessertItem)`
- `sundae` (Sundae inherits IceCream and defines topping_name & topping_price): `E   TypeError: object.__init__() takes exactly one argument (the instance to initialize)`
- Passing: DessertItem base class defines name attribute with default '', Candy inherits DessertItem and defines candy_weight & price_per_pound, Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your base classes and the Candy and Cookie subclasses are correctly implemented. However, there are issues with the inheritance structure for IceCream and Sundae.

**IceCream inherits DessertItem and defines scoop_count & price_per_scoop**: The IceCream class is not recognized as a subclass of DessertItem.
- 💡 How is the IceCream class defined in relation to the DessertItem class?

**Sundae inherits IceCream and defines topping_name & topping_price**: The initialization of the Sundae class is causing a TypeError because it is trying to call an initializer on a base class that doesn't support those arguments.
- 💡 If IceCream does not inherit from DessertItem, what happens when Sundae tries to call super().__init__()?

**Next step:** Review the class definition for IceCream to ensure it correctly inherits from DessertItem.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `icecream`, `sundae`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): next_step stated the fix ('ensure it inherits from DessertItem'), and fixed the typo 'inhertiance'. The Sundae item now says it follows from IceCream.

status: todo

```json
{
  "summary": "Your base class and the Candy and Cookie subclasses are correctly implemented. However, there are issues with the inheritance structure for IceCream and Sundae.",
  "items": [
    {
      "test_key": "icecream",
      "what_went_wrong": "The IceCream class is not recognized as a subclass of DessertItem.",
      "hint": "Can you reevaluate the inheritance structure for the IceCream class? Compare its class line with Candy's."
    },
    {
      "test_key": "sundae",
      "what_went_wrong": "Creating a Sundae fails with a TypeError about object.__init__, because of where IceCream's super() call ends up.",
      "hint": "This follows from the IceCream problem. If IceCream does not inherit from DessertItem, where does its super().__init__() call go?"
    }
  ],
  "next_step": "Compare the class line for IceCream with the class lines for Candy and Cookie."
}
```
