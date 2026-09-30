# Research reporting checklist

Use this checklist when reporting a reproduction, benchmark comparison, or
change that affects experimental interpretation. It describes evidence that
authors should supply, not a guarantee that the current software captures or
enforces every item. If a record is missing, say so and limit the claim.

Offline tests establish the behavior covered by those tests. They do not show
that RAC improves scientific quality, that every live host works, or that a
comparison is fair. Empirical claims need traceable runs and analysis.

## Define the comparison before inspecting outcomes

- Freeze the task IDs, seeds, hosts, conditions, exclusions, and intended number
  of attempts. Archive the configuration and expanded plan with their hashes.
- Define the score, aggregation, treatment of failures and missing scores, and
  analysis method before comparing outcomes. Disclose later changes and why
  they were made.
- Describe the actual N0 and R1–R3 execution paths. N0 invokes the host's native
  lifecycle; R1–R3 use the capability-level runner. Record scheduler, prompt,
  tool, permission, model, and preprocessing differences. Do not attribute an
  observed difference solely to one mechanism without addressing other changes.
- Record the scope of seed control. A local random seed does not guarantee
  deterministic provider responses, concurrent scheduling, or external tools.
- Report stopping rules separately from verification verdicts, including native
  completion, hop limits, budget exhaustion, and errors. Check whether each
  condition actually obeyed the intended stopping rule.

The current R3 verifier checks artifact changes, presence, size, nonempty
outputs, and invocation status. It does not validate the correctness of
scientific claims, citations, or statistics. Its `supported` verdict is an
advisory result of those limited checks, not evidence of scientific validity.

## Preserve source and environment evidence

| Layer | Evidence to retain |
|---|---|
| Integration | Exact Git commit, whether the checkout was dirty, and a source digest or patch covering local changes |
| Host and benchmark | Repository URLs, exact revisions, source-tree hashes, and any local changes or fork relationship |
| Runtime | Image ID/digest, operating system and architecture, Python version, resolved package/system dependencies, and downloaded model/resource revisions |
| Evaluated model | Provider identity, model/deployment identifier, available model version, sampling settings, and request adapter configuration |
| Inputs | Task IDs, prepared bundle hashes, preprocessing rules and overrides, and evidence that target material was excluded from host inputs |

`upstream.lock.json` freezes upstream source snapshots. It does not freeze the
complete runtime: current Docker recipes contain moving image tags, dependency
resolution, and downloaded resources. An environment captured after a build
helps identify that build; it is not by itself a lockfile for rebuilding it.

Keep credentials, private endpoint URLs, and SharedNet invites out of public
records. Record non-secret provider/deployment descriptors sufficient to explain
the setup; disclose any information withheld and resulting replication limits.

## Account for every attempt and budget

- Keep the planned denominator, every started attempt, terminal state, and
  reason for failure, exclusion, cancellation, or missing evidence. Preserve
  failed and budget-exhausted episodes. Retain old attempts when retrying.
- Give each attempt a unique episode ID. Map retries to the original planned
  task/host/condition/seed cell and explain how retries enter the analysis.
- Report configured limits and observed usage separately: cost, input/output
  tokens, agent calls, wall time, and hops. Include router/verifier usage where
  applicable, pricing assumptions, estimates, and unknown usage.
- Explain where each limit is enforced and any overrun or uninstrumented host
  call. Equal configured numbers alone do not establish equal enforced budgets.
- Retain reports, code, outputs, artifact hashes, coordination traces, and
  redacted logs. State missing or unverifiable artifacts explicitly.

## Make scoring traceable

- Record benchmark/scorer revision, scoring configuration, judge provider,
  model/deployment, available version, sampling settings, and concurrency.
- Associate each scoring attempt with its episode ID, exact terminal report
  hash, timestamp, and outcome. Retain earlier scoring attempts when retrying
  or changing judge configuration; disclose which attempt enters the analysis.
- Distinguish a valid numeric zero from an incomplete or failed score. Preserve
  the raw status and error when a score is absent, and state the analysis rule
  for missing values. Do not silently replace missing scores with zero or drop
  failed episodes from the denominator.
- Keep benchmark target material inside the authorized scoring environment.
  Public issue reports and fixtures should not reproduce answers or secrets.

## Support the result with an analysis artifact

- Publish paired per-task/seed results where the design is paired, the number
  of independent units, aggregation code, effect sizes, and uncertainty. Explain
  resampling or statistical assumptions; avoid treating dependent attempts as
  independent replications.
- Disclose missing cells, all exclusions, retries, failed episodes, and
  sensitivity to their treatment alongside summary scores.
- State the tested hosts, tasks, models, budgets, and environment. Limit
  conclusions to that scope and separate observed results from hypotheses.
- Cite this integration at the exact tested commit and credit the original
  hosts, experiment forks, and benchmark separately. Do not add an author,
  paper, DOI, or release claim without verified metadata.

Before sharing an archive, review its contents for credentials, private inputs,
benchmark answers, third-party distribution terms, and generated runtime
directories. The [runbook](runbook.md) explains episode operation and archiving;
the [contribution guide](../CONTRIBUTING.md) explains how to submit a change.
