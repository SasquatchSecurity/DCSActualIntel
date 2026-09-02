"""Scenario twists for random-play missions.

Twists are optional mechanical constraints applied on top of difficulty
tiers. Names are short English tokens; briefing text uses plain labels.
"""

from __future__ import annotations

import random
from typing import Any

# Twist ids eligible per difficulty tier (subset picked at random).
TWISTS_BY_TIER: dict[str, tuple[str, ...]] = {
    "training": (),
    "routine": ("low_visibility", "thin_support"),
    "contested": ("low_visibility", "night_ops", "bandits_airborne", "thin_support"),
    "high_threat": (
        "low_visibility",
        "night_ops",
        "bandits_airborne",
        "thin_support",
        "compressed_timeline",
    ),
}

TWIST_DEFS: dict[str, dict[str, Any]] = {
    "low_visibility": {
        "label": "LOW VISIBILITY",
        "briefing": "Low visibility — IMC or reduced contrast expected in the objective area.",
        "weather": "overcast",
    },
    "night_ops": {
        "label": "NIGHT OPS",
        "briefing": "Night operations — NVG discipline required.",
        "time_of_day": "night",
    },
    "bandits_airborne": {
        "label": "BANDITS AIRBORNE",
        "briefing": "Bandits already airborne — expect an active red CAP picture.",
        "cap_flights_delta": 1,
    },
    "thin_support": {
        "label": "THIN SUPPORT",
        "briefing": "Thin support — no AWACS or tanker on station for this sortie.",
        "awacs": False,
        "tanker": False,
    },
    "compressed_timeline": {
        "label": "COMPRESSED TIMELINE",
        "briefing": "Compressed timeline — objective is closer than a standard push.",
        "distance_scale": 0.72,
    },
}


def pick_twists(rng: random.Random, difficulty: str, count: int) -> list[str]:
    pool = TWISTS_BY_TIER[difficulty]
    if not pool or count <= 0:
        return []
    count = min(count, len(pool))
    return list(rng.sample(pool, count))


def apply_twists(
    spec: dict,
    twists: list[str],
    *,
    locked: set[str],
) -> list[str]:
    """Apply twist side effects to ``spec``. Returns briefing lines."""
    lines: list[str] = []
    for twist_id in twists:
        if twist_id not in TWIST_DEFS:
            continue
        twist = TWIST_DEFS[twist_id]
        lines.append(twist["briefing"])

        if "weather" in twist and "weather" not in locked:
            spec["weather"] = twist["weather"]
        if "time_of_day" in twist and "time_of_day" not in locked:
            spec["time_of_day"] = twist["time_of_day"]

        if twist.get("awacs") is False and "support" not in locked:
            spec.setdefault("support", {})["awacs"] = False
        if twist.get("tanker") is False and "support" not in locked:
            spec.setdefault("support", {})["tanker"] = False

        delta = twist.get("cap_flights_delta")
        if delta and "enemy.cap_flights" not in locked:
            enemy = spec.setdefault("enemy", {})
            enemy["cap_flights"] = min(4, enemy.get("cap_flights", 0) + delta)

        scale = twist.get("distance_scale")
        if scale and "distance_nm" not in locked:
            spec["distance_nm"] = max(15.0, float(spec["distance_nm"]) * scale)

    spec["twists"] = twists
    return lines
