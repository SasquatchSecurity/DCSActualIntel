"""MissionSpec: the JSON contract between the AI agent and the builder.

A MissionSpec is a plain dict (parsed from JSON). Only ``type`` is
required; every other field is optional and will be filled with seeded
random choices by the builder, so ``{"type": "sead", "seed": 42}`` is a
complete, reproducible mission.

Validation errors are raised as :class:`SpecError` with messages written
to be read by an AI agent, so it can fix the spec and retry without help.

Schema (all fields optional unless noted)::

    {
      "type": "dogfight|cap|sead|strike|escort|cas|intercept",   # REQUIRED
      "terrain": "Caucasus",              # must be owned
      "era": "modern|coldwar",
      "time_of_day": "dawn|day|dusk|night|random",
      "weather": "clear|scattered|broken|overcast|rain|random",
      "player": {
        "aircraft": "F-16C_50",           # must be owned & flyable
        "start": "cold|hot|runway|air",
        "airbase": "Kutaisi"              # by name; random if omitted
      },
      "enemy": {
        "skill": "Average|Good|High|Excellent|Random",
        "sam_types": ["SA-10", "SA-6"],   # sead only; era-checked
        "fighters": 2,                    # count of enemy fighter aircraft
        "cap_flights": 1                  # extra red CAP flights (sead/strike/cas)
      },
      "support": {"awacs": true, "tanker": true},
      "distance_nm": 80,                  # player base -> objective distance
      "briefing": {"title": "...", "situation": "...", "objective": "..."},
      "seed": 42
    }
"""

from __future__ import annotations

import random
from typing import Optional

from .data import load_data

MISSION_TYPES = ("dogfight", "cap", "sead", "strike", "escort", "cas", "intercept", "sead_training")
ERAS = ("modern", "coldwar")
TIMES_OF_DAY = ("dawn", "day", "dusk", "night", "random")
WEATHERS = ("clear", "scattered", "broken", "overcast", "rain", "random")
STARTS = ("cold", "hot", "runway", "air")
SKILLS = ("Average", "Good", "High", "Excellent", "Random")


class SpecError(ValueError):
    """A MissionSpec problem, with an agent-actionable message."""


def _fail(msg: str) -> None:
    raise SpecError(msg)


