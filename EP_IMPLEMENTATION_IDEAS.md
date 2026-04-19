# UVU Autograder v1 — Implementation Ideas

**Author:** Easton Parkhurst  

This document is a structured brain dump of the current code autograding market, including competitive analysis, personal observations, and implementation ideas for Utah Valley University's `autograder_v1` project.

---

## Current Market Competition & Analysis

### Gradescope
- Diff view for similarity detection and AI copy/paste responses
- Ability to print similarity reports
- Separation of failed tests from correct outputs
- Upload curriculum documents directly for manual grading, autograding, or hybrid workflows
- Easy copy/paste into LMS tools without excessive context switching
- Machine learning–based detection of class learning patterns and struggle points

---

## Easy Integrations (Minimize Development Effort)

- **Stanford MOSS (Plagiarism Detection)**  
  https://theory.stanford.edu/~aiken/moss/

- **JPlag (Alternative Plagiarism Detection)**  
  https://helmholtz.software/software/jplag

---

## Current Market Gaps & Headwinds

### Missing Capabilities
- Contextual LLM feedback tied to course-specific curriculum (e.g., CS1400) is largely absent in the market
- No strong commercial implementations of curriculum-aware AI grading

### Technical Challenges
- Python as a base language is fine, but OS/file output inconsistencies often break parsing
- Edge case handling is weak in most systems (test-case-only approaches are insufficient)
- Gradescope pitted against inefficient code can cause a 0% grade to be generated (~800MB buffer issues)

### Grading Limitations
- Over-reliance on unit tests can incorrectly award 100% to broken code
- Partially correct solutions often receive 0% (e.g., minor floating point or indexing mistakes)
- Formatting/whitespace issues frequently cause false negatives
- False negatives reduce instructor trust in autograding systems

### LLM Opportunities
- LLM inference is effectively required to reduce manual grading overhead
- Annotated code feedback (e.g., inline comments, strikethrough suggestions)
- Summary reports that help students understand mistakes
- Curriculum- and lesson-specific feedback at submission time

### System Design Considerations
- If not using RAG, a comprehensive test suite must fully cover the curriculum
- AI audit trails are necessary due to nondeterministic grading behavior
- Security risks: past Docker-based systems (e.g., Gradescope) have been exploited by students modifying container payloads

### Instructor Experience
- PDF report generation or plaintext output for LMS (e.g., Canvas) is essential
- Copy/paste–friendly grading summaries improve workflow efficiency
- Lack of DevOps integration and poor UX are major adoption barriers