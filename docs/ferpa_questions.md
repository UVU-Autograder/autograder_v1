# List of FERPA related questiosn 

## GENERAL ASPECT
1. What approval is required before moving from testing mode to real-course grading?
2. When does data with names removed still count as a student's education record under FERPA?
3. What requirements must data satisfy before the university considers it anonymous enough?
4. If Canvas stores the student's identity (e.g., John Doe) and our autograder stores only an assignment-specific identifier (e.g., Assn#12345) and never stores names, student IDs, emails, or rosters, does the university still consider our autograder to be handling FERPA-protected education records?
5. Because assignment-specific identifiers can be re-identified through Canvas, does exporting data that contains only those identifiers and associated grades still constitute handling FERPA-protected education records? Under what circumstances would such an export be considered compliant or non-compliant with FERPA and university policy?
6. Does the university have a Master Services Agreement (MSA) or standard Data Protection Agreement (DPA) templates that we are required to attach to any external vendor APIs we connect to our autograder?

## DATA STORAGE and SECURITY ASPECT
7. Does a student's code submission count as an education record, even if there is no personal information in the code? 
8. Do execution logs, AI-generated feedback comments, an autograded score, and test case results count as an education record?
9. At what point does sandbox activity become an education record?
10. Does FERPA still apply to temporary files or intermediate artifacts created during grading if they contain or are associated with student submissions, even if they are deleted immediately after processing?
11. What security controls does the university require for FERPA-covered systems?
12. What are the university’s minimum security requirements (including encryption standards) for systems that handle FERPA-protected student data? (Types of student-related data must be encrypted, such as submissions, grades, logs, exports, etc)

## SANDBOX ASPECT
13. Does FERPA apply to a system that processes student code if the system itself does not authenticate users or store personally identifiable information, but the data can still be linked to students through other university systems like Canvas?
14. If a student voluntarily or accidentally includes their name or student ID number in their code and uploads it to the public sandbox code editor, does that action transform that session into a FERPA-covered record?


## ADMIN ASPECT  
15. If our autograder only temporarily processes student submissions and immediately exports results without persistent storage, are there still university retention or audit requirements that apply to the processing, logs, or exported grading data?
16. What FERPA expectations exist for instructors, TAs/IAs, and system administrators?
17. Is role-based access control sufficient for FERPA compliance?

## AI ASPECT: 
18. If we host and run an AI autograding model entirely on our own university-managed servers (ensuring no student data ever leaves the physical or virtual network of the institution), does this local architecture still require a formal FERPA review to verify internal access controls and data isolation boundaries?
19. If we use Azure AI under the university's existing Microsoft Enterprise Agreement, does our institutional contract automatically cover Azure's AI/OpenAI cognitive services under the FERPA 'School Official' exception?
20. If we completely strip direct student identifiers (names, emails, IDs) from the source code files before uploading them to the MOSS server, does the university consider that data sufficiently de-identified under FERPA?
21. Given that computer science code has a unique style (indirect identifiers), does counsel require us to build an explicit 'Click-to-Consent' checkbox into our student user interface before transmitting their code to MOSS?
22. Are AI-generated feedback and comments themselves education records?

## MOVING FROM LOCAL HOSTING TO CLOUD DEPLOYMENT 
23. When we move our automated grading pipeline from local servers to the cloud, what specific contractual requirements or Data Protection Agreements (DPAs) must be active with the cloud provider to legally designate them as a 'School Official' under FERPA?
24. Does the university's standard FERPA policy require a formal Institutional Privacy Review or a specific compliance sign-off before a department can shift a student-facing service from local infrastructure to a cloud deployment?
