# Contributing

Thank you for improving RAC × AI Scientist.

## Development setup

Use Python 3.10 or newer from a source checkout:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/check_secrets.py
```

PowerShell activation is `.venv\Scripts\Activate.ps1`.

## Pull requests

- Keep policy in the shared runner and host translation in host bridges.
- Add or update offline tests for behavior changes.
- Do not modify pinned benchmark or host checkouts to make a test pass.
- Do not commit generated runs, archives, `.conda_env/`, credentials, provider
  endpoints, SharedNet invites, or tokens.
- Describe reproducibility-impacting dependency, image, schema, and budget
  changes in the pull request.
- Run the full offline test suite and `git diff --check` before submission.

The supported host matrix is ARK, Agent Laboratory, and EvoScientist. Changes
for retired adapters should be proposed separately with a clear maintenance and
reproducibility plan.
