#!/usr/bin/env python3
"""
Delete large `model.safetensors` files from specific model subtrees.

Targets:
  - models/r-series/**/model.safetensors
  - models/thor/thor-1.2/reply-enhancement/**/model.safetensors

This script defaults to dry-run. Use --apply to actually delete.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Match:
    path: Path
    size_bytes: int


def _human_gb(num_bytes: int) -> str:
    return f"{num_bytes / (1024**3):.3f} GB"


def _is_target_model_safetensors(p: Path) -> bool:
    # We only ever delete files named exactly `model.safetensors`.
    if p.name != "model.safetensors":
        return False

    # Match subpaths relative to the nearest "models" directory in the path.
    parts = p.parts
    try:
        models_idx = parts.index("models")
    except ValueError:
        return False

    rel = parts[models_idx + 1 :]
    if len(rel) < 2:
        return False

    # models/r-series/**/model.safetensors
    if rel[0] == "r-series":
        return True

    # models/thor/thor-1.2/reply-enhancement/**/model.safetensors
    if (
        len(rel) >= 4
        and rel[0] == "thor"
        and rel[1] == "thor-1.2"
        and rel[2] == "reply-enhancement"
    ):
        return True

    return False


def _collect_targets(root: Path) -> list[Match]:
    matches: list[Match] = []
    for p in root.rglob("model.safetensors"):
        if not p.is_file():
            continue
        if not _is_target_model_safetensors(p):
            continue
        try:
            size = p.stat().st_size
        except OSError:
            # If we can't stat it, skip (but report later by path).
            size = -1
        matches.append(Match(path=p, size_bytes=size))
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prune model.safetensors for r-series + thor reply-enhancement trees."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory to scan (can be the repo root or an absolute /models path). Default: .",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete files. If omitted, runs in dry-run mode.",
    )
    args = parser.parse_args()

    root = Path(os.path.expanduser(args.root)).resolve()
    if not root.exists():
        raise SystemExit(f"--root does not exist: {root}")

    matches = _collect_targets(root)
    if not matches:
        print(f"No targets found under: {root}")
        return 0

    total = sum(m.size_bytes for m in matches if m.size_bytes >= 0)
    print(f"Found {len(matches)} target file(s) under: {root}")
    if total > 0:
        print(f"Total size (stat-able): {_human_gb(total)}")

    for m in matches:
        size_str = "unknown size" if m.size_bytes < 0 else _human_gb(m.size_bytes)
        print(f"- {m.path} ({size_str})")

    if not args.apply:
        print("\nDry-run: no files deleted. Re-run with --apply to delete.")
        return 0

    deleted = 0
    failed = 0
    for m in matches:
        try:
            m.path.unlink()
            deleted += 1
        except OSError as e:
            failed += 1
            print(f"FAILED to delete: {m.path} ({e})")

    print(f"\nDeleted {deleted} file(s). Failed: {failed}.")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

