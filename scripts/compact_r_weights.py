#!/usr/bin/env python3
"""
Compact R-series weights on disk:

- Convert `weights/model.safetensors` (fp32/fp16) to an int8-on-disk format:
    - store weights as int8 tensors under original keys
    - store per-tensor scale under `__qt_scale__<key>` as float16 scalar tensor
  This typically shrinks ~4x from fp32 while keeping runtime efficiency since
  loaders dequantize to fp16 at load time.

- Write `weights/rN.safetensors` (or `weights/r{N}.safetensors`) for each model.
- Delete the original `weights/model.safetensors` when --apply is set.
- For Thor reply-enhancement models, prefer hardlinking to the corresponding
  r-series compact file to avoid duplicate storage.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple

import torch

try:
    from safetensors.torch import load_file, save_file
except Exception as e:  # pragma: no cover
    raise SystemExit("safetensors is required: pip install safetensors") from e

QT_SCALE_PREFIX = "__qt_scale__"


def _human_gb(num_bytes: int) -> str:
    return f"{num_bytes / (1024**3):.3f} GB"


def _quantize_tensor_int8(x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Symmetric per-tensor int8 quantization.
    Returns (q_int8, scale_fp16_scalar_tensor).
    """
    # Always quantize on CPU for predictable memory.
    x = x.detach().cpu()
    xf = x.float()
    max_abs = xf.abs().max().item()
    if max_abs == 0.0 or not (max_abs > 0.0):
        scale = 1.0
        q = torch.zeros_like(xf, dtype=torch.int8)
        s = torch.tensor(scale, dtype=torch.float16)
        return q, s

    scale = max_abs / 127.0
    q = torch.clamp((xf / scale).round(), -127, 127).to(torch.int8)
    s = torch.tensor(scale, dtype=torch.float16)
    return q, s


def compact_safetensors(in_path: Path, out_path: Path) -> None:
    """
    Read a safetensors file, write a compact int8-on-disk safetensors file.
    """
    state: Dict[str, torch.Tensor] = load_file(str(in_path))

    out: Dict[str, torch.Tensor] = {}
    scales: Dict[str, torch.Tensor] = {}

    for k, v in state.items():
        if v.dtype in (torch.float32, torch.float16, torch.bfloat16):
            q, s = _quantize_tensor_int8(v)
            out[k] = q
            scales[f"{QT_SCALE_PREFIX}{k}"] = s
        else:
            # Keep non-float tensors as-is.
            out[k] = v.detach().cpu()

    out.update(scales)
    meta = {
        "atlas_quant_scheme": "int8_sym_per_tensor_v1",
        "atlas_quant_scale_prefix": QT_SCALE_PREFIX,
        "source": str(in_path),
    }

    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    save_file(out, str(tmp), metadata=meta)
    tmp.replace(out_path)


@dataclass(frozen=True)
class ModelSpec:
    name: str  # r1..r6
    model_dir: Path

    @property
    def weights_dir(self) -> Path:
        return self.model_dir / "weights"

    @property
    def full_path(self) -> Path:
        return self.weights_dir / "model.safetensors"

    @property
    def compact_path(self) -> Path:
        return self.weights_dir / f"{self.name}.safetensors"


def _iter_r_series(repo_root: Path) -> Iterable[ModelSpec]:
    base = repo_root / "models" / "r-series"
    for i in range(1, 7):
        name = f"r{i}"
        yield ModelSpec(name=name, model_dir=base / name)


def _iter_reply_enhancement(repo_root: Path) -> Iterable[ModelSpec]:
    base = repo_root / "models" / "thor" / "thor-1.2" / "reply-enhancement"
    for i in range(1, 7):
        name = f"r{i}"
        yield ModelSpec(name=name, model_dir=base / name)


def _safe_stat(p: Path) -> int:
    try:
        return p.stat().st_size
    except OSError:
        return 0


def _hardlink_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        # Cross-device or permission issue; fall back to copy
        import shutil

        shutil.copy2(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".", help="Path to atlas-ai repo root (default: .)")
    ap.add_argument("--apply", action="store_true", help="Actually delete model.safetensors after compaction")
    ap.add_argument("--force", action="store_true", help="Recreate compact files even if they exist")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not (repo_root / "models").exists():
        raise SystemExit(f"Not a repo root (no models/): {repo_root}")

    # 1) Build compact files for r-series.
    reclaimed = 0
    created = 0

    print("Compacting r-series weights...")
    for spec in _iter_r_series(repo_root):
        if not spec.model_dir.exists():
            print(f"- skip (missing): {spec.model_dir}")
            continue
        if not spec.full_path.exists():
            print(f"- skip (no full weights): {spec.full_path}")
            continue

        if spec.compact_path.exists() and not args.force:
            print(f"- ok (exists): {spec.compact_path}")
        else:
            print(f"- create: {spec.compact_path} <- {spec.full_path}")
            compact_safetensors(spec.full_path, spec.compact_path)
            created += 1

        if args.apply:
            sz = _safe_stat(spec.full_path)
            spec.full_path.unlink(missing_ok=True)
            reclaimed += sz

    # 2) Reply-enhancement: prefer hardlink to r-series compact outputs.
    print("\nLinking/compacting reply-enhancement weights...")
    for spec in _iter_reply_enhancement(repo_root):
        if not spec.model_dir.exists():
            print(f"- skip (missing): {spec.model_dir}")
            continue

        r_series_compact = repo_root / "models" / "r-series" / spec.name / "weights" / f"{spec.name}.safetensors"
        if r_series_compact.exists():
            print(f"- link: {spec.compact_path} -> {r_series_compact}")
            _hardlink_or_copy(r_series_compact, spec.compact_path)
        elif spec.full_path.exists():
            if spec.compact_path.exists() and not args.force:
                print(f"- ok (exists): {spec.compact_path}")
            else:
                print(f"- create: {spec.compact_path} <- {spec.full_path}")
                compact_safetensors(spec.full_path, spec.compact_path)
                created += 1
        else:
            print(f"- skip (no weights): {spec.model_dir}")
            continue

        if args.apply and spec.full_path.exists():
            sz = _safe_stat(spec.full_path)
            spec.full_path.unlink(missing_ok=True)
            reclaimed += sz

    print(f"\nCreated/updated compact files: {created}")
    if args.apply:
        print(f"Reclaimed from deleted model.safetensors: {_human_gb(reclaimed)}")
    else:
        print("Dry-run for deletion: no model.safetensors removed (use --apply).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

