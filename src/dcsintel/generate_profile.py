"""Apply difficulty tiers and scenario twists to random-play MissionSpecs."""

from __future__ import annotations

import random
from typing import Optional

from .difficulty import profile
from .twists import apply_twists, pick_twists


def _rng_range(rng: random.Random, bounds: tuple[int, int]) -> int:
    lo, hi = bounds
    return rng.randint(lo, hi)


def _pick_sams(
    rng: random.Random,
    pool: tuple[str, ...],
    era_sams: list[str],
    count: int,
) -> list[str]:
    filtered = [s for s in pool if s in era_sams]
    if not filtered:
        filtered = list(era_sams)
    if count <= len(filtered):
        return rng.sample(filtered, count)
    return [filtered[rng.randrange(len(filtered))] for _ in range(count)]


def apply_generate_options(
    spec: dict,
    rng: random.Random,
    catalog: dict,
    *,
    locked: set[str],
    user_twists: Optional[list[str]],
) -> list[str]:
    """Fill difficulty-driven defaults and twists. Returns extra briefing lines."""
    diff_id = spec.get("difficulty", "routine")
    prof = profile(diff_id)
    spec["difficulty"] = diff_id
    spec["difficulty_profile"] = prof
    gen = prof["generate"]
    mtype = spec["type"]
    lines: list[str] = []

    if "era" not in locked:
        if rng.random() < gen["modern_era_chance"]:
            spec["era"] = "modern"

    era_sams = catalog["sam_by_era"][spec["era"]]

    if "time_of_day" not in locked and spec.get("time_of_day") in (None, "random"):
        spec["time_of_day"] = rng.choice(gen["time_pool"])
    if "weather" not in locked and spec.get("weather") in (None, "random"):
        spec["weather"] = rng.choice(gen["weather_pool"])

    enemy = spec.setdefault("enemy", {})
    if "enemy.skill" not in locked:
        enemy["skill"] = prof["enemy_skill"]

    if "enemy.fighters" not in locked:
        lo, hi = gen["fighters"].get(mtype, gen["fighters"]["default"])
        enemy["fighters"] = rng.randint(lo, hi)

    if "enemy.cap_flights" not in locked:
        enemy["cap_flights"] = _rng_range(rng, gen["cap_flights"])

    if "enemy.sam_types" not in locked:
        if mtype == "sead":
            count = _rng_range(rng, gen["sam_count"])
            enemy["sam_types"] = _pick_sams(rng, gen["sam_pool"], era_sams, count)
        else:
            pool = [s for s in gen["sam_pool"] if s in era_sams] or era_sams
            enemy["sam_types"] = [pool[rng.randrange(len(pool))]]

    support = spec.setdefault("support", {})
    if "support" not in locked:
        if gen.get("awacs") is not None:
            support["awacs"] = gen["awacs"]
        if gen.get("tanker") is not None:
            support["tanker"] = gen["tanker"]

    if user_twists is not None:
        twists = list(user_twists)
    else:
        twist_count = _rng_range(rng, gen["twist_count"])
        twists = pick_twists(rng, diff_id, twist_count)

    lines.extend(apply_twists(spec, twists, locked=locked))
    return lines
