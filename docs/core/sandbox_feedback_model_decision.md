# Decision record: sandbox feedback model

| | |
| --- | --- |
| **Decision** | Serve Gemma 4 12B with the reviewed LoRA adapter **`cs1410-p2c`** for sandbox AI feedback |
| **Status** | Proposed, 2026-09-24. Technically selected; waiting on the staff spot-check and the institutional live-use gate (below) |
| **Owners** | Model and data: Easton. Deployment: Jaxon. Feedback quality sign-off: CS 1410 instructors. Live use: UVU approval |
| **Scope** | Sandbox feedback only. Official runs stay without AI ([decisions.md](decisions.md)) |

## Summary

When a student runs code in the sandbox, the autograder grades it and a local
language model explains the result: what failed, a hint toward where to look,
and one next step. The model never grades and never sees anything that
identifies the student.

We fine-tuned the base model (Gemma 4 12B) on 146 reviewed examples and
compared four versions on a fixed set of 57 test cases. The chosen version,
**p2c**, gives hints that point students toward the problem instead of handing
them the fix, and its diagnoses are as accurate as the untuned model's. Every
earlier version traded one for the other. It runs on the Dell workstation as a
background service that only the autograder can reach.

Students should not see it until the instructors have spot-checked its feedback
and UVU has approved local AI for live use.

## Context

- **What the model does.** `backend/app/integrations/ai/prompts.py` (prompt v5)
  gives it the grader's failing tests, the assignment's automated checks, any
  concept warnings, and the student's code. It answers in a fixed JSON shape. The
  sandbox checks every response before display (`guardrails.validate_feedback`):
  it may only mention tests the grader reported failing, may not state a score,
  and may not write the solution as code. A response that fails the check is
  replaced by a standard "feedback unavailable" message.
- **Constraints.** Inference stays on university-managed hardware (the Dell,
  RTX PRO 4500, 32 GB). Only code reaches the model, and only when it is not
  personally traceable ([ferpa_analysis.md](ferpa_analysis.md)). No student
  data is used for training or evaluation: every example is a deliberately
  broken copy of an instructor's model solution.
- **Why fine-tune at all.** Prompt revisions (v2 through v5) fixed most
  problems with the untuned model. One remained that wording could not fix:
  in about 17 of 47 failing test cases its hints gave the answer away, for
  example "How can you use default values in `Candy.__init__`...?" The course's
  policy is that feedback points to *where to look*, never *what to write*.

## Options compared

All versions share the base model, prompt v5 and the server settings. The
eval set is 57 frozen synthetic cases over 13 assignments, held out from
training (`backend/eval/`).

| Version | What changed | Result |
| --- | --- | --- |
| Stock Gemma 4 12B | no fine-tuning | Accurate diagnoses; gives the answer away in ~17 of 47 failing cases |
| p2 | first adapter: 113 examples, compact JSON targets | Broke its JSON in 5 of 57 responses; invented problems on correct code in 3 of 6 all-pass cases |
| p2b | targets in the model's own JSON style, +8 all-pass examples, 3 passes (100 steps) | JSON fixed; best hints; but the same four wrong diagnoses in all 3 runs (for example "write more tests" when the tests existed but were misnamed) |
| **p2c** | same data as p2b, 2 passes (66 steps) | **Chosen.** Hints as good as p2b; diagnoses as good as stock |

Not pursued: hosted APIs (student code would leave UVU), "uncensored"
community variants of Gemma (they remove refusal behavior, which is the wrong
direction for student-facing text), and larger models (the 12B model met the
bar and leaves room on the card for about 9 concurrent full-length requests).

## Evidence

Seven eval runs: stock twice, p2b three times (one with the sandbox's
JSON-enforcing "guided" mode), p2c twice (unguided and guided).

