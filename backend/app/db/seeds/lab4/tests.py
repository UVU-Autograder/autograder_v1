"""Autograding test suite for Lab 4: Properties and Validation."""

import pytest
from python_autograder_helpers import import_student_modules


@pytest.mark.ag_title_property
def test_title_property() -> None:
    """Verify title property validation raising TypeError and ValueError."""
    (book_mod,) = import_student_modules("book")
    Book = book_mod.Book

    b = Book("The Hobbit", "J.R.R. Tolkien")
    assert b.title == "The Hobbit"

    b.title = "1984"
    assert b.title == "1984"

    with pytest.raises(TypeError):
        b.title = 123  # type: ignore

    with pytest.raises(ValueError):
        b.title = ""


@pytest.mark.ag_author_property
def test_author_property() -> None:
    """Verify author property validation raising TypeError and ValueError."""
    (book_mod,) = import_student_modules("book")
    Book = book_mod.Book

    b = Book("Dune", "Frank Herbert")
    assert b.author == "Frank Herbert"

    b.author = "F. Herbert"
    assert b.author == "F. Herbert"

    with pytest.raises(TypeError):
        b.author = ["Frank"]  # type: ignore

    with pytest.raises(ValueError):
        b.author = ""


@pytest.mark.ag_description_readonly
def test_description_readonly() -> None:
    """Verify description read-only property formatting and immutability."""
    (book_mod,) = import_student_modules("book")
    Book = book_mod.Book

    b = Book("Harry Potter", "J.K. Rowling")
    desc = b.description
    assert "Harry Potter" in desc and "J.K. Rowling" in desc and ("written by" in desc or "was written" in desc)

    with pytest.raises(AttributeError):
        b.description = "New Description"  # type: ignore
