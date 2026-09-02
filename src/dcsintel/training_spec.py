"""TrainingSpec: JSON contract for scripted F-16 training missions.

Separate from :mod:`dcsintel.spec` (random play). Only F-16 curricula are
implemented in v1; see ``data/curricula.json`` for the future-platform roadmap.
"""

from __future__ import annotations

import random
from typing import Optional

from .data import load_data
from .difficulty import DIFFICULTY_TIERS, profile
from .spec import ERAS, _fail

F16_AIRCRAFT = "F-16C_50"


def normalize_training(spec: dict, ownership: Optional[dict] = None) -> dict:
    """Validate a training spec and fill omitted fields."""
    if not isinstance(spec, dict):
        _fail("spec must be a JSON object")
    spec = dict(spec)

    curricula = load_data("curricula")["curricula"]

    curriculum = spec.get("curriculum")
    if curriculum is None:
        # Backward compatibility with legacy ``type: sead_training`` specs.
        if spec.get("type") == "sead_training":
            curriculum = "sead_viper"
        else:
            _fail(
                f"'curriculum' is required. Implemented: {list(curricula.keys())}"
            )
    if curriculum not in curricula:
        _fail(
            f"unknown curriculum {curriculum!r}. Implemented: {list(curricula.keys())}"
        )
    spec["curriculum"] = curriculum
    meta = curricula[curriculum]

    aircraft = spec.get("aircraft") or meta.get("aircraft") or F16_AIRCRAFT
    if aircraft != F16_AIRCRAFT:
        _fail(
            f"only {F16_AIRCRAFT} training is implemented. "
            f"Future platforms are listed in curricula.json under future_platforms."
        )
    owned_modules = ownership["modules"] if ownership else None
    if owned_modules is not None and aircraft not in owned_modules:
        _fail(
            f"aircraft {aircraft!r} is not an owned flyable module. "
            f"Owned: {owned_modules}"
        )
    spec["aircraft"] = aircraft

    difficulty = spec.get("difficulty", "routine")
    if difficulty not in DIFFICULTY_TIERS:
        _fail(
            f"'difficulty' must be one of {list(DIFFICULTY_TIERS)}, got {difficulty!r}"
        )
    spec["difficulty"] = difficulty
    spec["difficulty_profile"] = profile(difficulty)

    era = spec.get("era")
    if era is None:
        era = "modern" if difficulty in ("contested", "high_threat") else "coldwar"
    if era not in ERAS:
        _fail(f"'era' must be one of {list(ERAS)}, got {era!r}")
    spec["era"] = era

    catalog = load_data("catalog")
    prof = spec["difficulty_profile"]
    era_sams = set(catalog["sam_by_era"][era])
    missing = [s for s in prof["sam_pool"] if s not in era_sams]
    if missing:
        _fail(
            f"difficulty {difficulty!r} requires SAM types {missing} "
            f"which are not available in era {era!r}. "
            f"Era allows: {sorted(era_sams)}"
        )

    seed = spec.get("seed")
    if seed is None:
        seed = random.randrange(2**31)
    elif not isinstance(seed, int):
        _fail(f"'seed' must be an integer, got {seed!r}")
    spec["seed"] = seed

    owned_terrains = ownership["terrains"] if ownership else None
    terrain = spec.get("terrain")
    if terrain is None:
        terrain = random.choice(owned_terrains) if owned_terrains else "Caucasus"
    if owned_terrains is not None and terrain not in owned_terrains:
        _fail(f"terrain {terrain!r} is not owned. Owned terrains: {owned_terrains}")
    spec["terrain"] = terrain

    spec.setdefault("distance_nm", 70)
    spec.setdefault(
        "enemy",
        {"skill": spec["difficulty_profile"]["enemy_skill"]},
    )
    spec["enemy"]["skill"] = spec["difficulty_profile"]["enemy_skill"]

    briefing = dict(spec.get("briefing") or {})
    briefing.setdefault("title", meta.get("briefing_title"))
    briefing.setdefault("situation", meta.get("briefing_situation"))
    briefing.setdefault("objective", meta.get("briefing_objective"))
    spec["briefing"] = briefing

    # Legacy alias so existing generate tests keep working.
    spec["type"] = "sead_training"
    spec.setdefault("player", {"aircraft": aircraft, "start": "air"})

    return spec
