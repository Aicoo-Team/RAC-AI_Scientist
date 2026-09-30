# RAC × AI Scientist 公共运行手册

本文说明如何从公开源码准备、运行和评分一个 ResearchClawBench episode。
示例不包含真实 endpoint、密钥、SharedNet invite、机器地址或私有目录。

## 支持范围

| Host | Compose service | CLI `--host` |
|---|---|---|
| ARK | `ark` | `ark` |
| Agent Laboratory | `agent-laboratory` | `agent_laboratory` |
| EvoScientist | `evo-scientist` | `evo_scientist` |

条件只有 N0、R1、R2、R3。N0 运行 host 原生生命周期；R1 增加
SharedNet 通信；R2 增加运行时路由；R3 再增加工作契约和只提供建议的
artifact verifier。R3 verdict 不会回滚工作区或强制停止 episode。

## 1. 安装与离线检查

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/check_secrets.py
```

## 2. 获取冻结的 upstream

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

不要修改冻结的 benchmark checkout。Provider 兼容代码应放在本仓库集成层。

## 3. 配置秘密信息

复制 `.env.example` 为 `.env`，仅在本地填入 provider 和 judge 配置。
`.env` 已被 Git 忽略。不要在命令输出、issue、日志或结果归档中打印密钥和
SharedNet invite。

R1–R3 每个正式 cell 使用新的 SharedNet Room，并把 Room 配置放在本次
prepared task 的 `.env` 中。N0 不需要也不会读取 SharedNet 配置。

## 4. 准备无答案泄漏的 task

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

禁止把含 `target_study/` 的完整 benchmark task 挂载给 evaluated host。

## 5. 构建和零模型 preflight

选择与 host 对应的 `SERVICE` 和 `HOST`：

```bash
export SERVICE=agent-laboratory
export HOST=agent_laboratory
docker compose build "$SERVICE"
docker compose run --rm "$SERVICE" doctor-host --host "$HOST" </dev/null
docker compose run --rm "$SERVICE" check-workspace /input/task </dev/null
```

只有 build 和两项 preflight 都成功后才启动付费运行。

## 6. 启动 episode

下面预算只是示例。比较 N0–R3 时，同一 host/task/seed 必须使用相同模型、
输入、权限、工具和 lifecycle budget。

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

N0 必须省略 `--sharednet-env-file`。长任务建议在 `tmux` 内运行，并同时观察
容器状态和最终 `episode.json`；日志暂时无输出不等于进程停止。

## 7. 评分与归档

```bash
docker compose build scorer
export SCORER_IMAGE_ID="$(docker compose images -q scorer)"
docker compose run --rm scorer score-episode \
  --episode-dir "/runs/$EPISODE" \
  --benchmark /opt/benchmark

mkdir -p exports
tar --exclude='*/.conda_env' -czf "exports/${EPISODE}.tar.gz" \
  -C "$CELL_RUN_ROOT" "$EPISODE"
```

每次评分都会在 `scores/` 下追加不可覆盖的尝试记录，`score.json` 只是指向
最新所选尝试的兼容视图。缺失报告、judge HTTP 错误或解析失败必须表现为
`total_score: null` 和明确错误，不能伪装成合法的 0 分。归档需保留 episode、score、所有评分尝试、ledger、日志、
报告、代码和输出，但必须排除每个工作区的 `.conda_env/`。

## 发布前检查

```bash
python scripts/check_secrets.py
python -m compileall -q src tests scripts
python -m unittest discover -s tests -v
git diff --check
```

若 Git 历史曾包含真实 token，仅删除当前文件不够：必须先撤销 token，再由
维护者决定是否重写历史并协调所有 clone/fork。