def _choice(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def normalize(spec: dict, ownership: Optional[dict] = None) -> dict:
    """Validate ``spec`` and fill every omitted field with seeded choices.

    ``ownership`` is the dict returned by :func:`dcsintel.detect.detect`.
    Pass None to skip ownership checks (used by tests and --no-ownership-check).

    Returns a new, fully-populated spec dict. Raises SpecError on problems.
    """
    if not isinstance(spec, dict):
        _fail("spec must be a JSON object")
    spec = dict(spec)  # shallow copy; we normalize in place below
    catalog = load_data("catalog")

    mtype = spec.get("type")
    if mtype not in MISSION_TYPES:
        _fail(f"'type' must be one of {list(MISSION_TYPES)}, got {mtype!r}")

    if mtype == "sead_training":
        from .training_spec import normalize_training

        return normalize_training(spec, ownership)

    seed = spec.get("seed")
    if seed is None:
        seed = random.randrange(2**31)
    elif not isinstance(seed, int):
        _fail(f"'seed' must be an integer, got {seed!r}")
    spec["seed"] = seed
    rng = random.Random(seed)

    # --- terrain ---------------------------------------------------------
    owned_terrains = ownership["terrains"] if ownership else None
    terrain = spec.get("terrain")
    if terrain is None:
        if owned_terrains:
            terrain = _choice(rng, owned_terrains)
        else:
            terrain = "Caucasus"  # free with the base game
    if owned_terrains is not None and terrain not in owned_terrains:
        _fail(
            f"terrain {terrain!r} is not owned. Owned terrains: "
            f"{owned_terrains or ['<none detected - run dcsintel detect --refresh>']}"
        )
    spec["terrain"] = terrain

    # --- era / time / weather --------------------------------------------
    era = spec.get("era") or _choice(rng, ERAS)
    if era not in ERAS:
        _fail(f"'era' must be one of {list(ERAS)}, got {era!r}")
    spec["era"] = era

    tod = spec.get("time_of_day", "random")
    if tod not in TIMES_OF_DAY:
        _fail(f"'time_of_day' must be one of {list(TIMES_OF_DAY)}, got {tod!r}")
    if tod == "random":
        # Weighted toward daylight: night SEAD in an F-5 isn't fun by accident.
        tod = _choice(rng, ["dawn", "day", "day", "day", "dusk", "night"])
    spec["time_of_day"] = tod

    weather = spec.get("weather", "random")
    if weather not in WEATHERS:
        _fail(f"'weather' must be one of {list(WEATHERS)}, got {weather!r}")
    if weather == "random":
        weather = _choice(rng, ["clear", "clear", "scattered", "scattered", "broken", "overcast", "rain"])
    spec["weather"] = weather

    # --- player ------------------------------------------------------------
    player = dict(spec.get("player") or {})
    owned_modules = ownership["modules"] if ownership else None
    aircraft = player.get("aircraft")
    if aircraft is None:
        if not owned_modules:
            _fail(
                "player.aircraft not given and no owned modules detected. "
                "Run 'dcsintel detect --refresh' or set 'modules' in dcsintel.config.json."
            )
        aircraft = _choice(rng, owned_modules)
    if owned_modules is not None and aircraft not in owned_modules:
        _fail(
            f"player.aircraft {aircraft!r} is not an owned flyable module. "
            f"Owned: {owned_modules}"
        )
    player["aircraft"] = aircraft

    start = player.get("start")
    if start is None:
        start = "air" if mtype == "dogfight" else "hot"
    if start not in STARTS:
        _fail(f"player.start must be one of {list(STARTS)}, got {start!r}")
    if mtype == "intercept" and start == "air":
        _fail("intercept is a scramble mission: player.start must be cold, hot, or runway")
    player["start"] = start
    player.setdefault("airbase", None)  # resolved against terrain by the builder
    spec["player"] = player

    # --- enemy -------------------------------------------------------------
    enemy = dict(spec.get("enemy") or {})
    skill = enemy.get("skill", "Good")
    if skill not in SKILLS:
        _fail(f"enemy.skill must be one of {list(SKILLS)}, got {skill!r}")
    enemy["skill"] = skill

    era_sams = catalog["sam_by_era"][era]
    sam_types = enemy.get("sam_types")
    if sam_types is not None:
        bad = [s for s in sam_types if s not in catalog["sam_templates"]]
        if bad:
            _fail(f"unknown enemy.sam_types {bad}. Known: {list(catalog['sam_templates'])}")
        wrong_era = [s for s in sam_types if s not in era_sams]
        if wrong_era:
            _fail(f"enemy.sam_types {wrong_era} not appropriate for era {era!r}. Allowed: {era_sams}")
    else:
        count = rng.randint(2, 3) if mtype == "sead" else 1
        sam_types = rng.sample(era_sams, min(count, len(era_sams)))
    enemy["sam_types"] = sam_types

    fighters = enemy.get("fighters")
    if fighters is None:
        fighters = {"dogfight": rng.randint(1, 2)}.get(mtype, rng.randint(2, 4))
    if not isinstance(fighters, int) or not 1 <= fighters <= 8:
        _fail(f"enemy.fighters must be an integer 1-8, got {fighters!r}")
    enemy["fighters"] = fighters

    cap_flights = enemy.get("cap_flights")
    if cap_flights is None:
        cap_flights = rng.randint(0, 1)
    if not isinstance(cap_flights, int) or not 0 <= cap_flights <= 4:
        _fail(f"enemy.cap_flights must be an integer 0-4, got {cap_flights!r}")
    enemy["cap_flights"] = cap_flights
    spec["enemy"] = enemy

    # --- support -----------------------------------------------------------
    support = dict(spec.get("support") or {})
    support.setdefault("awacs", mtype != "dogfight")
    support.setdefault("tanker", mtype in ("cap", "sead", "strike", "escort"))
    spec["support"] = support

    # --- geometry ----------------------------------------------------------
    distance = spec.get("distance_nm")
    if distance is None:
        distance = {
            "dogfight": rng.randint(30, 50),
            "cap": rng.randint(60, 100),
            "sead": rng.randint(60, 120),
            "strike": rng.randint(60, 120),
            "escort": rng.randint(80, 140),
            "cas": rng.randint(40, 80),
            "intercept": rng.randint(50, 90),
        }[mtype]
    if not isinstance(distance, (int, float)) or not 15 <= distance <= 300:
        _fail(f"distance_nm must be a number between 15 and 300, got {distance!r}")
    spec["distance_nm"] = float(distance)

    # --- briefing ----------------------------------------------------------
    briefing = dict(spec.get("briefing") or {})
    briefing.setdefault("title", None)
    briefing.setdefault("situation", None)
    briefing.setdefault("objective", None)
    spec["briefing"] = briefing

    return spec
