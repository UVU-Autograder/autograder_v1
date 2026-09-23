"""Autograding test suite for Lab 2: Bank Account Class."""

import contextlib
import io

import pytest
from python_autograder_helpers import import_student_modules


@pytest.mark.ag_account_init
def test_account_init() -> None:
    """Verify Account initialization with default and custom arguments."""
    (account_mod,) = import_student_modules("account")
    Account = account_mod.Account

    default_acc = Account()
    assert getattr(default_acc, "owner", None) == ""
    assert float(getattr(default_acc, "balance", -1)) == pytest.approx(0.0)

    custom_acc = Account("Alice", 100.0)
    assert getattr(custom_acc, "owner", None) == "Alice"
    assert float(getattr(custom_acc, "balance", -1)) == pytest.approx(100.0)


@pytest.mark.ag_account_str
def test_account_str() -> None:
    """Verify Account __str__ formatting."""
    (account_mod,) = import_student_modules("account")
    Account = account_mod.Account

    acc = Account("Alice", 100.0)
    output = str(acc)
    assert "Owner: Alice, Balance: $100.00" in output, (
        f"Expected 'Owner: Alice, Balance: $100.00', got {output!r}"
    )

    acc2 = Account("Bob", 50.5)
    output2 = str(acc2)
    assert "Owner: Bob, Balance: $50.50" in output2, (
        f"Expected 'Owner: Bob, Balance: $50.50', got {output2!r}"
    )


@pytest.mark.ag_demo_output
def test_demo_output() -> None:
    """Verify demo.py executes and produces expected stdout output."""
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        (demo_mod,) = import_student_modules("demo")
        if hasattr(demo_mod, "main"):
            demo_mod.main()

    stdout = f.getvalue()
    assert "Owner:" in stdout and "Balance:" in stdout, (
        "demo.py output missing expected Account print statements"
    )
