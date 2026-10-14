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
- ``all_pass_problems``: feedback on a submission that passes everything but
  still reads like a bug report ("but Sundae's packaging is overwritten",
  "Review the Order.__iter__ method"). p3 learned this from all-pass targets
  whose extension ideas were phrased as instructions to re-check working code.

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
_ATTR_RE = re.compile(r"\b[A-Za-z_]\w*\.([A-Za-z_]\w*)(?!\s*\()")
_DEF_RE = re.compile(r"\bdef\s+\w+\s*\((.*?)\)")
_SUPER_INIT_RE = re.compile(r"\bsuper\(\)\.__init__\((.*?)\)")
_PARAM_RE = re.compile(r"(?:^|,)\s*\*{0,2}([A-Za-z_]\w*)")
# File extensions look like attributes to _ATTR_RE ("dessert.py") but name nothing to change.
_IGNORED_NAMES = {"self", "cls", "args", "kwargs", "py", "md", "txt", "json", "jpg", "png"}
# All-pass feedback: the summary must not hedge or report a defect, and the next
# step must be an optional extension, not an instruction to re-check the code.
_DEFECT_WORDS = r"problem|issue|bug|wrong|incorrect|broken|overwrit\w*|fix\w*|mistake"
_ALL_PASS_SUMMARY_RE = re.compile(rf"\b(?:but|however|although|though|missing|error|fails?|failing|{_DEFECT_WORDS})\b", re.I)
_ALL_PASS_NEXT_RE = re.compile(rf"\b(?:{_DEFECT_WORDS})\b", re.I)
_RECHECK_START_RE = re.compile(r"^\s*(?:review|check|trace|fix|look at|make sure|verify|debug|correct|re-?read)\b", re.I)
# "Every test passes", "Congratulations": the student can tell the code works.
_AFFIRM_RE = re.compile(r"\b(?:pass(?:es|ed)?|congratulations|great job|well done|nice work|all (?:the )?(?:tests|requirements))\b", re.I)
# Wording that suspects working code: "to see how it handles multiple passes", "to see if they match".
_SUSPECT_RE = re.compile(
    r"\b(?:to see (?:if|whether)|to see how (?:it|they) handles?|whether (?:it|they) (?:handles?|works?|match(?:es)?)"
    r"|make sure|double-check|is (?:it|this) (?:correct|right))\b",
    re.I,
)
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
        unquoted = _QUOTED_RE.sub(" ", line)
        names.update(_ATTR_RE.findall(unquoted))
        for params in _DEF_RE.findall(unquoted):
            names.update(_PARAM_RE.findall(params))
        for args in _SUPER_INIT_RE.findall(unquoted):
            names.update(_PARAM_RE.findall(args))
    return {name for name in names if name not in _IGNORED_NAMES and len(name) > 1}


def pinpointed_identifiers(text: str, bug_diff: str) -> list[str]:
    """Changed-line attributes/parameters named in ``text`` (pass item prose and next step).

    A plain word like ``order`` or ``weight`` only counts when written as code
    (``self.order``, ``.order``, in backticks, or in quotes); names with an
    underscore or a capital always count.
    """
    found = []
    for name in changed_identifiers(bug_diff):
        if "_" in name or not name.islower():
            pattern = rf"(?<!\w){re.escape(name)}(?!\w)"
        else:
            pattern = rf"""(?:\.{re.escape(name)}(?!\w)|[`'"]{re.escape(name)}[`'"])"""
        if re.search(pattern, text):
            found.append(name)
    return sorted(found)


def all_pass_problems(summary: str, next_step: str) -> list[str]:
    """Why feedback on an all-pass submission reads like a bug report (empty when it does not)."""
    problems = []
    hedge = _ALL_PASS_SUMMARY_RE.search(summary)
    if hedge:
        problems.append(f"summary hedges or reports a defect ({hedge.group(0)!r}) though every test passes")
    defect = _ALL_PASS_NEXT_RE.search(next_step)
    if defect:
        problems.append(f"next_step talks about a defect ({defect.group(0)!r}) though every test passes")
    if _SUSPECT_RE.search(next_step):
        problems.append("next_step suspects working code; suggest an optional extension instead")
    elif _RECHECK_START_RE.match(next_step) and not _AFFIRM_RE.search(summary):
        problems.append("summary never says the tests pass and next_step sends the student back into the code")
    return problems


def word_count(prose: str) -> int:
    return len(prose.split())
