"""Threat difficulty tiers for training and (later) random-play missions.

Tier ids are short ASCII tokens for specs and CLI flags. Display labels use
plain US military aviation wording so non-native English speakers can read them
on the briefing screen without idioms or pop-culture references.
"""

from __future__ import annotations

DIFFICULTY_TIERS = ("training", "routine", "contested", "high_threat")

# Mechanical knobs applied by builders. Labels are shown to the pilot.
DIFFICULTY_PROFILES: dict[str, dict] = {
    "training": {
        "label": "TRAINING",
        "description": "Low threat — wide training areas, one SAM site, no CAP.",
        "enemy_skill": "Average",
        "cap_flights": 0,
        "site_count": 1,
        "sam_pool": ("SA-2", "SA-3"),
        "zone_scale": 1.35,
        "spawn_nm": 30,
        "hold_nm": 10,
        "site_spacing_nm": 16,
    },
    "routine": {
        "label": "ROUTINE",
        "description": "Standard threat — two legacy SAM sites, no CAP.",
        "enemy_skill": "Good",
        "cap_flights": 0,
        "site_count": 2,
        "sam_pool": ("SA-2", "SA-3", "SA-6"),
        "zone_scale": 1.0,
        "spawn_nm": 32,
        "hold_nm": 12,
        "site_spacing_nm": 18,
    },
    "contested": {
        "label": "CONTESTED",
        "description": "Contested airspace — three SAM sites, higher skill.",
        "enemy_skill": "High",
        "cap_flights": 0,
        "site_count": 3,
        "sam_pool": ("SA-6", "SA-11"),
        "zone_scale": 0.85,
        "spawn_nm": 34,
        "hold_nm": 12,
        "site_spacing_nm": 16,
    },
    "high_threat": {
        "label": "HIGH THREAT",
        "description": "High threat — layered SAMs plus red CAP.",
        "enemy_skill": "Excellent",
        "cap_flights": 1,
        "site_count": 3,
        "sam_pool": ("SA-6", "SA-11"),
        "zone_scale": 0.75,
        "spawn_nm": 36,
        "hold_nm": 14,
        "site_spacing_nm": 14,
    },
}


def profile(difficulty: str) -> dict:
    """Return the profile dict for a tier id; raises KeyError if unknown."""
    return DIFFICULTY_PROFILES[difficulty]
