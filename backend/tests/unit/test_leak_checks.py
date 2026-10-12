from app.integrations.ai.leak_checks import (
    answer_literals,
    changed_identifiers,
    echoed_values,
    pinpointed_identifiers,
    shown_labels,
    word_count,
)

ICECREAM_FAILURE = {
    "key": "icecream",
    "label": "IceCream inherits DessertItem and defines scoop_count & price_per_scoop",
    "message": (
        "tests.py:40: in test_icecream\n"
        '    assert ic.scoop_count == 0, "Default scoop_count must be 0"\n'
        "E   AssertionError: Default scoop_count must be 0\n"
        "E   assert 0.5 == 0\n"
        "E    +  where 0.5 = <dessert.IceCream object at 0x000001F1C2CF86E0>.scoop_count\n"
    ),
    "your_value": "ic.scoop_count",
    "expected_value": '0, "Default scoop_count must be 0',
}
ICECREAM_DIFF = (
    "--- model/dessert.py\n+++ student/dessert.py\n@@ -20,3 +20,3 @@\n"
    "-    def __init__(self, name: str = \"\", scoop_count: int = 0, price_per_scoop: float = 0.0):\n"
    "+    def __init__(self, name: str = \"\", scoop_count: float = 0.5, price_per_scoop: float = 0.0):\n"
)
CASH_FAILURE = {
    "key": "order_payable",
    "label": "Order implements PayType and the Payable protocol",
    "message": "E   AssertionError: assert 'cash' == 'CASH'\nE     - CASH\nE     + cash",
    "your_value": "order.get_pay_type()",
    "expected_value": "CASH",
}
CASH_DIFF = (
    "--- model/dessert.py\n+++ student/dessert.py\n"
    '-        self._pay_type: PayType = "CASH"\n'
    '+        self._pay_type: PayType = "cash"\n'
)


def test_the_reported_icecream_feedback_is_caught():
    prose = (
        "A new IceCream with no scoop_count has 0.5 scoops; the test expects 0.\n"
        "What is the default value for scoop_count in your IceCream init?"
    )
    assert echoed_values(prose, [ICECREAM_FAILURE]) == ["0", "0.5"]
    assert pinpointed_identifiers("What is the default value for scoop_count in your IceCream init?", ICECREAM_DIFF) == [
        "scoop_count"
    ]


def test_describing_the_difference_in_words_passes():
    prose = (
        "A new IceCream starts with a different number of scoops than the test expects.\n"
        "When you create an IceCream without arguments, where does its starting scoop count come from?"
    )
    assert echoed_values(prose, [ICECREAM_FAILURE]) == []
    assert answer_literals(prose, ICECREAM_DIFF) == []
    assert pinpointed_identifiers(prose, ICECREAM_DIFF) == []


def test_numbers_compare_by_value_and_by_whole_token():
    assert echoed_values("It reports 0.50 scoops.", [ICECREAM_FAILURE]) == ["0.50"]
    assert echoed_values("After 10 tries and 2.05 seconds", [ICECREAM_FAILURE]) == []


def test_numbers_in_the_test_label_are_allowed():
    failure = {"key": "k", "label": "main prints at least 7 lines", "message": "E   assert 2 >= 7"}
    assert echoed_values("The output should have at least 7 lines.", [failure]) == []
    assert echoed_values("It printed 2 lines.", [failure]) == ["2"]


def test_quoted_values_are_case_sensitive_and_names_are_not_values():
    assert echoed_values("Your default pay type is lowercase 'cash'.", [CASH_FAILURE]) == ["cash"]
    assert echoed_values("Check how get_pay_type reports the default.", [CASH_FAILURE]) == []
    name_check = {
        "key": "proto",
        "label": "Combinable protocol",
        "message": "E    +  where False = hasattr(<class 'combine.Combinable'>, 'combine')\nE   AttributeError: 'Candy' object has no attribute 'candy_weight'",
    }
    assert echoed_values("The protocol has no combine method; candy_weight is missing.", [name_check]) == []


def test_answer_literal_is_what_only_the_model_solution_has():
    assert answer_literals("Payment types are written in upper case like CASH.", CASH_DIFF) == ["CASH"]
    assert answer_literals("Your default is cash.", CASH_DIFF) == []
    assert answer_literals("Scoops should start at 0.", ICECREAM_DIFF) == ["0"]
    protocol_diff = '-    def combine(self, other: "Combinable") -> "Combinable": ...\n'
    assert answer_literals("Compare Combinable with Candy.", protocol_diff, shown="Combinable protocol") == []


def test_plain_words_only_count_as_identifiers_when_written_as_code():
    diff = "-        self.order.append(item)\n+        self.order = [item]\n"
    assert changed_identifiers(diff) == {"order"}
    assert pinpointed_identifiers("What happens to the items already in your order?", diff) == []
    assert pinpointed_identifiers("What happens to self.order when you add?", diff) == ["order"]
    assert pinpointed_identifiers("What does `order` hold?", diff) == ["order"]


def test_parameters_and_private_attributes_are_identifiers():
    assert changed_identifiers(ICECREAM_DIFF) == {"name", "scoop_count", "price_per_scoop"}
    assert pinpointed_identifiers("Check the initial value of _pay_type.", CASH_DIFF) == ["_pay_type"]


def test_shown_labels_and_word_count():
    assert "scoop_count" in shown_labels([ICECREAM_FAILURE])
    assert word_count("one two  three\nfour") == 4
