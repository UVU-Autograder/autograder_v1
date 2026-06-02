# List of FERPA related questions

## GENERAL ASPECT

1. What approval is required before moving from testing mode to real-course grading?
   A: We need to submit a request through the myUVU portal for review by the ATSC.
2. When does data with names removed still count as a student's education record under FERPA?
3. What requirements must data satisfy before the university considers it anonymous enough?
4. If Canvas stores the student's identity (e.g., John Doe) and our autograder stores only an assignment-specific identifier (e.g., Assn#12345) and never stores names, student IDs, emails, or rosters, does the university still consider our autograder to be handling FERPA-protected education records?
   A: We would be okay then. However, the autograder cannot map student-identifiable information with those identifiers at all.
5. Because assignment-specific identifiers can be re-identified through Canvas, does exporting data that contains only those identifiers and associated grades still constitute handling FERPA-protected education records? Under what circumstances would such an export be considered compliant or non-compliant with FERPA and university policy?
   A: This is okay as long as the way we map the information back to the student is approved.
6. Does the university have a Master Services Agreement (MSA) or standard Data Protection Agreement (DPA) templates that we are required to attach to any external vendor APIs we connect to our autograder?
   A: UVU requires completing a HECVAT questionnaire and signing a DPA.

## DATA STORAGE and SECURITY ASPECT

7. Does a student's code submission count as an education record, even if there is no personal information in the code?
8. At what point does sandbox activity become an education record?
9. What security controls does the university require for FERPA-covered systems?
10. What are the university’s minimum security requirements (including encryption standards) for systems that handle FERPA-protected student data? (Types of student-related data must be encrypted, such as submissions, grades, logs, exports, etc)

## SANDBOX ASPECT

11. If a student voluntarily or accidentally includes their name or student ID number in their code and uploads it to the public sandbox code editor, does that action transform that session into a FERPA-covered record?

## ADMIN ASPECT

12. If our autograder only temporarily processes student submissions and immediately exports results without persistent storage, are there still university retention or audit requirements that apply to the processing, logs, AI-generated feedback, or exported grading data?
13. What FERPA expectations exist for instructors, TAs/IAs, and system administrators?
14. Is role-based access control sufficient for FERPA compliance?

## AI ASPECT:

15. If we host and run an AI autograding model entirely on our own university-managed servers (ensuring no student data ever leaves the physical or virtual network of the institution), does this local architecture still require a formal FERPA review to verify internal access controls and data isolation boundaries?
16. If we use Azure AI under the university's existing Microsoft Enterprise Agreement, does our institutional contract automatically cover Azure's AI/OpenAI cognitive services under the FERPA 'School Official' exception?
    A: The UVU-approved Azure AI is FERPA compliant because it does not mine any input data.
17. Are AI-generated feedback and comments themselves education records?

## MOVING FROM LOCAL HOSTING TO CLOUD DEPLOYMENT

18. When we move our automated grading pipeline from local servers to the cloud, what specific contractual requirements or Data Protection Agreements (DPAs) must be active with the cloud provider to legally designate them as a 'School Official' under FERPA?
    A: We must execute a DPA that places the vendor under UVU's direct control and strictly prohibits use or disclosure of student data.
19. Does the university's standard FERPA policy require a formal Institutional Privacy Review or a specific compliance sign-off before a department can shift a student-facing service from local infrastructure to a cloud deployment?
    A: Yes, we would have to submit a request through the UVU Software Approval Process.
