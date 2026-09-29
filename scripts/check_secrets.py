#!/usr/bin/env python3
"""Fail when a tracked file contains credential material or a live RAC invite."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    "",
    ".cff",
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
PATTERNS = (
    ("live SharedNet token", re.compile(r"\brit_(?!REDACTED\b)[A-Za-z0-9_-]{12,}")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT
    ).decode("utf-8", errors="surrogateescape")
    return [ROOT / name for name in output.split("\0") if name]


def main() -> int:
    findings: list[str] = []
    for path in tracked_files():
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(ROOT)}:{line}: {label}")
    if findings:
        print("Potential secrets found in tracked files:", file=sys.stderr)
        print("\n".join(findings), file=sys.stderr)
        return 1
    print("Tracked-tree secret check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
