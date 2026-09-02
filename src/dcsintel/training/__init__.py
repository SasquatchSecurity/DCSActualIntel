"""Scripted training mission builders (F-16 v1)."""

from __future__ import annotations

from pathlib import Path

from ..spec import SpecError


_BUILDERS = {
    "sead_viper": "sead_viper",
    "jdam_viper": "jdam_viper",
}


def build_training(spec: dict, out_path: str | None = None) -> Path:
    """Build a normalized training spec and return the saved ``.miz`` path."""
    curriculum = spec.get("curriculum", "sead_viper")
    module = _BUILDERS.get(curriculum)
    if module is None:
        raise SpecError(
            f"no builder for curriculum {curriculum!r}. "
            f"Implemented: {sorted(_BUILDERS)}"
        )
    import importlib

    build_fn = getattr(importlib.import_module(f".{module}", __package__), f"build_{module}")
    return Path(build_fn(spec, out_path))
