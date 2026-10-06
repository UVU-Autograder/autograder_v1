# Otter-Grader: package generation and local practice

Inspected 2026-10-06 from a shallow clone of [ucbds-infra/otter-grader](https://github.com/ucbds-infra/otter-grader), commit `190c1a4c3e97fff6f6469b7a506ca8d073384a64` (commit timestamp 2026-10-01). The manifest identifies version 7.0.0. No package was installed, notebook executed or Docker image built. The clone was removed before cloning Piston. [Comparison and integration proposal](autograding-platforms.md).

## Architecture and workflow

Otter is a Python/R grading toolkit rather than a course web application. Its modules cover assignment generation, student checks, grader-package generation, submission execution, local Docker grading and exports. That modularity is relevant to UVU: authoring and verification can improve without redesigning staff identity or Canvas intake. [Overview](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/README.md), [manifest and CLI](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/pyproject.toml).

`otter assign` processes a master notebook into distinct autograder and student outputs. Student output removes solutions and hidden tests; autograder output carries the full test set and supporting environment requirements. The documented default workflow clears copied notebook outputs, creates grading artifacts and runs tests on the solution notebook. Public tests can then run locally for students. RMarkdown and Quarto support follow related authoring paths. [Assignment workflow](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/docs/otter_assign/usage.rst), [output separation](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/otter/assign/output.py), [test manager](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/otter/assign/tests_manager.py).

Local grading builds an assignment image and submits grading work through a bounded thread pool, with a container for each submission. It collects results and can produce CSV grades and notebook PDFs for manual review. The API defaults to four containers, no explicit submission timeout, and networking enabled unless disabled. Those defaults are appropriate to inspect rather than silently carry into a public execution service. [Local grading entrypoint](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/otter/grade/__init__.py), [container implementation](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/otter/grade/containers.py), [local workflow](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/docs/workflow/executing_submissions/otter_grade.rst).

The result model represents tests, points, errors and public/hidden visibility, and can produce a Gradescope-shaped JSON object. Local result transport also copies a pickle file from the grading container and loads it with `dill`. That is an object-deserialization trust boundary we should not import into the UVU host; use validated data-only results instead. This observation is not a demonstrated exploit against Otter. [Results and visibility](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/otter/test_files/__init__.py), [grader configuration](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/otter/run/run_autograder/autograder_config.py).

Plugins expose authoring, generation, before/after execution, grading and reporting hooks. This makes extensions convenient, but not inherently safe. Hook code can access submission metadata and alter grading behavior; it is privileged course/platform code and belongs in the approved build process. [Plugin contract](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/otter/plugins/abstract_plugin.py).

## The most useful adaptation: a publishable assignment package

Our current instructor assets already distinguish tests, models and support files. Otter suggests making that separation visible as a reproducible export/build operation. A UVU package could contain:

- A canonical instructor manifest: scoring keys, file requirements, concept policy, artifact identities, runtime profile and protocol version.
- An instructor verification bundle: models, positive/negative synthetic cases and expected outcomes.
- A student bundle: starter/support assets and explicitly public local tests, with no model solutions or official-only tests.
- A release report: validation results, source package digest and a clear list of unsupported/missing checks.

Generate all outputs from the same config and assets, then inspect the student bundle for leakage. Students should never receive the instructor verification bundle through a broadly labeled “download assignment” action. The package should be inert data until an approved isolated grading process runs its tests. Package extraction must reuse our archive protections rather than copy a toolkit's direct `extractall` call.

This aligns with the planned master-course release/adoption workflow. Published instructor artifacts can persist; student attempt data cannot be baked into releases or evidence. A section adopts a specific package version. Editing a draft should not change a released assignment, and an official batch should capture its adopted package when admitted. Our current [official snapshot](../../backend/app/domains/runs/official_execution.py) is first created in the execution step, so there is a queue-time configuration-change window to address; it should not be described as fully immutable at intake today.

## Optional local checks for students

Otter's student client provides rapid feedback without waiting for a central service. UVU could offer a small instructor-generated public pytest bundle for students already using Python locally. Include supported Python/dependency versions and simple commands. Report that these checks cover public practice requirements; official results still come from the approved server runtime and full rubric.

Local execution should use files students choose on their own machine, without uploading identities or maintaining a new server attempt history. Avoid forcing a new toolkit into introductory courses if it increases setup burden. A downloadable pytest bundle is a smaller initial experiment than packaging Otter as a client dependency. Compare student success and support effort against the existing browser sandbox before promoting it.

## Notebook support is a separate investment

Otter offers a strong reference if UVU later needs notebook/data-science courses. Notebook grading requires more than accepting `.ipynb` in the upload dialog: cell execution order, kernel lifetime, state reset, timeouts, large outputs, embedded HTML/images and export rendering all affect correctness and safety. The inspected preprocessor illustrates the additional execution machinery. [Notebook execution preprocessing](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/otter/execute/preprocessor.py).

For such a course, require a clean-kernel sequential run, deterministic seed policy, bounded notebook size/output, sanctioned data assets and a renderer that treats student HTML as untrusted. Notebook PDFs would be official student detail and expire with the review workspace. Preserve Kata isolation and the current on-prem data boundary. Do not add R/notebook runtimes simply because the toolkit supports them.

## Integration options and constraints

The least expensive integration is conceptual: implement package generation, leak checks and local public tests ourselves. A second option is an authoring-time importer for an explicitly supported Otter subset, translating test/point/visibility metadata to our stable keys. It should produce a conversion report and reject unsupported plugins, notebooks or scoring behavior instead of pretending to preserve them. Actual execution of Otter-generated graders is a third, substantially larger runtime project.

Its CSV/Gradescope compatibility is not automatic Canvas write-back. Our Canvas filename grouping, identity reconciliation, manual completeness gate and HTML export still own the official workflow. Keep those semantics when experimenting with package interoperability.

Otter's configurable build-time dependencies and lifecycle hooks should never become arbitrary network installation or host plugins per public submission. Bake reviewed dependencies into approved images. Its `no_kill` debugging option also conflicts with UVU's immediate engine-payload cleanup. Container deletion does not automatically establish deletion of copied host result/PDF files; lifecycle ownership must cover every artifact.

The inspected [license](https://github.com/ucbds-infra/otter-grader/blob/190c1a4c3e97fff6f6469b7a506ca8d073384a64/LICENSE) identifies BSD-3-Clause. The toolkit's notebook/export dependencies still create a larger maintenance surface than our current Python runner. Recent dependency updates establish snapshot activity, not a complete support guarantee.

## Proposed experiment

Generate separate instructor/student packages for one synthetic assignment. Verify all referenced paths, ensure the student ZIP lacks model and private-test bytes, execute its public checks locally on a correct and incorrect implementation, and compare those results to server grading. Test a stale student package against a newer published release and show a clear version mismatch. No upstream execution or such experiment was performed for this report.
