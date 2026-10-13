# Security Policy — UVU Autograder

The UVU Autograder team takes software security, student privacy, and infrastructure isolation seriously. We welcome responsible vulnerability disclosures from researchers, students, and educators.

---

## Supported Versions

Security updates and patches are actively provided for the following releases:

| Version | Supported |
| :--- | :--- |
| `main` branch (latest) | :white_check_mark: |
| Pilot Releases (`v0.x`) | :white_check_mark: |
| Legacy / Deprecated Releases | :x: |

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a potential vulnerability, security bypass, or unintended data disclosure in the UVU Autograder:

1. **GitHub Security Advisory (Preferred):** Navigate to the repository's [Security Advisories](https://github.com/UVU-Autograder/autograder_v1/security/advisories) tab and click **"New draft security advisory"**.
2. **Email Disclosure:** Contact the repository maintainers directly with details:
   - **Email:** `autograder-security@uvu.edu` (or contact project maintainers via university email)
   - **Subject Line:** `[SECURITY DISCLOSURE] UVU Autograder - <Short Description>`

### What to Include in Your Report

To help us triage and resolve the issue quickly, please provide:
- A clear description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions or a minimal proof of concept (PoC).
- The affected component (e.g., sandbox execution, API endpoint, authentication flow).
- Any suggested remediations or mitigations, if known.

### Response & Remediation Commitments

- **Acknowledgment:** We strive to acknowledge vulnerability reports within 48 business hours.
- **Triage & Assessment:** We will confirm the vulnerability, assign severity, and coordinate remediation.
- **Disclosure:** We ask that you adhere to responsible disclosure principles and provide the development team reasonable time to release a patch before publicly disclosing details.

---

## Core Security Invariants

The platform enforces architectural security invariants designed to protect host systems and student privacy:

1. **Untrusted Code Isolation:** All student code executes strictly within isolated sandbox environments (Judge0 / Kata microVMs) subject to memory caps (512 MB default), process limits, CPU quotas, and strict network isolation.
2. **Loopback Service Isolation:** Backing services (PostgreSQL, Redis, Judge0 engine, internal LLM endpoint) bind strictly to `127.0.0.1` and are never exposed directly to external networks. Only the hardened reverse proxy routes traffic.
3. **FERPA & Zero-Retention:** Student execution files, Judge0 tokens, and raw payloads are purged immediately after evaluation. The standalone cleanup worker sweeps the database every 60 seconds to enforce a strict 24-hour physical deletion policy.
4. **Audit Logging & Sanitization:** System audit logs redact credentials, tokens, student identifiers, and raw source code from logs.
