# Security Policy

## Reporting

Do not open a public issue for a suspected vulnerability. Send a private GitHub security advisory with affected version, reproduction, impact, and suggested mitigation. This portfolio repository has no production SLA, but reports should be acknowledged promptly.

## Secrets and authentication state

- Supply `JWT_SECRET` through environment or a deployment secret manager; `.env` is ignored.
- Never commit bearer/refresh tokens, cookies, Playwright storage state, traces containing credentials, or real user data.
- CI uses ephemeral databases and generated secrets. Sample values are deliberately non-production.
- The local suite-execution endpoint requires a separate execution token and only accepts server-defined command allow-list entries.
- Refresh records contain a SHA-256 JTI digest, not the token. Passwords use salted PBKDF2-HMAC-SHA256.

## Threat model

Protected assets are user identity, role assignments, refresh-token families, profile data, test evidence, and defect artifacts. Relevant threats include credential stuffing, token theft/replay, broken access control, malicious requirement content, command injection through runners, artifact secret leakage, dependency compromise, and unsafe agent actions.

Controls include password policy, bounded login rate limiting, signed short-lived access tokens, refresh rotation/family revocation, server-side RBAC, strict JWT algorithm selection, Pydantic validation, `yaml.safe_load`, an allow-listed runner with no arbitrary command input, deterministic AI checks, explicit approval signals for mutating tools, CodeQL, Dependabot, and opt-in ZAP.

Bearer tokens in session storage make CSRF inapplicable to the current API pattern but make XSS prevention critical. If browser tokens move to cookies, use `Secure`, `HttpOnly`, and `SameSite`, add CSRF tokens, and verify cookie scope. Avoid persisting browser auth state.

## Known limitations

- The local rate limiter is per process and resets on restart. Production requires a shared atomic store such as Redis.
- SQLite and synchronous execution are not designed for multi-runner scale.
- HS256 uses one shared secret. A production identity provider and asymmetric verification are preferred.
- Access tokens are stateless and remain valid until expiry after logout; short TTL limits exposure. A denylist/introspection service is a planned production option.
- Defect flags intentionally weaken behavior. They default off and configuration refuses them in production.
- The demo UI has no CSP hardening and is not intended for internet exposure.

## Local ZAP

With the SUT running: `docker run --rm --network host -v "$PWD:/zap/wrk/:rw" ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://localhost:8000 -r reports/zap.html`. Review findings before treating a baseline failure as an application defect.
