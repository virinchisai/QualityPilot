# Implementation Plan

## Phase 0 — Planning

Define architecture, delivery states, directory boundaries, risks, and verification gates.

Exit gate: documents and importable package skeleton exist.

## Phase 1 — Foundation

Build the FastAPI SUT, SQLAlchemy persistence, JWT access/rotating refresh tokens, RBAC, rate limiting, profile UI/API, defect flags, Docker Compose, and baseline CI. Add API, identity, and Playwright coverage.

Exit gate: health succeeds; automated authentication and RBAC tests pass; Docker images build.

## Phase 2 — Quality Platform

Implement requirement parsing for the supported formats, validated test-case generation, Gherkin output, an allow-listed execution orchestrator, evidence manifests, execution history, traceability, Behave features, API routes, and Streamlit views.

Exit gate: a sample requirement produces validated cases and Gherkin; results persist and appear through API/dashboard.

## Phase 3 — Intelligence

Implement deterministic failure classification, transition-based flaky scoring, defect serialization, and optional Ollama summaries behind provider interfaces.

Exit gate: unit tests cover classifiers, score edge cases, and every report format.

## Phase 4 — Enterprise extensions

Add deterministic AI-agent evaluation, OpenAPI contract testing, axe/visual examples, Locust, mock stream validation, security workflows, and a mock Jira payload endpoint.

Exit gate: examples execute locally or are explicitly labeled experimental with exact commands.

## Phase 5 — Polish

Complete sample artifacts, interview script, accurate resume bullets, operating/security docs, screenshots when generated, and release notes.

Exit gate: clean install and full documented verification succeed; implemented/experimental/planned claims match code.

## Delivery risks and controls

- Browser availability: API suites remain independent; Playwright install command is documented.
- Secret leakage: `.gitignore`, example-only secrets, CI secret generation, and no stored browser auth state.
- Demo vulnerabilities: flags default off and cannot start in production.
- Flaky statistics: label scores heuristic and expose the history used.
- External LLM availability: deterministic adapter is the default and Ollama failures degrade cleanly.

