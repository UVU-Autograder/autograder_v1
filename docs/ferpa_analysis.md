# UVU Autograder v1 - FERPA Analysis

This document is an internal engineering analysis of the current FERPA posture of the project. It is not legal advice and it is not a formal university approval memo.

It complements:

- [decisions.md](/abs/c:/Users/Jaxon/coding/autograder_v1/docs/backend_implementation/decisions.md)
- [technical_specs.md](/abs/c:/Users/Jaxon/coding/autograder_v1/docs/technical_specs.md)

## Current Posture

The current specification is materially better than the earlier sandbox model, but it is still not cleared for unrestricted live student-record use.

The biggest FERPA improvement already made is the removal of student-specific sandbox access. UVU treats student schedule and schedule details as non-directory information, and UVU treats student ID as directory information only because it cannot by itself unlock education records without the student's password and MFA. Under the earlier model, the sandbox used student-specific identity and enrollment-linked visibility. Under the current model, sandbox assignments are globally visible and no student authentication is required, which materially reduces that specific FERPA problem. See UVU FERPA guidance and the U.S. Department of Education FAQ on student identifiers as directory information:

- [UVU FERPA](https://www.uvu.edu/registration/ferpa/index.html)
- [May a social security number or other student identification number be listed as directory information?](https://studentprivacy.ed.gov/faq/may-social-security-number-or-other-student-identification-number-be-listed-directory)
- [§99.37 What conditions apply to disclosing directory information?](https://studentprivacy.ed.gov/ferpa?exp=8#0.1_se34.1.99_131)

That change does not clear the whole system. The official grading workflow still processes education-record-linked data, and FERPA compliance still turns on institutional authorization, direct control, approved systems, and approved disclosures rather than on "we store less data" alone. See:

- [UVU FERPA](https://www.uvu.edu/registration/ferpa/index.html)
- [FERPA for Faculty and Staff](https://www.uvu.edu/registration/faculty_resources/ferpa.html)
- [Who is a “school official” under FERPA?](https://studentprivacy.ed.gov/faq/who-school-official-under-ferpa)
- [FERPA regulations](https://studentprivacy.ed.gov/ferpa?exp=8)

### Institutional Control Requirements

FERPA can permit school-official or contractor access when the institution keeps direct control over the use and maintenance of education records. For this project, that means the official grading workflow needs more than a good zero-retention design: it needs UVU approval, role-bounded access, approved infrastructure, and approved handling for any external service such as Azure OpenAI.

The current M1 design supports that direction by keeping the sandbox public and non-student-specific, limiting persistent data to metadata, and making cleanup part of the grading contract. Those controls reduce risk but do not by themselves authorize live official grading with education-record-linked data.

## What Changed Already

- Sandbox assignments are now globally visible instead of being tied to student-specific access.
- The sandbox no longer requires student authentication.
- The persistent roster-based sandbox authorization mapping was removed from the current spec.
- Zero-retention remains a core design principle for submissions, detailed artifacts, and Judge0 execution records.
- Judge0 cleanup is explicitly documented as `DELETE /submissions/{token}` immediately after retrieval.

Those changes reduce the chance that the student-facing sandbox itself becomes a disclosure of enrollment or schedule information. They do not eliminate the official workflow's FERPA obligations.

## M1 Validation Data

M1 validation uses only fake/synthetic data or completely anonymized data. M1 does not use live student submissions, Canvas exports containing real student identifiers, or pseudonymous datasets that require a re-identification map.

Completely anonymized validation data must not be reasonably linkable back to a student by the app, the project team, or an instructor-held mapping file. Synthetic data is preferred because it avoids the ambiguity of whether a real submission has been anonymized enough.

If a real submission is ever considered for anonymized validation, the anonymization pass must remove or replace direct identifiers before the data reaches the app, including:

- student names
- UVU IDs
- email addresses
- Canvas user IDs or other Canvas-linked student identifiers
- filenames and folder labels that include student identifiers
- comments, package names, or project labels that directly identify a student
- any other direct identifier an instructor or UVU reviewer can reasonably spot before upload

Pseudonymous labels with a retained mapping, even if the mapping stays outside the app, are not considered completely anonymized for M1 validation. They may be a future manual-grading bridge only after the official workflow receives institutional approval.

The app should treat fake and fully anonymized validation bundles with the same zero-retention discipline used for student-code-bearing data: no persistent source bodies, filenames, detailed tracebacks, detailed feedback, or per-student artifacts.

Anonymization reduces validation risk, but it does not by itself authorize all downstream uses. Azure OpenAI feedback must remain disabled for any real student-derived code unless the UVU/Azure approval checklist is complete. Live official grading with education-record-linked data still requires formal institutional approval.

## Issues And Fixes Matrix

| Current issue                                                                                            | Why this is a FERPA or institutional-control problem                                                                                                                                                                                                  | Already mitigated by current spec                                                           | Preferred solution                                                                                                                                                                                                                           | Alternative solution(s)                                                                                                                                                                                                          |
| -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Student-specific sandbox access used to reveal course or assignment visibility based on student identity | UVU classifies schedule details as non-directory information, and UVU's student-ID-as-directory rationale depends on the ID not granting access to education records without additional authentication                                                | Yes. The current sandbox is public and assignment-driven rather than student-driven         | Keep the public sandbox model and do not reintroduce student-specific sandbox visibility without formal approval                                                                                                                             | If a future student-specific sandbox is required, gate it behind an approved UVU-controlled auth system and explicit institutional approval                                                                                      |
| Official grading ingest, processing, and exports are still live education-record workflows               | Canvas ZIPs, submission-linked identifiers, Canvas-ready grade CSVs, and per-student feedback ZIPs can all contain or produce education-record data; instructor upload or convenience does not by itself make the workflow institutionally authorized | No                                                                                          | Treat live official grading as institutionally gated and require formal UVU approval for ingest, processing, export generation, and handling before production use                                                                           | Keep M1 limited to fake/synthetic or completely anonymized validation data until approval exists; disable live student export generation and keep real-course use out of M1                                                       |
| Azure OpenAI with live student submissions                                                               | Sending student code, traceback context, or grading context to Azure is a third-party disclosure unless UVU has approved that exact use under its governance model                                                                                    | No                                                                                          | Pursue UVU approval for Azure OpenAI use through UVU's secure enterprise Microsoft/Azure tenant rather than an independent developer tenant, and require confirmation before live use                                                        | Use a local open-weight model on the Dell workstation if Azure approval is denied; or disable AI feedback for live student data                                                                                                  |
| M1 validation with real or pseudonymous student data                                                     | Pseudonymous or re-identifiable datasets can still be linked back to students, and app-side redaction still receives identifiable data first                                                                                                           | Partly. The current zero-retention model limits persistence after intake                    | Use only fake/synthetic or completely anonymized validation data for M1                                                                                                                                                                      | Treat pseudonymous/manual re-identification workflows as future official-grading options only after formal approval                                                                                                             |
| Approved hardware does not equal approved workflow                                                       | FERPA compliance turns on institutional control and authorized use, not just device ownership or on-prem location; UVU faculty guidance also says student records should be stored on approved UVU systems                                            | Partly. The current docs assume Dell-workstation permission, but not full workflow approval | Formalize the tool's status through UVU's Software Approval Process, routed through the myUVU portal and reviewed through the Academic Technology Steering Committee (ATSC) and related UVU governance bodies before live student-record use | Keep the app limited to non-live, non-student-record workflows until institutional approval is obtained                                                                                                                          |
| Manual ZIP and CSV handling increases unmanaged disclosure risk                                          | Manual instructor export/import workflows create more opportunities for local copies, ad hoc sharing, and handling outside approved controls                                                                                                          | No                                                                                          | Prefer a governed Canvas integration path over manual ingest/export where feasible                                                                                                                                                           | Evaluate Canvas LTI 1.3 plus anonymous-grading support so the app can process anonymous assignment-specific identifiers instead of raw student identifiers; treat this as a possible architecture, not a current approved design |

## Preferred Path

The preferred compliance posture for the current project is:

- keep the public sandbox in scope
- limit M1 validation to fake/synthetic or completely anonymized data
- do not assume official grading with live student data is cleared by the current docs alone
- require formal UVU approval and institutional control before production use of live official grading workflows
- narrow live-data processing to approved workflows only

Within that posture, the strongest technical direction is:

1. Keep the sandbox public and non-student-specific.
2. Treat official grading as the only workflow that may touch live student education records.
3. Pursue UVU approval for the official workflow, including the Dell workstation operating model and any approved vendor disclosures.
4. Reduce external disclosure where possible:
   - prefer a governed Canvas integration path over manual ZIP/CSV handling when feasible
   - consider Canvas LTI 1.3 with anonymous-grading support as a future architecture path if UVU wants institutional integration
   - use UVU's enterprise Azure tenant if Azure OpenAI is approved
   - use a local LLM if Azure OpenAI is not approved
   - defer plagiarism detection unless UVU approves a local or otherwise institutionally approved tool

Reasonable fallback positions if approval is deferred:

- keep the system limited to assignment authoring, test authoring, model-solution validation, fake/synthetic submissions, completely anonymized validation bundles, and the public sandbox
- disable live official grading exports
- disable AI feedback for live, pseudonymous, or real student-derived code unless UVU/Azure approval is complete
- keep plagiarism detection out of live M1 workflows

## References

Official UVU and FERPA sources used in this analysis:

- [UVU FERPA](https://www.uvu.edu/registration/ferpa/index.html)
- [UVU FERPA for Faculty and Staff](https://www.uvu.edu/registration/faculty_resources/ferpa.html)
- [UVU FERPA Annual Notice](https://www.uvu.edu/registration/docs/ferpa_annual_notice.pdf)
- [UVU System Procurement and Implementation](https://www.uvu.edu/biservices/system-procurement-implementation.html)
- [UVU Academic Technology Steering Committee](https://www.uvu.edu/biservices/governance.html)
- [UVU Policy Manual: Policy 445 Institutional Data Governance and Management](https://www.uvu.edu/policies/manual/)
- [U.S. Department of Education: Who is a “school official” under FERPA?](https://studentprivacy.ed.gov/faq/who-school-official-under-ferpa)
- [U.S. Department of Education: FERPA regulations](https://studentprivacy.ed.gov/ferpa?exp=8)
- [U.S. Department of Education: May a student identification number be listed as directory information?](https://studentprivacy.ed.gov/faq/may-social-security-number-or-other-student-identification-number-be-listed-directory)
- [FERPA compliance software](https://secureprivacy.ai/blog/ferpa-compliance-software)

User-provided mitigation ideas incorporated here as possible technical directions that still require UVU review and implementation validation:

- Canvas LTI 1.3 plus anonymous-grading support instead of manual ZIP/CSV handling
- local open-weight LLM fallback on the Dell workstation
- future local plagiarism tooling such as Dolos or JPlag, if UVU approves it for live student data
