import importlib

import pytest

student_functions = importlib.import_module("student_functions")


@pytest.mark.ag_add_numbers
def test_add_numbers_positive_values():
    assert student_functions.add_numbers(2, 3) == 5


@pytest.mark.ag_add_numbers
def test_add_numbers_negative_values():
    assert student_functions.add_numbers(-4, 9) == 5


@pytest.mark.ag_reverse_words
def test_reverse_words_basic_sentence():
    assert student_functions.reverse_words("hello world") == "olleh dlrow"


@pytest.mark.ag_reverse_words
def test_reverse_words_preserves_spacing_between_words():
    assert student_functions.reverse_words("python is fun") == "nohtyp si nuf"


@pytest.mark.ag_count_vowels
def test_count_vowels_lowercase():
    assert student_functions.count_vowels("education") == 5


@pytest.mark.ag_count_vowels
def test_count_vowels_case_insensitive():
    assert student_functions.count_vowels("AutoGrader") == 5
