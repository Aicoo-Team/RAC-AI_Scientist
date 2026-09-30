# Contributing

Thank you for improving RAC × AI Scientist.

This is an alpha research integration. Contributions to documentation, offline
tests, host compatibility, and reproducibility are welcome. The supported hosts
are ARK, Agent Laboratory, and EvoScientist; the conditions are N0–R3.

## Choose the right starting point

- Use a **bug report** for an installation, CLI, or runtime failure. Include the
  integration commit, environment, minimal reproduction, and expected behavior.
- Use a **reproducibility report** for an unexpected experiment or scoring
  difference. Follow the [research reporting checklist](docs/research-reporting.md).
- Use a **feature request** to explain a proposed capability and its effect on
  existing experiments. Discuss new hosts or changes to condition semantics
  before investing in a large implementation.
- Small documentation corrections can go directly to a pull request. Search
  existing issues and pull requests first to avoid duplicating work.

Do not put credentials, live SharedNet invites, private endpoints, benchmark
answers, or personal information into issues or pull requests. Read the
[security policy](SECURITY.md) before reporting sensitive findings. Public issue
forms are not a private reporting channel. Follow the [code of conduct](CODE_OF_CONDUCT.md).

## Development setup

Use Python 3.10 or newer. CI currently runs the offline suite on Python 3.10 and
3.12; declaring a minimum version does not mean every platform has been tested.
From a source checkout:

```bash
git clone https://github.com/FORLEMON/RAC-AI_Scientist.git
cd RAC-AI_Scientist
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

PowerShell activation is `.venv\Scripts\Activate.ps1`. Installing dependencies
requires access to a package index or a populated local cache. The following
checks do not call a model and do not require provider credentials or upstream
checkouts:

```bash
python -m unittest discover -s tests -v
python scripts/check_secrets.py
python -m compileall -q src tests scripts
rac-ai-scientist --help
git diff --check
```

For a package build, also install `build` and run `python -m build`, as CI does.
Host image builds and live experiments have separate dependencies; follow the
[public runbook](docs/runbook.md) or [Chinese runbook](docs/runbook.zh-CN.md).
Passing offline tests does not demonstrate that an image builds, a provider is
compatible, or a live experiment completes. State which checks you actually ran.

## Where to make and test a change

| Change area | Main implementation | Relevant offline tests |
|---|---|---|
| Condition semantics, routing, stopping, usage | `conditions.py`, `policy.py`, `runner.py`, `schemas.py` | `test_conditions.py`, `test_policy.py`, `test_runner.py`, `test_usage.py` |
| Host translation and native lifecycle | `hosts/`, `bridge.py`, `configs/hosts/` | `test_bridge.py`, `test_host_registry.py`, `test_manifests.py`, `test_ark_*.py`, `test_agent_laboratory_*.py`, `test_evo_*.py` |
| Benchmark preparation and scoring | `benchmark.py`, `judge.py` | `test_benchmark.py`, `test_judge.py`, `test_score_preflight.py` |
| Artifacts, source records, matrix planning | `artifacts.py`, `provenance.py`, `matrix.py` | `test_artifacts.py`, `test_provenance.py`, `test_matrix.py` |
| Runtime communication | `sharednet.py` | `test_sharednet.py` |

Implementation paths above are relative to `src/rac_ai_scientist/`, except
`configs/hosts/`; test paths are relative to `tests/`. Run a focused group during
development, for example:

```bash
python -m unittest discover -s tests -p 'test_agent_laboratory_*.py' -v
```

Before submission, run the full offline suite. Add a regression test when
changing behavior; documentation-only changes can be checked for correct
commands, links, and consistency. Keep policy in the shared runner and native
translation in host bridges; see the [architecture](docs/architecture.md).

Source pins in `upstream.lock.json` do not lock the entire runtime environment.
For a proposed upstream update, record the old/new commits, source-tree hashes,
license changes, affected capabilities, and validation performed. Do not modify
a pinned host or benchmark checkout just to make a test pass. Keep provider
adaptation in the integration layer and disclose its effect on native behavior.

## Pull requests

1. Create a topic branch in your fork or checkout and keep the change focused.
2. Explain the problem, the resulting behavior, and any linked issue. Include a
   minimal before/after example when it clarifies the fix.
3. List the validation commands and results, plus checks not run. Never imply a
   paid experiment ran when validation only used mocks or offline tests.
4. Describe changes to source pins, dependencies, images, schemas, prompts,
   budgets, preprocessing, host behavior, or scoring. Explain whether existing
   episode records or comparisons are affected.
5. Update affected documentation. If the PR makes an empirical claim, supply the
   evidence in the [research reporting checklist](docs/research-reporting.md).

Do not commit generated runs, archives, `.conda_env/`, or private configuration.
Use small synthetic fixtures in tests. Redact logs before attaching them; an
ignore rule or a passing secret scan does not prove an attachment is safe.

Preserve third-party copyright and license notices, and identify the source and
license of any code or data you adapt. This integration uses the [MIT license](LICENSE);
independent upstream projects retain their [own terms](NOTICE.md). Do not invent
author names or citations when updating project metadata.

Changes for retired adapters should be proposed separately with a maintenance
and reproducibility plan. A pull request can document incomplete work and known
limitations; it should not claim a release, replication, or performance gain
without the corresponding evidence.
