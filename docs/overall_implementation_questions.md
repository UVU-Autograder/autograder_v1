# Overall Implementation Questions

## 1. Bulk official-run output format

When the instructor submits the bulk student `.zip`, should the program return feedback or just a Canvas-compatible CSV?

**Jaxon:** For M1, I believe we should only provide feedback when students upload into the sandbox. It is displayed as an HTML document that they can either look at until they have closed out of the page or download. If we can find a way to easily bulk upload feedback to Canvas, we can do that in M1, but I'd recommend HTML files attached to comments for a balance of simplicity and better-than-plaintext formatting.

- PDFs are complicated to generate, but take marginally less effort to open than HTML documents.
- Markdown provides no benefit over HTML, as students will have to use an outside program to display the formatted document either way.

## 2. Teacher/IA review workflow

The teacher/IA workflow is not completely nailed down:

`Upload ZIP of all submissions -> autograding, plagiarism checks, etc. -> ?`

Should there be a manual check on each assignment, where the teacher/IA clicks "accept" through a queue of each assignment and its test outcomes (and maybe AI comments), or should they be able to upload files and download grades directly, with manual review as an optional spot-check for surprising results?
