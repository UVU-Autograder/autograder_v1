## Summary of Changes

A concise description of the changes proposed in this pull request and the rationale behind them.

## Related Issue

Closes #<!-- insert issue number here -->

## Type of Change

- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing behavior to change)
- [ ] Architecture / Refactoring (no external behavior change)
- [ ] Documentation / Configuration update

## Verification & Testing

Explain how these changes were tested and verified:
- [ ] Backend test suite: `cd backend && python -m pytest tests/`
- [ ] Frontend build & tests: `cd frontend && npm test && npm run build`
- [ ] Code formatting & linting: `ruff check .` / `npm run lint`
- [ ] Deployment / Release audit: `python scripts/audit_release_readiness.py`

## Pre-Merge Checklist

- [ ] **No Secrets:** Confirmed no API keys, tokens, or environment passwords are committed.
- [ ] **FERPA & Privacy:** Verified no student code, real names, or Canvas archives are included in fixtures or commits.
- [ ] **Schema Parity:** If API routes changed, ran `python backend/scripts/generate_openapi.py` to keep specs synchronized.
- [ ] **Documentation:** Updated relevant documentation in `docs/` where applicable.
