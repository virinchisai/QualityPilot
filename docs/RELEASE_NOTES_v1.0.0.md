# QualityPilot v1.0.0 — Portfolio MVP

QualityPilot v1.0.0 is the first portfolio-ready release of the local-first enterprise TestOps platform.

## Release highlights

- Requirement ingestion from Markdown, YAML, JSON, plain text, Gherkin, and OpenAPI.
- Pydantic-validated test-case and Gherkin generation with traceability.
- JWT access and rotating refresh tokens, revocation, logout invalidation, password policy, rate limiting, and RBAC.
- pytest/HTTPX/Schemathesis API and identity tests, Playwright Page Objects, Behave, Cucumber.js compatibility, and a Selenium smoke adapter.
- SQLite execution history, deterministic failure classification, flaky-test scoring, evidence manifests, and persistent defect reports.
- Rally-compatible CSV/JSON test export, requirements traceability matrix, and configurable release quality gates.
- Deterministic AI-agent quality evaluation, event-order/duplicate/DLQ validation, Prometheus metrics, Docker Compose, CodeQL, Dependabot, and ZAP configuration.
- Interactive Streamlit workflow and reproducible demo GIF.

## Verified evidence

- 49 Python tests discovered: 48 pass by default and one Selenium test is opt-in.
- 4 Behave scenarios with 12 steps.
- 2 Cucumber.js scenarios with 8 steps.
- 9 Playwright Chromium checks: 7 default and 2 opt-in demonstrations.
- CI, CodeQL, and Docker build completed successfully before release preparation.

## Release assets and guides

- [Architecture overview](../ARCHITECTURE.md)
- [Demo GIF](assets/qualitypilot-demo.gif)
- [Desktop and mobile screenshots](assets/)
- [Sample Markdown defect](../reports/sample-defect.md)
- [Sample JSON defect](../reports/sample-defect.json)
- [Five-minute interview demo](INTERVIEW_DEMO.md)
- [Accurate resume bullets](RESUME_BULLETS.md)
- GitHub Actions artifacts from the tagged commit

## Known limitations

This release is designed for local demonstration. SQLite, synchronous runners, process-local rate limiting, HS256 shared-secret signing, the mock Jira endpoint, simulated event streams, and manually triggered ZAP are not production infrastructure. PostgreSQL, distributed workers, real defect-tracker writes, Kafka infrastructure, asymmetric identity-provider integration, and cloud deployment remain roadmap items.