| | Stock (2 runs) | p2b (3 runs) | **p2c (2 runs)** |
| --- | --- | --- | --- |
| Automatic checks passed | 100%, 100% | 100% in all 3 | **100%, 100%** |
| Wrong on the 4 cases p2b got wrong | 0 of 4 (one run's next step names a method that does not exist) | 3 to 4 of 4 in every run | **0 of 4 in both runs** |
| Invented problems on correct code (6 all-pass cases per run) | 0 | 1 in one run | **0 in 12 samples** |
| Hints that give the answer away (47 failing cases) | ~17 | ~3 | **~3** |
| Mean response time, guided (one request at a time) | n/a | 2.1 s | **2.1 s** |
| Mean response length | ~620 chars | ~520 chars | **~500 chars** |

How to read this:

- **The automatic checks are safety gates, not quality.** They cannot tell a
  right diagnosis from a wrong one, so every response in every run was read and
  compared against the grader output, and disputed claims were checked against
  the code in the case (for example, whether a test value the model quoted was
  actually in the input). That read was done while developing the adapter;
  it is not yet an independent staff assessment.
- **Single runs are noisy.** The same model's two runs matched word for word on
  only 2 of 57 cases. The p2b/p2c difference is trusted because each model's
  behavior on those cases repeated in every one of its runs.
- **One bug, three versions** (`normalize` misses exactly 100 cents because it
  checks `> 100`). Stock tells the fix: "should it handle values equal to 100 as
  well as those greater than 100?" p2b invents an input that appears nowhere in
  the test: "Can you work out how many dollars 125 cents should give...?" p2c:
  "What happens when cents is exactly 100? Can you trace normalize with that
  value?"

## Training data

- **146 examples**, 133 for training and 13 held out: realistic single bugs,
  cascades of failures from one cause, two independent bugs, empty submissions,
  prompt-injection attempts, concept-rule warnings, and 19 correct submissions
  (11 alternative solutions, 8 plain). Built by `python -m eval.build_cases
  --split train` from `eval/mutations.py`, graded by the real autograder.
- **Targets** were drafted by the untuned model, edited to the course's
  feedback checklist, then reviewed: 123 approved by CS 1410 professors and IAs;
  14 targets revised after the test suites were tightened (commit 4159d52),
  reviewed by Easton with 5 wording edits; 9 added afterwards (8 plain all-pass
  cases and one concept case) accepted by Easton as drafted. The review files are
  versioned in `backend/training/p2/review/`, with who accepted what in the
  commit history.
- **Training run (p2c):** QLoRA rank 16 on 328 language-model projections,
  66 steps, 18.5 minutes on the Dell, peak GPU memory 14.3 GiB, held-out loss
  0.672 -> 0.597 -> 0.574. The run's settings travel with the adapter
  (`training_summary.json`); the commit and weights checksum are recorded in its
  `PROVENANCE.json` when it is promoted.

## Deployment

`backend/training/install_vllm_service.sh p2c` installs `vllm-cs1410.service`
on the Dell (details and operations in `backend/training/README.md`):

- listens on **127.0.0.1:8001 only**; the autograder's containers use host
  networking and reach it on loopback, nothing on the campus network can;
- runs offline with vLLM's usage telemetry turned off;
- serves the promoted copy of the adapter (`/data/models/adapters/cs1410-p2c`),
  so retraining cannot change what is live, and keeps the replaced adapter for
  rollback;
- starts at boot and restarts on failure;
- serves the untuned model on the same server as `gemma4-12b-qat`.

The autograder uses it with `LOCAL_LLM_ENDPOINT=http://127.0.0.1:8001/v1` and
`LOCAL_LLM_MODEL=cs1410-p2c`. The sandbox already requests JSON-enforced
("guided") output, the configuration measured above.

**Rollback:** set `LOCAL_LLM_MODEL=gemma4-12b-qat` (untuned model, no
restart of the model server), or stop the service, in which case students get the
standard "feedback unavailable" message and grading is unaffected.

## Known limitations

- **Small wording slips remain.** In both p2c runs one summary said equality
  "fails for two different amounts" when it failed for two objects with the
  same amount; one response said "your own tests pass" and then that one failed.
  None of the p2c responses we read sent a student toward a wrong fix, but a
  few sentences are imprecise.
- **Three assignments are untested.** DS6, DS7 and Lab 6 (pygame) are not in the
  eval set or the training data. Their feedback quality is unknown.
- **Long prompts are untested.** Every training example fit in 8,192 tokens
  (the longest is about 7,000). The server accepts up to 12,288 because prompt
  v5 does not cap failure messages; behavior on longer prompts has not been
  measured.
- **The adapter is tied to prompt v5.** Any change to the prompt text needs a new
  eval run, and a material change needs retraining.
- **The eval set is synthetic and small.** It measures behavior on known bug
  patterns, not on the variety of real student code.

## Before students see it

| Step | Owner | Status |
| --- | --- | --- |
| Instructors or IAs spot-check about 20 cases in the p2c review sheet (`backend/eval/results/p2c-v5-review.md`, each case next to stock, with Accurate / Helpful / Tone columns) and record sign-off | CS 1410 staff | Open |
| Install the service on the Dell and confirm it serves `cs1410-p2c` | Easton | Ready to run |
| Point the stack at it (`LOCAL_LLM_ENDPOINT`, `LOCAL_LLM_MODEL`) and check sandbox AI feedback end to end | Jaxon | Open |
| Cap failure-message length in the prompt (keep each message's start and end), bump the prompt version, re-run the eval | Jaxon / Easton | Open |
| Decide AI feedback for DS6, DS7 and Lab 6: evaluate first, or leave it off for them | Instructors / Easton | Open |
| UVU Software Approval with an approved local-AI scope, and pilot release sign-off ([backlog](../planning/backlog.md) P0 "Institutional Live-Use Gate") | UVU / project leads | Open |

## Revisit when

- the prompt changes (retrain against the new version, then re-run this comparison);
- the staff spot-check finds inaccurate or unhelpful feedback;
- the guardrails reject more than a few percent of live responses;
- assignments are added or the pygame assignments come into scope;
- a new base model is considered.
