# v8 target review

72 targets were rewritten to the new rules. Each has a `> v8 revision (Claude):` note; review them the usual way.

**New rules:**
- Don't repeat the student's or the expected value. The UI already shows both.
- Hints name the method or class to look at, never the attribute, parameter or default to change.
- Stay under 80 words.

**Example:** "A new Candy has tax_percent 8.25; the test expects 7.25" became "A new Candy's tax rate is higher than the test expects."

**Worth a second look** (the most direct hints left): `lab7_no_dataclass`, `ds4_icecream_cost_missing`, `lab5_str_space_pad`.

## p3b changes

63 targets changed; each has a `> p3b (Claude):` note.
- **11 all-pass targets:** praise first, and the next step is an optional extension ("Optional: …"), so students with working code aren't sent back to re-check it.
- **52 targets trimmed to 65 words or fewer**, because the model writes about 10 words more than its targets. Next steps are under 15 words.

## p4 changes

43 targets trimmed; each has a `> p4 (Claude):` note. p3b still ran long (15-17-word next steps, 87-106 words on 3-item cascades).
- **26 all-pass/concept targets:** next step 10 words or fewer.
- **17 three-item targets:** 55 words or fewer; follow-on items say "Same cause." or "Fix X first."
- **34 new cases** (`p4_*`, not drafted yet): 23 injection attempts the feedback must ignore, and 11 arithmetic/rounding bugs where the test message points at the wrong thing.
