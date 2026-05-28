# UVU Autograder v1 - FERPA Analysis

This document is an internal engineering analysis of the current FERPA posture of the project. It is not legal advice and it is not a formal university approval memo.

It complements:

- [implementation_questions.md](/abs/c:/Users/Jaxon/coding/autograder_v1/docs/implementation_questions.md)
- [decisions.md](/abs/c:/Users/Jaxon/coding/autograder_v1/docs/backend_implementation/jaxon_implementation/decisions.md)
- [technical_specs.md](/abs/c:/Users/Jaxon/coding/autograder_v1/docs/backend_implementation/jaxon_implementation/technical_specs.md)

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

### §99.31 Under what conditions is prior consent not required to disclose information?
FERPA permits disclosure to contractors who are “under the direct control of the agency or institution with respect to the use and maintenance of education records” [34 C.F.R. § 99.31(a)(1)(i)(B)(2)](https://studentprivacy.ed.gov/ferpa?exp=8#0.1_se34.1.99_131). So, if the school develops and operates the autograding software itself, then FERPA generally considers the school to have “direct control” over the system and the education records used in it. A student’s class schedule is usually considered an “education record” under Family Educational Rights and Privacy Act (FERPA). The school can often use that information internally without getting separate student consent if the use is connected to legitimate educational operations.

For example, the school may use class schedules to:
- enroll students into the correct autograder course,
- connect assignments to the correct section,
- identify instructors/TAs,
- manage submissions and grades.

This is usually allowed because it supports a “legitimate educational interest.”

However, the school still must:

- limit access to authorized people,
- protect the records,
- use the data only for educational/administrative purposes,
- maintain security/privacy controls.


### FERPA Compliance Software
FERPA compliance software: represents specialized technology platforms helping schools automate, monitor, and demonstrate compliance with privacy and security requirements.

Core FERPA requirements software must support include but not limited to: 
- Access Control and Role-Based Permissions: Software should restrict users to only the student data necessary for their job role, such as teacher or administrator. Access permissions should automatically update or expire when a user’s role or employment status changes.
- Record Access Logging and Audit Trails: Systems must keep detailed logs of who accessed student records, when they accessed them, and what actions they performed. Secure audit trails help schools meet FERPA requirements and investigate unauthorized access.
- Data Minimization and Retention Controls: Schools should keep student records only as long as necessary and securely delete outdated data according to retention policies. Limiting unnecessary stored records reduces privacy and security risks.  

 FERPA does not mandate specific software, but it requires schools to implement reasonable security measures protecting education records.  Data must be protected under FERPA? All personally identifiable information in education records requires protection. This includes academic records (grades, transcripts), disciplinary records, health records maintained by schools, financial information, contact information, student identification numbers, biometric data, and indirect identifiers that could identify students when combined with other information.


## What Changed Already

- Sandbox assignments are now globally visible instead of being tied to student-specific access.
- The sandbox no longer requires student authentication.
- The persistent roster-based sandbox authorization mapping was removed from the current spec.
- Zero-retention remains a core design principle for submissions, detailed artifacts, and Judge0 execution records.
- Judge0 cleanup is explicitly documented as `DELETE /submissions/{token}` immediately after retrieval.

Those changes reduce the chance that the student-facing sandbox itself becomes a disclosure of enrollment or schedule information. They do not eliminate the official workflow's FERPA obligations.

## Issues And Fixes Matrix

| Current issue                                                                                            | Why this is a FERPA or institutional-control problem                                                                                                                                                       | Already mitigated by current spec                                                           | Preferred solution                                                                                                                                                                                                                           | Alternative solution(s)                                                                                                                                                                                                           |
| -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Student-specific sandbox access used to reveal course or assignment visibility based on student identity | UVU classifies schedule details as non-directory information, and UVU's student-ID-as-directory rationale depends on the ID not granting access to education records without additional authentication     | Yes. The current sandbox is public and assignment-driven rather than student-driven         | Keep the public sandbox model and do not reintroduce student-specific sandbox visibility without formal approval                                                                                                                             | If a future student-specific sandbox is required, gate it behind an approved UVU-controlled auth system and explicit institutional approval                                                                                       |
| Official grading still processes Canvas ZIPs, submission-linked identifiers, and per-student outputs     | Education records include records directly related to students maintained by the institution or by a party acting on its behalf; instructor convenience alone is not enough to authorize this workflow     | No                                                                                          | Treat official grading with live student data as institutionally gated and require formal UVU approval before production use                                                                                                                 | Restrict the app to synthetic, pseudonymized, or instructor-de-identified data until approval exists                                                                                                                              |
| Canvas-ready grade CSVs and per-student feedback ZIPs are still sensitive outputs                        | Grades are non-directory information at UVU, and exported files can themselves become education-record disclosures if generated or handled outside approved controls                                       | No                                                                                          | Require UVU approval for live export generation and handling on the Dell workstation                                                                                                                                                         | Disable live student export generation and keep the app in preview-only mode for real courses                                                                                                                                     |
| Azure OpenAI with live student submissions                                                               | Sending student code, traceback context, or grading context to Azure is a third-party disclosure unless UVU has approved that exact use under its governance model                                         | No                                                                                          | Pursue UVU approval for Azure OpenAI use through UVU's secure enterprise Microsoft/Azure tenant rather than an independent developer tenant, and require confirmation before live use                                                        | Use a local open-weight model on the Dell workstation if Azure approval is denied; or disable AI feedback for live student data                                                                                                   |
| Stanford MOSS for live student code                                                                      | MOSS is a third-party server, so sending student code there is an external disclosure                                                                                                                      | No                                                                                          | Do not use MOSS for live student data unless UVU explicitly approves that disclosure path                                                                                                                                                    | Replace MOSS with a local plagiarism tool running entirely offline on the Dell workstation, such as Dolos or JPlag via Docker or CLI, so no student data is transmitted to third-party servers                                    |
| Approved hardware does not equal approved workflow                                                       | FERPA compliance turns on institutional control and authorized use, not just device ownership or on-prem location; UVU faculty guidance also says student records should be stored on approved UVU systems | Partly. The current docs assume Dell-workstation permission, but not full workflow approval | Formalize the tool's status through UVU's Software Approval Process, routed through the myUVU portal and reviewed through the Academic Technology Steering Committee (ATSC) and related UVU governance bodies before live student-record use | Keep the app limited to non-live, non-student-record workflows until institutional approval is obtained                                                                                                                           |
| Instructor uploads do not by themselves establish authorization                                          | Faculty members do not personally convert a system into an authorized institutional records workflow merely by exporting or uploading course data                                                          | No                                                                                          | Require explicit UVU authorization for instructor upload workflows involving live student data                                                                                                                                               | Require instructor-side pseudonymization before upload when live approval is deferred                                                                                                                                             |
| Manual ZIP and CSV handling increases unmanaged disclosure risk                                          | Manual instructor export/import workflows create more opportunities for local copies, ad hoc sharing, and handling outside approved controls                                                               | No                                                                                          | Prefer a governed Canvas integration path over manual ingest/export where feasible                                                                                                                                                           | Evaluate Canvas LTI 1.3 plus anonymous-grading support so the app can process anonymous assignment-specific identifiers instead of raw student identifiers; treat this as a candidate architecture, not a current approved design |

## Preferred Path

The preferred compliance posture for the current project is:

- keep the public sandbox in scope
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
   - use a local plagiarism tool if third-party plagiarism services are not approved

Reasonable fallback positions if approval is deferred:

- keep the system limited to assignment authoring, test authoring, model-solution validation, synthetic submissions, and the public sandbox
- disable live official grading exports
- disable AI feedback for live student data
- disable MOSS for live student data

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

User-provided mitigation ideas incorporated here as candidate technical directions that still require UVU review and implementation validation:

- Canvas LTI 1.3 plus anonymous-grading support instead of manual ZIP/CSV handling
- local open-weight LLM fallback on the Dell workstation
- local plagiarism tooling such as Dolos or JPlag instead of MOSS for live student data
