# Contributing

Use Python 3.11+ (3.12 in CI) and Node 20+. Create a virtual environment, install `.[dev]`, copy `.env.example`, and install Node packages. Keep modules typed and focused, public adapter methods documented, request/response models validated, and security decisions explicit.

Before a pull request, run:

```bash
ruff check .
pytest
python scripts/check_duplicate_steps.py
behave tests/bdd
npm run format:check
npm test
```

PRs should link a requirement or issue, describe risk, list evidence, distinguish implementation from plans, avoid secrets/auth state, and update `TASKS.md`, docs, and samples when behavior changes. Prefer stable accessible Playwright locators and isolated test data. New defect flags must default off and be rejected in production.

