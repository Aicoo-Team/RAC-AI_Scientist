# Security policy

## Reporting a vulnerability

Do not disclose credentials, live SharedNet invites, answer leakage, or other
sensitive findings in a public issue. Use GitHub's private vulnerability
reporting flow for this repository. If that flow is unavailable, contact a
maintainer privately before sharing exploit details.

Include the affected revision, impact, minimal reproduction, and whether any
credential or benchmark answer may have been exposed. Never include a live key
or token in the report; provide only a redacted identifier.

## Secrets and benchmark integrity

- Store provider and judge credentials only in ignored local `.env` files or a
  secret manager.
- Use a fresh SharedNet Room for every formal R1–R3 cell.
- Never expose ResearchClawBench `target_study/` to an evaluated host.
- Treat any credential committed to Git history as compromised even after the
  current file is corrected: revoke it first, then coordinate history cleanup.
