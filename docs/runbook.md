# Runtime AI Scientist Public Runbook

This runbook describes how to prepare, execute, score, and archive one
ResearchClawBench episode from a source checkout. The examples intentionally
contain no real endpoints, credentials, SharedNet invites, machine addresses,
or private filesystem paths.

## Supported scope

| Host | Compose service | CLI `--host` |
|---|---|---|
| ARK | `ark` | `ark` |
| Agent Laboratory | `agent-laboratory` | `agent_laboratory` |
| EvoScientist | `evo-scientist` | `evo_scientist` |

The supported condition ladder is N0 through R3:

- **N0:** the host's complete native lifecycle, without SharedNet or the RAC
  phase loop.
- **R1:** N0's fixed native successor order with SharedNet communication.
- **R2:** R1 plus shared runtime capability selection.
- **R3:** R2 plus scoped work contracts and artifact-grounded advisory
  verification.

An R3 verification verdict is recorded and supplied to the next selected agent.
It does not roll back the workspace, force a retry, or stop the episode.

## 1. Install and run offline checks

From the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/check_secrets.py
```

On PowerShell, activate the environment with
`.venv\Scripts\Activate.ps1`.

These checks do not call a model. Long-running host execution is intended for
a Linux system with Docker Compose.

## 2. Materialize the frozen upstream revisions

```bash
python3 scripts/bootstrap.py \
  --only ark \
  --only agent_laboratory \
  --only evo_scientist \
  --only researchclawbench

rac-ai-scientist verify-upstreams \
  --only ark \
  --only agent_laboratory \
  --only evo_scientist \
  --only researchclawbench
```

Do not modify a pinned host or benchmark checkout to make a run pass. Provider
adaptation and experiment policy belong in this integration repository.

## 3. Configure private settings

Copy `.env.example` to `.env` and provide the evaluated-model and judge
configuration locally. The repository ignores `.env`.

Never print or commit provider keys, private endpoints, or SharedNet invites.
R1–R3 require a fresh SharedNet Room for every formal cell; store that cell's
Room configuration in the prepared task's `.env`. N0 neither needs nor reads
SharedNet configuration.

## 4. Prepare a target-free task bundle

Choose a task and create a unique prepared directory:

```bash
export REPO="$(pwd)"
export TASK=Math_000
export STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
export PREPARED_TASK="$REPO/prepared_tasks/${TASK}_${STAMP}"
export RUN_ROOT="$REPO/runs"

rac-ai-scientist prepare-task \
  --task-dir "$REPO/upstreams/researchclawbench/tasks/$TASK" \
  --output "$PREPARED_TASK"

rac-ai-scientist check-workspace "$PREPARED_TASK"
```

Never mount the full ResearchClawBench task into an evaluated host. The full
task contains `target_study/`, which is reserved for the external scorer.

For R1–R3, edit the prepared task's private environment file:

```bash
vim "$PREPARED_TASK/.env"
```

Use placeholders only in documentation:

```dotenv
SHAREDNET_ROOM_ID=rom_example
SHAREDNET_INVITE='ROOM=rom_example TOKEN=rit_REDACTED BASE=https://www.sharednet.ai'
SHAREDNET_BASE_URL=https://www.sharednet.ai
```

The Room ID must match the Room encoded in the invite. Only the non-secret Room
ID may appear in episode provenance.

## 5. Build and run the zero-model preflight

Select one matching service and host ID. This example uses Agent Laboratory:

```bash
export SERVICE=agent-laboratory
export HOST=agent_laboratory

docker compose build "$SERVICE"
test "$?" -eq 0

docker compose run --rm "$SERVICE" \
  doctor-host --host "$HOST" </dev/null

docker compose run --rm "$SERVICE" \
  check-workspace /input/task </dev/null
```

Do not start a paid run unless the image build and both preflight checks finish
successfully.

## 6. Start an episode

The following budget is an example, not a universal benchmark budget. Within a
host/task/seed comparison, N0–R3 must use the same model, inputs, permissions,
tools, and lifecycle budget. Router and verifier usage is charged to the same
budget.

```bash
export CONDITION=R3
export SEED=0
export EPISODE="${HOST}-${TASK,,}-${CONDITION,,}-s${SEED}-${STAMP}"
export CELL_RUN_ROOT="$RUN_ROOT/cells/$EPISODE"
mkdir -p "$CELL_RUN_ROOT"
export RAC_IMAGE_ID="$(docker compose images -q "$SERVICE")"

docker compose run --rm "$SERVICE" run-one \
  --host "$HOST" \
  --condition "$CONDITION" \
  --task-dir /input/task \
  --sharednet-env-file /input/task/.env \
  --run-root /runs \
  --episode-id "$EPISODE" \
  --seed "$SEED" \
  --max-cost-usd 25 \
  --max-input-tokens 60000000 \
  --max-output-tokens 1300000 \
  --max-agent-calls 900 \
  --max-wall-seconds 21600 \
  --max-hops 14
```

For N0, omit `--sharednet-env-file`. Use `tmux` for long runs. A temporarily
quiet log does not prove that the process is stuck; inspect the container and
the final episode record as well:

```bash
docker ps --format '{{.ID}} {{.Names}} {{.Status}}'
test -f "$CELL_RUN_ROOT/$EPISODE/episode.json" && \
  python3 -m json.tool "$CELL_RUN_ROOT/$EPISODE/episode.json"
```

Every retry must use a new episode ID. Preserve failed episodes for audit unless
an explicit data-retention policy requires their removal.

## 7. Score the episode

The scorer runs outside the evaluated host and is the only component allowed to
read benchmark target material:

```bash
docker compose build scorer
test "$?" -eq 0
export SCORER_IMAGE_ID="$(docker compose images -q scorer)"

docker compose run --rm scorer score-episode \
  --episode-dir "/runs/$EPISODE" \
  --benchmark /opt/benchmark
```

A legitimate numeric zero differs from an incomplete score. Each scoring run
is appended under `scores/`; `score.json` is the compatibility view of the
latest selected attempt. A missing report,
judge HTTP error, or response-parse failure must produce `total_score: null`
with an explicit error; it must never be silently converted to zero.

## 8. Archive reproducibility evidence

Preserve the episode record, `score.json`, all `scores/` attempts, coordination ledger, logs, report, code, and
outputs. Always exclude generated `.conda_env/` runtimes:

```bash
mkdir -p "$REPO/exports"
tar --exclude='*/.conda_env' \
  -czf "$REPO/exports/${EPISODE}.tar.gz" \
  -C "$CELL_RUN_ROOT" "$EPISODE"
```

## Release checks

Before publishing a revision:

```bash
python scripts/check_secrets.py
python -m compileall -q src tests scripts
python -m unittest discover -s tests -v
git diff --check
```

If a real token has ever entered Git history, deleting it from the current tree
is insufficient. Revoke it first, then coordinate any history rewrite with all
maintainers and users of existing clones or forks.
