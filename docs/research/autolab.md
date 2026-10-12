# Autolab: an execution service and deliberate grading workflows

Inspected 2026-10-06 from a shallow clone of [autolab/Autolab](https://github.com/autolab/Autolab), commit `674efe9deac197e108a426c873beb7c5f912b25f` (commit timestamp 2025-10-21). The Rails application, its Tango client, bundled Tango documentation and relevant tests were inspected. Tango is a separate repository and was not cloned or run; its isolation/lifecycle implementation is not independently verified here. The Autolab clone was removed before cloning Otter-Grader. [Comparison and integration proposal](autograding-platforms.md).

## What the architecture teaches

Autolab combines assessment administration, student submissions, gradebooks, automatic grading and staff annotation. Execution is delegated to Tango through a Ruby client. The application uploads grading files, submits a job with image/files/timeout/network policy, and receives output through polling or a callback. The separation permits graders to be developed offline and run without embedding course-management decisions in the execution service. [Tango client](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/lib/tango_client.rb), [autograding orchestration](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/app/helpers/assessment_autograde_core.rb).

The bundled Tango documentation defines a machine-management interface: initialize, wait for readiness, copy files in, run, copy results out, destroy and verify destruction. It documents Docker and EC2 implementations and uses “VM” for both containers and virtual machines. Consequently, the user-supplied description's “ephemeral Docker or VM containers” needs qualification: a service interface does not itself guarantee a hardware-backed VM, clean reset or per-job isolation. Those depend on Tango's selected backend and configuration. [Machine-management contract](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/docs/tango-vmms.md), [job API](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/docs/tango-rest.md).

Grading packages conventionally contain an `autograde-Makefile` and archive. The platform runs the package and reads a final stdout JSON `scores` object keyed by assessment problem names. Manual problems can be omitted from automatic output. Optional semantic feedback adds stages, pass/fail tests, hints and timing. This lets authors start small and add better presentation without implementing another application. [Authoring contract](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/docs/lab.md), [formatted feedback](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/docs/features/formatted-feedback.md).

Staff annotations can target a line or a whole problem and associate a point adjustment. Shared comments are scoped to a problem. Documentation explicitly explains the precedence issue: editing a gradesheet overrides the annotation-derived score while leaving annotations visible. This is a particularly useful negative lesson. Multiple editable representations of the same grade create ambiguity unless authority is explicit. [Annotation semantics](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/docs/features/annotations.md), [score model](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/app/models/score.rb).

## Fit with our implementation

UVU already has the analogous separation: [Judge0 integration](../../backend/app/integrations/judge0/client.py), [pytest execution adapter](../../backend/app/domains/grading/executor.py), [host score calculation](../../backend/app/domains/grading/result_parser.py), and [official orchestration](../../backend/app/domains/runs/official_execution.py). We do not need Tango to acquire this architecture. We should make our execution contract clearer and preserve host-owned scoring configuration. Stable `ag_<key>` scoring keys are preferable to coupling results to display names, which instructors may rename.

Tango's explicit destruction-verification method supports our existing policy that cleanup failure invalidates execution success. This principle should survive any future engine adapter. Define lifecycle outcomes that include execution, result handling and verified disposal. An engine that returns a correct grade but leaves retrievable student payloads cannot be considered a successful run under our requirements.

The current Autolab client retries transport failures, including job creation calls. That is a reminder to distinguish read retries from ambiguous write retries: if a server accepted a job but its response was lost, blindly repeating creation can duplicate execution. Our ownership tokens/checkpoints already guard several duplicate-processing cases. Before changing submit retries, model accepted-but-unknown engine tokens and cleanup obligations explicitly. The source demonstrates a retry mechanism, not a proof that our desired exactly-once effects follow from retries.

## Practical improvements

### Improve manual review with anchored comments

Add optional comments anchored to the submitted file and a bounded line range, linked to a manual scoring-item key. Store anchors against the immutable official bundle snapshot, not against a filename that could later refer to different content. A content digest can disambiguate the artifact within the transient workspace; do not keep per-student hashes permanently as supposed anonymous evidence.

Keep one authoritative score per manual item. Initially comments should explain a score rather than independently calculate deductions. If later marks affect points, display the complete derivation and require an explicit override reason. The exported HTML should display criterion score, selected marks and source location consistently with the staff screen. Continue to distinguish unreviewed from reviewed-zero.

Reusable comment templates should be instructor-maintained assets independent of any student annotation. Autolab ties shared comments to an originating annotation; following that literally would conflict with our deletion boundary. Creating a persistent template from a student's comment must never copy names, code or personal context implicitly. A small instructor-authored bank of generic comments is sufficient initially.

### Add stage summaries and authored hints

The student result screen could lead with a concise staged explanation: files accepted, tests collected, execution completed, requirement failed. Instructors can attach a short hint to a known scoring requirement. Hints should point toward concepts and expected interfaces rather than expose solutions. They are deterministic, fast and available when local AI is down.

AI can explain the same public evidence, but should not become the only way to understand a failure. The initial report should remain useful without generating AI. Staff-only defects need a separate public message rather than streaming raw grader output. Autolab's live stdout feature is an idea to evaluate selectively; our validated-AI-before-streaming rule and sensitive-output filtering still apply.

### Strengthen package and engine provenance

Autolab avoids redundant uploads by comparing file hashes. We can borrow content identity for instructor packages and runtime profiles, using our existing SHA-256 artifact metadata rather than adopting its MD5 cache convention. A reusable package manifest should identify config, tests, support assets, runner protocol and image digest. Cache only approved instructor assets; student bundles and engine results keep their present lifetimes.

Do not interpret a file hash or image tag as a complete reproducibility guarantee. Package identity also depends on dependency versions, runner generation, platform behavior, timezone/locale and random seed. A digest manifest should capture what we can verify and expose missing provenance honestly.

## Tradeoffs and non-fit

Autolab's mature course product includes persistent rosters, submissions, grade records, scoreboards, penalties and collaboration features. UVU uses Canvas for those official course functions. A replacement would duplicate authority and add migrations, identity mapping and operational responsibility. Competition scoreboards do not directly support our introductory feedback goals and could reveal performance data; defer them unless there is an explicit pedagogical and approved data purpose.

The inspected helper creates email-bearing job/output names and logs detailed submission context, while the score model logs email and scores. Do not copy those telemetry patterns. Use opaque transient job identity inside approved workspaces and sanitized aggregate operational logs. Callback secrets also should not be carried into logs simply because an upstream integration does so. This is a compatibility observation, not a completed security audit.

The latest default-branch commit in this clone is almost a year before the inspection date, and the lockfile pins Rails 6.1.7.6 and Ruby 3.2.2. This warrants a current support/dependency investigation before adoption, but does not establish that the project is abandoned or vulnerable. An inspected roundtrip feature test has Tango-dependent assertions commented out; therefore its existence alone does not prove an integrated execution deployment is tested. [Dependency lockfile](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/Gemfile.lock), [roundtrip test](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/spec/features/autograding_roundtrip_spec.rb), [license metadata: Apache-2.0](https://github.com/autolab/Autolab/blob/674efe9deac197e108a426c873beb7c5f912b25f/LICENSE).

## Proposed verification

Prototype source-anchored comments on synthetic code, then compare staff view and HTML export. Verify score authority when adding/removing comments, stale-save rejection between two reviewers, section-grant enforcement and cleanup of all anchors/comments. Separately exercise engine submission-response loss, duplicate delivery, stale callbacks, terminal-result replay and deletion failure. Run these against our own engine contract rather than assuming Tango behavior transfers. None of these experiments was executed for this source-only research.
