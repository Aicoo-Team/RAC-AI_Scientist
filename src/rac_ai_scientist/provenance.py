from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def _is_generated_package_metadata(relative: Path) -> bool:
    return any(part.endswith((".egg-info", ".dist-info")) for part in relative.parts)


def tree_hash(root: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    count = 0
    size = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if (
            not path.is_file()
            or IGNORED_PARTS.intersection(relative.parts)
            or _is_generated_package_metadata(relative)
            or path.suffix in IGNORED_SUFFIXES
        ):
            continue
        file_digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                file_digest.update(chunk)
        encoded_path = relative.as_posix().encode("utf-8")
        digest.update(len(encoded_path).to_bytes(8, "big"))
        digest.update(encoded_path)
        digest.update(file_digest.digest())
        count += 1
        size += path.stat().st_size
    return digest.hexdigest(), count, size


def file_hash(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_provenance(root: Path) -> dict[str, Any]:
    """Return revision and dirty state without failing outside a Git checkout."""

    result: dict[str, Any] = {"revision": None, "dirty": None}
    try:
        result["revision"] = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        status = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        result["dirty"] = bool(status.strip())
    except (OSError, subprocess.CalledProcessError):
        pass
    return result


def _fingerprint(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def integration_provenance(root: Path) -> dict[str, Any]:
    source_root = root / "src" / "rac_ai_scientist"
    source_hash, files, byte_count = tree_hash(source_root)
    return {
        **git_provenance(root),
        "source_tree_sha256": source_hash,
        "source_file_count": files,
        "source_byte_count": byte_count,
    }


def runtime_provenance(*, model: str | None = None) -> dict[str, Any]:
    image_identity = next(
        (
            os.environ.get(name)
            for name in ("RAC_IMAGE_DIGEST", "RAC_IMAGE_ID", "HOST_IMAGE_DIGEST")
            if os.environ.get(name)
        ),
        None,
    )
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "image_identity": image_identity,
        "image_identity_source": "environment" if image_identity else "unavailable",
        "model": model,
        "api_base_sha256_16": _fingerprint(os.environ.get("AGENT_API_BASE")),
        "api_version": os.environ.get("AGENT_API_VERSION") or os.environ.get("OPENAI_API_VERSION"),
    }


def score_provenance(root: Path, benchmark: Path, report: Path) -> dict[str, Any]:
    benchmark_git = git_provenance(benchmark)
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "integration": integration_provenance(root),
        "benchmark": benchmark_git,
        "report_sha256": file_hash(report),
        "scorer_image_identity": os.environ.get("SCORER_IMAGE_ID") or None,
        "judge": {
            "provider": os.environ.get("JUDGE_PROVIDER", "default"),
            "model": os.environ.get("JUDGE_MODEL_NAME"),
            "api_version": os.environ.get("JUDGE_API_VERSION"),
            "api_base_sha256_16": _fingerprint(os.environ.get("JUDGE_API_BASE")),
            "max_completion_tokens": os.environ.get("JUDGE_MAX_COMPLETION_TOKENS"),
            "max_workers": os.environ.get("JUDGE_MAX_WORKERS"),
        },
    }
