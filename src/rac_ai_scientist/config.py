from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .conditions import Condition


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class DoctorFinding:
    level: str
    message: str


def load_config(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON experiment config: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("experiment config must be a JSON object")
    return data


def validate_config(data: dict[str, Any], root: Path) -> list[DoctorFinding]:
    findings: list[DoctorFinding] = []
    required_top_level = {
        "schema_version",
        "experiment_id",
        "hosts",
        "conditions",
        "tasks",
        "seeds",
        "repeats",
        "max_parallel_episodes",
        "model",
        "budget",
        "paths",
    }
    missing = sorted(required_top_level - data.keys())
    if missing:
        findings.append(DoctorFinding("ERROR", "missing required fields: " + ", ".join(missing)))
    if data.get("schema_version") != 1:
        findings.append(DoctorFinding("ERROR", "schema_version must be 1"))
    if not isinstance(data.get("experiment_id"), str) or not data.get("experiment_id", "").strip():
        findings.append(DoctorFinding("ERROR", "experiment_id must be a nonempty string"))

    def require_unique_list(name: str, *, allow_empty: bool = False) -> list[Any]:
        value = data.get(name)
        if not isinstance(value, list):
            findings.append(DoctorFinding("ERROR", f"{name} must be a list"))
            return []
        if not value and not allow_empty:
            findings.append(DoctorFinding("ERROR", f"{name} must not be empty"))
        try:
            unique = len(set(value)) == len(value)
        except TypeError:
            unique = False
        if not unique:
            findings.append(DoctorFinding("ERROR", f"{name} must contain unique scalar values"))
        return value

    try:
        raw_conditions = require_unique_list("conditions")
        conditions = [Condition.parse(item) for item in raw_conditions]
    except (TypeError, ValueError) as exc:
        findings.append(DoctorFinding("ERROR", str(exc)))
        conditions = []
    if not conditions:
        findings.append(DoctorFinding("ERROR", "at least one condition is required"))

    hosts = require_unique_list("hosts")
    if any(not isinstance(item, str) or not item for item in hosts):
        findings.append(DoctorFinding("ERROR", "hosts must contain nonempty strings"))
        hosts = [item for item in hosts if isinstance(item, str)]
    from .hosts.registry import HOST_IDS

    allowed_hosts = set(HOST_IDS)
    unknown = sorted(set(hosts) - allowed_hosts)
    if unknown:
        findings.append(DoctorFinding("ERROR", f"unknown hosts: {', '.join(unknown)}"))

    tasks = require_unique_list("tasks", allow_empty=True)
    if any(not isinstance(item, str) or not item for item in tasks):
        findings.append(DoctorFinding("ERROR", "tasks must contain nonempty strings"))
    if not tasks:
        findings.append(DoctorFinding("BLOCKED", "task list is empty; freeze CPU-feasible tasks before live runs"))

    seeds = require_unique_list("seeds")
    if any(not isinstance(item, int) or isinstance(item, bool) for item in seeds):
        findings.append(DoctorFinding("ERROR", "seeds must contain only integers"))
    for name in ("repeats", "max_parallel_episodes"):
        value = data.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            findings.append(DoctorFinding("ERROR", f"{name} must be a positive integer"))

    required_budget = {
        "max_provider_cost_usd",
        "max_input_tokens",
        "max_output_tokens",
        "max_agent_calls",
        "max_wall_seconds",
        "max_hops",
    }
    budget = data.get("budget")
    if not isinstance(budget, dict):
        findings.append(DoctorFinding("ERROR", "budget must be an object"))
        budget = {}
    missing_budget = sorted(required_budget - budget.keys())
    if missing_budget:
        findings.append(DoctorFinding("ERROR", "budget is missing limits: " + ", ".join(missing_budget)))
    invalid_budget = sorted(
        key
        for key in required_budget.intersection(budget)
        if (
            not isinstance(budget[key], (int, float))
            or isinstance(budget[key], bool)
            or not math.isfinite(float(budget[key]))
            or budget[key] <= 0
        )
    )
    if invalid_budget:
        findings.append(DoctorFinding("BLOCKED", "live budget is unset or invalid: " + ", ".join(invalid_budget)))
    discrete_budget = {
        "max_input_tokens",
        "max_output_tokens",
        "max_agent_calls",
        "max_hops",
    }
    noninteger_budget = sorted(
        key
        for key in discrete_budget.intersection(budget)
        if not isinstance(budget[key], int) or isinstance(budget[key], bool)
    )
    if noninteger_budget:
        findings.append(
            DoctorFinding(
                "ERROR",
                "discrete budget limits must be integers: " + ", ".join(noninteger_budget),
            )
        )

    model = data.get("model", {})
    if not isinstance(model, dict):
        findings.append(DoctorFinding("ERROR", "model must be an object"))
        model = {}
    model_name = model.get("name")
    if not isinstance(model_name, str) or not model_name.strip() or model_name == "SET_ME":
        findings.append(DoctorFinding("BLOCKED", "evaluated model is not configured"))

    paths = data.get("paths")
    if not isinstance(paths, dict):
        findings.append(DoctorFinding("ERROR", "paths must be an object"))
        paths = {}
    for key in ("benchmark", "upstream_root", "run_root"):
        raw = paths.get(key)
        if not isinstance(raw, str) or not raw.strip():
            findings.append(DoctorFinding("ERROR", f"{key} path is required"))
        elif key != "run_root" and not (root / raw).exists():
            findings.append(DoctorFinding("BLOCKED", f"{key} path does not exist: {raw}"))
    if not findings:
        findings.append(DoctorFinding("OK", "configuration is ready for a dry-run"))
    return findings


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
