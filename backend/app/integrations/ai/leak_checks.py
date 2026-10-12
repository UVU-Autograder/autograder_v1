"""Text checks for feedback that gives the answer away without writing code.

``guardrails`` catches code-shaped leaks (solution blocks, score talk). These
catch the quieter kind found in prompt-v7 era feedback, e.g.

    "A new IceCream with no scoop_count has 0.5 scoops; the test expects 0."
    "What is the default value for scoop_count in your IceCream init?"

- ``echoed_values``: a literal from the failing test (the student's value or the
  expected one) repeated in the feedback. The sandbox UI already shows both, so
  repeating them only adds words, and next to a pointed hint it is the answer.
- ``answer_literals``: a literal that exists only in the model solution's side
  of the diff -- the exact thing to type. Needs the case's ``bug_diff``, so it
  works in eval and dataset building, not at serving time.
- ``pinpointed_identifiers``: an attribute or parameter from the changed lines
  named in a hint or next step ("the default value for scoop_count").

Literals are numbers and quoted strings taken from pytest's assertion lines and
from numeric student/expected values; numbers compare by value (0.5 == 0.50).
Pure functions, no I/O: the dataset gate, the eval and (later) the runtime
guardrail share them.
"""

from __future__ import annotations

import re
from typing import Any

# A number that is not part of an identifier, a hex address, or an exponent.
_NUMBER_RE = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w])")
_QUOTED_RE = re.compile(r"""'([^'\n]{2,80})'|"([^"\n]{2,80})\"""")
# pytest lines that carry the compared values.
_VALUE_LINE_RE = re.compile(r"^E\s+(?:.*\bassert\b|.*AssertionError|\+\s+where\b|Obtained:|Expected:)")
_APPROX_TAIL_RE = re.compile(r"\s*±.*$")
_SELF_ATTR_RE = re.compile(r"\bself\.(\w+)")
_DEF_RE = re.compile(r"\bdef\s+\w+\s*\((.*?)\)")
_PARAM_RE = re.compile(r"(?:^|,)\s*\*{0,2}([A-Za-z_]\w*)")
_IGNORED_NAMES = {"self", "cls", "args", "kwargs"}
# Quoted strings in these positions are names (methods, attributes, imports), not values.
_NAME_POSITION_RE = re.compile(
    r"""(?:hasattr|getattr|setattr)\([^,()]*,\s*['"]\w+['"]"""
    r"""|(?:attribute|name|module|import)\s+['"]\w+['"]"""
)
_IGNORED_STRINGS = {"True", "False", "None"}


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def _literals(text: str) -> tuple[set[float], set[str]]:
    """Numbers and quoted strings in a line of code or test output."""
    text = _NAME_POSITION_RE.sub(" ", text)
    strings = {a or b for a, b in _QUOTED_RE.findall(text)} - _IGNORED_STRINGS
    without_strings = _QUOTED_RE.sub(" ", text)
    numbers = {n for n in (_number(m) for m in _NUMBER_RE.findall(without_strings)) if n is not None}
    return numbers, {s for s in strings if any(ch.isalnum() for ch in s)}


def value_literals(failures: list[dict[str, Any]]) -> tuple[set[float], set[str]]:
    """The literals a student already sees for these failures."""
    numbers: set[float] = set()
    strings: set[str] = set()
    label_numbers: set[float] = set()
    labels = shown_labels(failures)
    for failure in failures:
        for line in str(failure.get("message") or "").splitlines():
            if _VALUE_LINE_RE.match(line):
                line_numbers, line_strings = _literals(_APPROX_TAIL_RE.sub("", line))
                numbers |= line_numbers
                strings |= line_strings
        for key in ("your_value", "expected_value"):
            value = failure.get(key)
            if value is not None:
                number = _number(_APPROX_TAIL_RE.sub("", str(value)).strip())
                if number is not None:
                    numbers.add(number)
        label_numbers |= _literals(str(failure.get("label") or ""))[0]
    # A test's label is shown as its title, so anything in it is fair to mention.
    return numbers - label_numbers, {text for text in strings if text not in labels}


def shown_labels(failures: list[dict[str, Any]]) -> str:
    """Test titles the student sees next to the feedback."""
    return "\n".join(f"{failure.get('key', '')} {failure.get('label', '')}" for failure in failures)


def _found(prose: str, numbers: set[float], strings: set[str]) -> list[str]:
    hits = [m for m in _NUMBER_RE.findall(prose) if _number(m) in numbers]
    for text in strings:
        pattern = re.escape(text)
        if text[0].isalnum():
            pattern = r"(?<!\w)" + pattern
        if text[-1].isalnum():
            pattern += r"(?!\w)"
        if re.search(pattern, prose):
            hits.append(text)
    return sorted(set(hits))


def echoed_values(prose: str, failures: list[dict[str, Any]]) -> list[str]:
    """Literals from the failing tests that the feedback repeats."""
    return _found(prose, *value_literals(failures))


def _diff_sides(bug_diff: str) -> tuple[list[str], list[str]]:
    lines = bug_diff.splitlines()
    removed = [line[1:] for line in lines if line.startswith("-") and not line.startswith("---")]
    added = [line[1:] for line in lines if line.startswith("+") and not line.startswith("+++")]
    return removed, added


def answer_literals(prose: str, bug_diff: str, shown: str = "") -> list[str]:
    """Literals only the model solution's lines contain (diff is model -> student), found in the feedback.

    ``shown`` is text the student already sees (test labels); names in it, like a
    Protocol written as a quoted type hint, are not answers.
    """
    removed, added = _diff_sides(bug_diff)
    _, solution_strings = _literals("\n".join(removed))
    _, student_strings = _literals("\n".join(added))
    strings = {text for text in solution_strings - student_strings if text not in shown}
    # Numbers are compared as written here, so a solution's 0 is not cancelled by an unrelated 0.0.
    numbers = _number_tokens("\n".join(removed)) - _number_tokens("\n".join(added))
    return _found(prose, {float(n) for n in numbers}, strings)


def _number_tokens(code: str) -> set[str]:
    return set(_NUMBER_RE.findall(_QUOTED_RE.sub(" ", _NAME_POSITION_RE.sub(" ", code))))


def changed_identifiers(bug_diff: str) -> set[str]:
    """Attributes and parameters on the changed lines of the diff."""
    names: set[str] = set()
    for line in sum(_diff_sides(bug_diff), []):
        names.update(_SELF_ATTR_RE.findall(line))
        for params in _DEF_RE.findall(line):
            names.update(_PARAM_RE.findall(params))
    return {name for name in names if name not in _IGNORED_NAMES and len(name) > 1}


def pinpointed_identifiers(text: str, bug_diff: str) -> list[str]:
    """Changed-line attributes/parameters named in ``text`` (pass the hints and next step).

    A plain word like ``order`` or ``weight`` only counts when written as code
    (``self.order``, ``.order``, or in backticks); names with an underscore or a
    capital always count.
    """
    found = []
    for name in changed_identifiers(bug_diff):
        if "_" in name.strip("_") or not name.islower():
            pattern = rf"(?<!\w){re.escape(name)}(?!\w)"
        else:
            pattern = rf"(?:\.{re.escape(name)}(?!\w)|`{re.escape(name)}`)"
        if re.search(pattern, text):
            found.append(name)
    return sorted(found)


def word_count(prose: str) -> int:
    return len(prose.split())
