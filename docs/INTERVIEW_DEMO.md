# Five-minute interview demo

## Before the call

Run `docker compose up --build`, open the dashboard at `http://localhost:8501`, and keep the demo app (`:8000/docs`), QualityPilot API (`:8001/docs`), and a recent GitHub Actions run available. Do not enable more than one defect flag at once.

## 0:00–0:45 — Requirement intake

Open **Requirement Lab**, select YAML, and use `AUTH-003` from `requirements/user_stories.yaml`. Generate cases. Point out the Pydantic-enforced fields, deterministic offline behavior, identity/security variant, and requirement IDs carried into tags.

## 0:45–1:20 — Gherkin and traceability

Scroll to generated Gherkin. Show feature/scenario tags and the reusable Behave steps under `tests/bdd`. Mention duplicate-step detection in CI.

## 1:20–2:10 — API and identity automation

Run `.venv/bin/pytest tests/api tests/identity -q`. In the API docs, show login, refresh, logout, protected profile, and admin audit. Explain signed short-lived access tokens, one-way refresh JTI storage, rotation/replay rejection, family revocation, malformed/expired-token checks, and server-side RBAC.

## 2:10–2:45 — Playwright evidence

Run `npm test` or open the latest Playwright CI artifact. Show the Page Object Model, role/label locators, mobile project, accessibility check, and trace/screenshot/video retention. Mention that the visual baseline is intentionally experimental until reviewed.

## 2:45–3:35 — Controlled defect and analysis

Stop the SUT, set `DEFECT_DISABLE_REFRESH_ROTATION=true`, restart, then run the refresh identity test. Submit its error and pass/fail history to `/api/failures/analyze`. Explain why flags default off and production config rejects them. Reset the variable immediately afterward.

## 3:35–4:20 — Flaky signal and defect report

Post alternating outcomes for one test to `/api/executions`, then open **Flaky Tests**. Show the transparent transition/retry score and stabilization advice. Submit the failure to `/api/defects`; open its Markdown, JSON, and Jira-compatible payload. Note that the Jira endpoint is mock-only and makes no external write.

## 4:20–5:00 — AI quality and CI/CD

In **AI Quality**, ask about refresh rotation, then try an instruction-injection prompt. Show citations, refusal, schema/groundedness checks, tool allow-list, and approval gate. Finish with GitHub Actions artifacts and CodeQL/Dependabot/ZAP configuration. Be explicit that PostgreSQL, distributed runners, Kafka infrastructure, and real defect-tracker writes are roadmap items.

