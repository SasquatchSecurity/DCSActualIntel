"""Scripted training mission builders (F-16 v1)."""

from __future__ import annotations

from pathlib import Path

from ..spec import SpecError


def build_training(spec: dict, out_path: str | None = None) -> Path:
    """Build a normalized training spec and return the saved ``.miz`` path."""
    curriculum = spec.get("curriculum", "sead_viper")
    if curriculum == "sead_viper":
        from .sead_viper import build_sead_viper

        return Path(build_sead_viper(spec, out_path))
    raise SpecError(f"no builder for curriculum {curriculum!r}")
