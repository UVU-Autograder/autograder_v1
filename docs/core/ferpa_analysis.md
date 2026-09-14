# UVU Autograder — FERPA Analysis

This document is an internal engineering analysis of the current FERPA posture of the project. It is not legal advice and it is not a formal university approval memo.

It complements:

- [decisions.md](decisions.md)
- [technical_specs.md](technical_specs.md)

## Current Posture

UVU treats student schedule and schedule details as non-directory information, and UVU treats student ID as directory information only because it cannot by itself unlock education records without the student's password and MFA. Under the earlier model, the sandbox used student-specific identity and enrollment-linked visibility. Under the current model, sandbox assignments are globally visible and no student authentication is required, which materially reduces that specific FERPA problem. See UVU FERPA guidance and the U.S. Department of Education FAQ on student identifiers as directory information:

- [UVU FERPA](https://www.uvu.edu/registration/ferpa/index.html)
- [May a social security number or other student identification number be listed as directory information?](https://studentprivacy.ed.gov/faq/may-social-security-number-or-other-student-identification-number-be-listed-directory)
- [§99.37 What conditions apply to disclosing directory information?](https://studentprivacy.ed.gov/ferpa?exp=8#0.1_se34.1.99_131)

That change does not clear the whole system. The official grading workflow still processes education-record-linked data, and FERPA compliance still turns on institutional authorization, direct control, approved systems, and approved disclosures rather than on "we store less data" alone. See:

- [UVU FERPA](https://www.uvu.edu/registration/ferpa/index.html)
- [FERPA for Faculty and Staff](https://www.uvu.edu/registration/faculty_resources/ferpa.html)
- [Who is a “school official” under FERPA?](https://studentprivacy.ed.gov/faq/who-school-official-under-ferpa)
- [FERPA regulations](https://studentprivacy.ed.gov/ferpa?exp=8)

### Institutional Control Requirements

FERPA can permit school-official or contractor access when the institution keeps direct control over the use and maintenance of education records. For this project, that means the official grading workflow needs more than a good retention design: it needs UVU approval, role-bounded access, approved infrastructure, and approved handling for any local AI model.

**Current institutional status (project team):** UVU Software Approval (myUVU / ATSC) for live official grading is **in progress**. Until approval completes, treat production use of live Canvas exports as institutionally gated even when technical retention controls are in place.

The current design supports that direction by keeping the sandbox public and non-student-specific, limiting persistent data to metadata, retaining official review/export artifacts only ≤24h (or until staff cleanup), and wiping sandbox artifacts immediately. Those controls reduce risk but do not by themselves authorize live official grading with education-record-linked data.

Answered project questions incorporated into this analysis:

- Moving from testing mode to real-course grading requires a request through the myUVU Software Approval Process for ATSC and related institutional review.
- If the autograder cannot map assignment-specific identifiers back to student-identifiable information, that reduces the direct-identification risk; however, exports that can be mapped back through Canvas still need an approved mapping and handling process.
- External vendor APIs require UVU-approved contracting controls, including HECVAT review and an active Data Protection Agreement where applicable.
- Moving from local hosting to cloud deployment requires an active DPA that places the vendor under UVU's direct control and restricts student-data use or disclosure.
- A fully local model on university-managed infrastructure can reduce third-party disclosure, but institutional review of access control, data isolation, and operating procedures still applies for FERPA-covered use.

## What Changed Already

- Sandbox assignments are globally visible instead of being tied to student-specific access.
- The sandbox no longer requires student authentication.
- The persistent roster-based sandbox authorization mapping was removed from the current spec.
- Retention remains a core design principle: Judge0/Kata artifacts deleted immediately after retrieval; sandbox wipe after results; official identifiable artifacts ≤24h or until staff cleanup.
- Judge0 cleanup is explicitly documented as `DELETE /submissions/{token}` immediately after retrieval.
- Sandbox Local LLM may process student **code** when the payload is not personally traceable (no student PII/identifiers). Official-run AI is deferred.

Those changes reduce the chance that the student-facing sandbox itself becomes a disclosure of enrollment or schedule information. They do not eliminate the official workflow's FERPA obligations.

## Validation Data

Prefer fake/synthetic data or completely anonymized data for validation until live-data posture is confirmed for a given workflow. Do not use live student submissions, Canvas exports containing real student identifiers, or pseudonymous datasets that require a re-identification map for casual validation.

Completely anonymized validation data must not be reasonably linkable back to a student by the app, the project team, or an instructor-held mapping file. Synthetic data is preferred because it avoids the ambiguity of whether a real submission has been anonymized enough.

If a real submission is ever considered for anonymized validation, the anonymization pass must remove or replace direct identifiers before the data reaches the app, including:

- student names
- UVU IDs
- email addresses
- Canvas user IDs or other Canvas-linked student identifiers
- filenames and folder labels that include student identifiers
- comments, package names, or project labels that directly identify a student
- any other direct identifier an instructor or UVU reviewer can reasonably spot before upload

Pseudonymous labels with a retained mapping, even if the mapping stays outside the app, are not considered completely anonymized.

The app should treat fake and fully anonymized validation bundles with the same retention discipline used for student-code-bearing data.

### Local POC / developer use of real Canvas exports

Real Canvas bulk-download ZIPs may be used on local or on-prem POC hosts for debugging and integration testing **only when all of the following remain true**:

- access is limited to authorized staff accounts (`@uvu.edu`) and section-scoped official routes
- student code, Canvas identifiers, and student names exist only in **ephemeral** official workspaces (≤24h or staff cleanup)
- PostgreSQL `RunSummary` and long-lived logs remain aggregate-only and non-identifying
- Monaco/file-tree surfaces show **sanitized assignment-local filenames** only (for example `dessert.py`), not raw Canvas export names
- exports (CSV, feedback ZIP) are treated as education-record artifacts and handled under instructor/institutional policy
- real exports are not committed to git, attached to issues, or reused as long-lived fixtures without anonymization

This posture is acceptable for POC engineering while institutional approval is in progress. It does **not** replace formal UVU approval for production/live-course deployment.

Anonymization reduces validation risk, but it does not by itself authorize all downstream uses. Live official grading with education-record-linked data still requires formal institutional approval.

## Issues And Fixes Matrix

| Current issue                                                                                            | Why this is a FERPA or institutional-control problem                                                                                                                                                                                                  | Already mitigated by current spec                                                           | Preferred solution                                                                                                                                                                                                                           | Alternative solution(s)                                                                                                                                                                                                          |
| -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Student-specific sandbox access used to reveal course or assignment visibility based on student identity | UVU classifies schedule details as non-directory information, and UVU's student-ID-as-directory rationale depends on the ID not granting access to education records without additional authentication                                                | Yes. The current sandbox is public and assignment-driven rather than student-driven         | Keep the public sandbox model and do not reintroduce student-specific sandbox visibility without formal approval                                                                                                                             | If a future student-specific sandbox is required, gate it behind an approved UVU-controlled auth system and explicit institutional approval                                                                                      |
| Official grading ingest, processing, and exports are still live education-record workflows               | Canvas ZIPs, submission-linked identifiers, Canvas-ready grade CSVs, and per-student feedback ZIPs can all contain or produce education-record data; instructor upload or convenience does not by itself make the workflow institutionally authorized | Partly. ≤24h official retention + metadata-only Postgres                                    | Treat live official grading as institutionally gated and require formal UVU approval for production use                                                                                                                                      | Prefer synthetic/anonymized validation until approval exists                                                                                                                                                                     |
| AI feedback with student code                                                                            | Model input is a disclosure that must meet institutional privacy and security standards                                                                                                                                                               | Partly. Sandbox-only AI; code must not be personally traceable                              | Keep Local LLM on university-managed infrastructure; strip identifiers; sandbox only until official AI is explicitly approved                                                                                                                | Disable AI if a payload cannot be made non-identifying                                                                                                                                                                           |
| Validation with real or pseudonymous student data                                                        | Pseudonymous or re-identifiable datasets can still be linked back to students                                                                                                                                                                         | Partly. Retention limits persistence after intake                                           | Prefer fake/synthetic or completely anonymized validation data                                                                                                                                                                               | Treat pseudonymous workflows as future options only after formal approval                                                                                                                                                        |
| Approved hardware does not equal approved workflow                                                       | FERPA compliance turns on institutional control and authorized use, not just device ownership or on-prem location                                                                                                                                     | Partly. Dell-workstation hosting assumed, full workflow approval may still be needed        | Formalize the tool's status through UVU's Software Approval Process (myUVU / ATSC and related bodies) before live student-record use                                                                                                         | Keep non-live workflows until institutional approval is obtained                                                                                                                                                                 |
| Manual ZIP and CSV handling increases unmanaged disclosure risk                                          | Manual instructor export/import workflows create more opportunities for local copies and ad hoc sharing                                                                                                                                               | No                                                                                          | Prefer a governed Canvas integration path over manual ingest/export where feasible                                                                                                                                                           | Evaluate Canvas LTI 1.3 plus anonymous-grading support as a possible future architecture                                                                                                                                         |

## Ephemeral vs persistent data boundary

| Data | Allowed location | Max retention | FERPA notes |
| :--- | :--- | :--- | :--- |
| Student code files | Official review workspace (`student_{canvas_id}/`) | ≤24h or staff cleanup | Staff-auth, section-scoped; not in Postgres |
| Canvas student name, Canvas user id, submission id | Ephemeral `run_details.json`, CSV export, feedback ZIP | ≤24h or staff cleanup | Required for staff review and Canvas CSV import; must not enter Postgres or long-lived logs |
| Sanitized assignment-local filenames (`dessert.py`) | Monaco preview / file-tree API responses | ≤24h or staff cleanup | Preferred staff-facing filename shape |
| Raw Canvas export filenames (`name_id_submission_dessert-uuid.py`) | Raw uploaded ZIP only | ≤24h or staff cleanup | Not shown in Monaco/file-tree surfaces after normalization |
| Aggregate run counts / coarse failure categories | Postgres `RunSummary` | Persistent | Compliant when non-identifying |
| Student code, tracebacks, Judge0 payloads | Judge0 + `ag_grade_*` execution workspace | Immediate delete after retrieval | Zero-retention execution boundary |

Staff and developers must not copy ephemeral exports into tickets, logs, or repository fixtures without anonymization.

### Structured audit logging

Operational review relies on structured audit events emitted by `backend/app/core/audit_log.py`:

- allowlisted JSON fields only (`run_id`, aggregate counts, coarse `failure_category`, staff actor id, and similar non-identifying metadata)
- no student names, Canvas ids, raw Canvas filenames, student code, or Judge0 tokens in audit payloads
- a process-wide `SensitiveDataFilter` redacts Canvas export filenames, `student_{canvas_id}` path segments, email addresses, and Judge0 tokens from all application logs
- when redaction occurs, an `audit.pii_redacted` event is emitted for traceability

Audit events cover official ingest, run lifecycle transitions, manual/expired workspace cleanup, and Judge0 cleanup failures. Audit logs are aggregate operational evidence and must not be treated as an education-record store.

## Preferred Path

The preferred compliance posture for the current project is:

- keep the public sandbox in scope
- prefer fake/synthetic or completely anonymized validation data until live-data posture is confirmed
- do not assume official grading with live student data is cleared by the current docs alone
- require formal UVU approval and institutional control before production use of live official grading workflows
- narrow live-data processing to approved workflows only
- sandbox Local LLM: code-only payloads that are not personally traceable; official AI deferred

Within that posture, the strongest technical direction is:

1. Keep the sandbox public and non-student-specific.
2. Treat official grading as the workflow that may touch live student education records (with ≤24h review retention).
3. Pursue UVU approval for the official workflow, including the Dell workstation operating model.
4. Reduce external disclosure where possible:
   - prefer a governed Canvas integration path over manual ZIP/CSV handling when feasible
   - consider Canvas LTI 1.3 with anonymous-grading support as a future architecture path if UVU wants institutional integration
   - use the local LLM on university-managed infrastructure with PII-safe sandbox payloads

## References

Official UVU and FERPA sources used in this analysis:

- [UVU FERPA](https://www.uvu.edu/registration/ferpa/index.html)
- [UVU FERPA for Faculty and Staff](https://www.uvu.edu/registration/faculty_resources/ferpa.html)
- [UVU FERPA Annual Notice](https://www.uvu.edu/registration/docs/ferpa_annual_notice.pdf)
- [UVU System Procurement and Implementation](https://www.uvu.edu/biservices/system-procurement-implementation.html)
- [UVU Academic Technology Steering Committee](https://www.uvu.edu/biservices/governance.html)
- [UVU Policy Manual: Policy 445 Institutional Data Governance and Management](https://www.uvu.edu/policies/manual/)
