"""Threat difficulty tiers for training and random-play missions.

Tier ids are short ASCII tokens for specs and CLI flags. Display labels use
plain US military aviation wording so non-native English speakers can read them
on the briefing screen without idioms or pop-culture references.

Training builders read the top-level keys (``enemy_skill``, ``cap_flights``,
``site_count``, ``sam_pool``, etc.). Random-play ``dcsintel generate`` reads
the nested ``generate`` block on each profile.
"""

from __future__ import annotations

DIFFICULTY_TIERS = ("training", "routine", "contested", "high_threat")

# Mechanical knobs applied by builders. Labels are shown to the pilot.
DIFFICULTY_PROFILES: dict[str, dict] = {
    "training": {
        "label": "TRAINING",
        "description": "Low threat — forgiving opposition, clear weather, full support.",
        "enemy_skill": "Average",
        "cap_flights": 0,
        "site_count": 1,
        "sam_pool": ("SA-2", "SA-3"),
        "zone_scale": 1.35,
        "spawn_nm": 30,
        "hold_nm": 10,
        "site_spacing_nm": 16,
        "generate": {
            "modern_era_chance": 0.2,
            "time_pool": ("day", "day", "day", "dawn"),
            "weather_pool": ("clear", "clear", "clear", "scattered"),
            "cap_flights": (0, 0),
            "sam_count": (1, 2),
            "sam_pool": ("SA-2", "SA-3", "AAA"),
            "fighters": {
                "dogfight": (1, 1),
                "default": (1, 2),
            },
            "awacs": True,
            "tanker": True,
            "twist_count": (0, 0),
        },
    },
    "routine": {
        "label": "ROUTINE",
        "description": "Standard threat — era-typical opposition, mixed weather.",
        "enemy_skill": "Good",
        "cap_flights": 0,
        "site_count": 2,
        "sam_pool": ("SA-2", "SA-3", "SA-6"),
        "zone_scale": 1.0,
        "spawn_nm": 32,
        "hold_nm": 12,
        "site_spacing_nm": 18,
        "generate": {
            "modern_era_chance": 0.45,
            "time_pool": ("dawn", "day", "day", "day", "dusk", "night"),
            "weather_pool": ("clear", "clear", "scattered", "scattered", "broken", "overcast"),
            "cap_flights": (0, 1),
            "sam_count": (2, 3),
            "sam_pool": ("SA-2", "SA-3", "SA-6", "AAA"),
            "fighters": {
                "dogfight": (1, 2),
                "default": (2, 4),
            },
            "awacs": True,
            "tanker": True,
            "twist_count": (0, 1),
        },
    },
    "contested": {
        "label": "CONTESTED",
        "description": "Contested airspace — layered threats, reduced support, harder weather.",
        "enemy_skill": "High",
        "cap_flights": 0,
        "site_count": 3,
        "sam_pool": ("SA-6", "SA-11"),
        "zone_scale": 0.85,
        "spawn_nm": 34,
        "hold_nm": 12,
        "site_spacing_nm": 16,
        "generate": {
            "modern_era_chance": 0.75,
            "time_pool": ("dusk", "night", "day", "day", "dawn"),
            "weather_pool": ("scattered", "broken", "overcast", "overcast", "rain"),
            "cap_flights": (1, 2),
            "sam_count": (2, 4),
            "sam_pool": ("SA-6", "SA-11", "SA-15", "AAA"),
            "fighters": {
                "dogfight": (2, 3),
                "default": (3, 5),
            },
            "awacs": True,
            "tanker": False,
            "twist_count": (1, 2),
        },
    },
    "high_threat": {
        "label": "HIGH THREAT",
        "description": "High threat — IADS, stacked CAP, minimal support, mean environment.",
        "enemy_skill": "Excellent",
        "cap_flights": 1,
        "site_count": 3,
        "sam_pool": ("SA-6", "SA-11"),
        "zone_scale": 0.75,
        "spawn_nm": 36,
        "hold_nm": 14,
        "site_spacing_nm": 14,
        "generate": {
            "modern_era_chance": 0.9,
            "time_pool": ("night", "dusk", "dawn", "day"),
            "weather_pool": ("broken", "overcast", "overcast", "rain"),
            "cap_flights": (2, 3),
            "sam_count": (3, 4),
            "sam_pool": ("SA-6", "SA-10", "SA-11", "SA-15", "SA-19"),
            "fighters": {
                "dogfight": (2, 4),
                "default": (4, 6),
            },
            "awacs": False,
            "tanker": False,
            "twist_count": (2, 3),
        },
    },
}


def profile(difficulty: str) -> dict:
    """Return the profile dict for a tier id; raises KeyError if unknown."""
    return DIFFICULTY_PROFILES[difficulty]
