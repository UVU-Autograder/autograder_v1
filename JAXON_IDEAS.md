# UVU Autograder v1 — Project Vision & Architecture

## 1. Existing Components & Libraries

To maintain a "Simplicity-First" approach, we will leverage established open-source tools for the technical heavy lifting. We are currently evaluating two primary options for the core execution engine.

### Execution Engine (Evaluating Options)

We are considering either a standalone API or a direct Python library to handle the code sandboxing.

**Option A: Piston (High-performance API)**

- **Pros:** Supports 100+ languages; stateless by design (every run starts fresh); easy to scale horizontally as a separate service on Railway.
- **Cons:** Adds a separate infrastructure component to manage; requires internal API security to prevent unauthorized access.

**Option B: Autograder-sandbox (Python Library)**

- **Pros:** Built specifically for academic autograding (University of Michigan); integrates directly into our Django logic as a Python package; tighter control over the container lifecycle.
- **Cons:** More complex initial configuration for Docker networking; supports fewer languages out of the box compared to Piston.

---

### Other Core Libraries

- **Constraint Checking:** **Python `ast` library**. Used for static analysis to walk the code tree and programmatically detect forbidden functions (e.g., `sort()`) or imports before the code is executed.
- **Plagiarism Detection:** **Stanford Python `mosspy` library**. A lightweight wrapper for MOSS, providing industry-standard similarity reports with minimal local effort.
- **Testing Engine:** **Python `pytest` library**. Simplifies test discovery and provides structured error reports that can be easily fed into the AI feedback agent.
- **Deployment & Integration:**
  - **Docker:** Wrap the entire application to ensure environment consistency and eliminate "works on my machine" issues.
  - **Python `canvasapi` library:** For programmatic interaction with UVU’s Canvas instance in later phases.

- **Grading Specifications:**
  - **Submitty `config.json`:** We will adopt this proven schema for defining test cases, point values, and resource limits.

---

## 2. Custom Development (The "Glue")

Our internal development will focus on the unique UVU workflow:

- **Instructor Dashboard:** A minimalist Django portal for bulk-uploading Canvas ZIPs, reviewing similarity reports, and auditing grades.
- **Feedback Agent (LLM):** A prompt-engineered wrapper (GPT-4o-mini) that translates technical failures into pedagogical hints without giving away the solution.
- **Canvas ZIP Parser:** A utility to extract bulk-downloaded submissions and map filenames (e.g., `jaxonlarsen_12345_assignment1.py`) to student database records.

---

## 3. Tech Stack

- **Backend Framework:** **Django**. Provides built-in authentication, an automatic Admin panel for instructors, and robust database management in a single repository.
- **Database:** **PostgreSQL**. The relational structure is ideal for mapping students to assignments and submissions. We will store student code as `TEXT` blobs or JSON to keep the initial implementation simple and searchable.
- **Hosting:** **Railway** for the web application, database, and execution engine.

---

## Backlog, Questions

## 4. Questions & Roadblocks

- **AI Hallucinations:** How do we handle cases where the AI feedback contradicts the actual test results?
- **Resource Limits:** What are the hard caps for **CPU time** and **RAM** to prevent infinite loops from hanging the server?
- **Persistence Strategy:** Should we store code as `TEXT` blobs in the database for simplicity, or utilize S3/Railway Volumes for better long-term scalability?
