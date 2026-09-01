"""Shared mission plumbing: MissionSpec dict -> saved .miz file.

This module owns everything common to all mission types: terrain and
weather setup, airbase selection, the player flight, support aircraft
(AWACS/tanker), briefing text, saving, and validation. The per-type
content (what makes SEAD a SEAD) lives in :mod:`dcsintel.missions`.

Coordinate conventions: pydcs points are terrain-local meters;
``Point.point_from_heading(deg, meters)`` projects a point. We work in
nautical miles at the API surface (DCS pilots think in nm) and convert.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Type

import dcs
from dcs.cloud_presets import Clouds
from dcs.mapping import Point
from dcs.mission import Mission, StartType
from dcs.terrain import (
    Caucasus, Falklands, Germany, Kola, MarianaIslands, Nevada,
    Normandy, PersianGulf, Sinai, Syria, TheChannel,
)
from dcs.unit import Skill
from dcs.weather import Wind

from .data import load_data
from .spec import SpecError

NM = 1852.0  # meters per nautical mile
FT = 0.3048  # meters per foot

TERRAIN_CLASSES = {
    "Caucasus": Caucasus,
    "Falklands": Falklands,
    "Germany": Germany,
    "Kola": Kola,
    "MarianaIslands": MarianaIslands,
    "Nevada": Nevada,
    "Normandy": Normandy,
    "PersianGulf": PersianGulf,
    "Sinai": Sinai,
    "Syria": Syria,
    "TheChannel": TheChannel,
}

START_TYPES = {
    "cold": StartType.Cold,
    "hot": StartType.Warm,
    "runway": StartType.Runway,
    # "air" handled separately via flight_group_inflight
}

_TOD_HOURS = {"dawn": 5, "day": 12, "dusk": 19, "night": 22}

# Callsign pools; purely cosmetic, picked with the mission rng.
BLUE_CALLSIGNS = ["Enfield", "Springfield", "Uzi", "Colt", "Dodge", "Ford", "Chevy", "Pontiac"]
RED_GROUP_NAMES = ["Vandal", "Bandit", "Hostile", "Raider", "Cossack", "Tempest"]


@dataclass
class BuildContext:
    """Everything a mission-type builder needs, precomputed once."""

    mission: Mission
    spec: dict
    rng: random.Random
    catalog: dict
    blue: object  # dcs Country
    red: object   # dcs Country
    blue_airport: object   # dcs Airport
    red_airport: object    # dcs Airport
    heading: float         # degrees, blue airbase -> objective
    objective: Point       # mission objective / engagement point
    player_group: object = None      # set by build_mission after player spawn
    briefing_lines: list = field(default_factory=list)  # extra lines per type

    def nm_between(self, a: Point, b: Point) -> float:
        return a.distance_to_point(b) / NM

    def point_toward_blue(self, origin: Point, nm: float) -> Point:
        """A point ``nm`` from ``origin`` back toward the blue airbase."""
        back = (self.heading + 180) % 360
        return origin.point_from_heading(back, nm * NM)

    def scatter(self, center: Point, max_nm: float) -> Point:
        """Random point within ``max_nm`` of center (uniform-ish)."""
        return center.point_from_heading(
            self.rng.uniform(0, 360), self.rng.uniform(0, max_nm) * NM
        )


# --------------------------------------------------------------------------
# Aircraft / unit resolution
# --------------------------------------------------------------------------

def aircraft_class(type_id: str) -> Type:
    """Resolve a DCS aircraft type id to its pydcs class (plane or helicopter)."""
    cls = dcs.planes.plane_map.get(type_id) or dcs.helicopters.helicopter_map.get(type_id)
    if cls is None:
        raise SpecError(
            f"aircraft type {type_id!r} is unknown to pydcs. "
            "Check the exact DCS type name (e.g. 'F-16C_50', 'FA-18C_hornet')."
        )
    return cls


def is_helicopter(type_id: str) -> bool:
    return type_id in dcs.helicopters.helicopter_map


def vehicle_class(type_id: str) -> Type:
    cls = dcs.vehicles.vehicle_map.get(type_id)
    if cls is None:
        raise SpecError(f"vehicle type {type_id!r} is unknown to pydcs.")
    return cls


def set_group_skill(group, skill_name: str) -> None:
    skill = Skill(skill_name) if skill_name != "Random" else Skill.Random
    for unit in group.units:
        unit.skill = skill


# --------------------------------------------------------------------------
# Spawn helpers used by mission-type builders
# --------------------------------------------------------------------------

def spawn_red_flight(
    ctx: BuildContext,
    name: str,
    type_id: str,
    position: Point,
    altitude_ft: float,
    group_size: int,
    maintask=None,
    toward: Optional[Point] = None,
):
    """Air-spawn a red flight at ``position`` with an optional waypoint toward a target."""
    fg = ctx.mission.flight_group_inflight(
        ctx.red, name, aircraft_class(type_id), position,
        int(altitude_ft * FT), maintask=maintask, group_size=group_size,
    )
    set_group_skill(fg, ctx.spec["enemy"]["skill"])
    if toward is not None:
        fg.add_waypoint(toward, int(altitude_ft * FT))
    return fg


def spawn_sam_site(ctx: BuildContext, sam_key: str, center: Point, name: str):
    """Place one SAM battery as a single vehicle group.

    DCS requires every component of a SAM site (search radar, track radar,
    launchers) to live in the *same* group or the battery cannot engage.
    Each component is still placed on the ring layout, but they share one
    group so AI can link radar to launchers under standard alarm rules.
    """
    template = ctx.catalog["sam_templates"][sam_key]
    placements: list[tuple[str, Point, float]] = []

    for i, type_id in enumerate(template["center"]):
        pos = center.point_from_heading(ctx.rng.uniform(0, 360), 60 + 40 * i)
        placements.append((type_id, pos, 0.0))

    ring = template["ring"]
    for i in range(ring["count"]):
        heading_deg = 360 / ring["count"] * i
        pos = center.point_from_heading(heading_deg, ring["ring_radius_m"])
        placements.append((ring["type"], pos, float((heading_deg + 180) % 360)))

    vehicles = []
    for i, (type_id, pos, hdg) in enumerate(placements):
        v = ctx.mission.vehicle(f"{name} Unit #{i + 1}", vehicle_class(type_id))
        v.position = pos
        v.heading = hdg
        vehicles.append(v)

    group = ctx.mission.vehicle_group_from_vehicles(ctx.red, name, vehicles, center)
    # pydcs runs a formation pass that stacks units; restore our layout.
    for unit, (_, pos, hdg) in zip(group.units, placements):
        unit.position = pos
        unit.heading = hdg

    return [group]


def spawn_vehicle_cluster(ctx: BuildContext, country, name: str, type_ids: list,
                          center: Point, spread_nm: float = 0.5):
    """Scatter one single-type vehicle group per type id around ``center``."""
    groups = []
    for i, type_id in enumerate(type_ids):
        pos = ctx.scatter(center, spread_nm)
        size = ctx.rng.randint(2, 4) if country is ctx.red else 3
        g = ctx.mission.vehicle_group(
            country, f"{name} {i + 1}", vehicle_class(type_id), pos,
            heading=ctx.rng.uniform(0, 360), group_size=size,
        )
        groups.append(g)
    return groups


def add_red_cap(ctx: BuildContext, count: int, station: Point) -> list:
    """Air-spawn ``count`` red CAP flights loitering near ``station``."""
    flights = []
    fighters = ctx.catalog["red_fighters"][ctx.spec["era"]]
    for i in range(count):
        type_id = fighters[ctx.rng.randrange(len(fighters))]
        pos = ctx.scatter(station, 10)
        fg = spawn_red_flight(
            ctx, f"Red CAP {i + 1}", type_id, pos,
            altitude_ft=ctx.rng.choice([15000, 20000, 25000]),
            group_size=2, maintask=dcs.task.CAP, toward=station,
        )
        flights.append(fg)
    return flights


# --------------------------------------------------------------------------
# Environment setup
# --------------------------------------------------------------------------

def _apply_start_time(m: Mission, spec: dict, rng: random.Random, catalog: dict) -> None:
    year = catalog["eras"][spec["era"]]["year"]
    hour = _TOD_HOURS[spec["time_of_day"]]
    m.start_time = datetime(
        year, rng.randint(5, 9), rng.randint(1, 28), hour, rng.choice([0, 15, 30, 45]),
        tzinfo=timezone.utc,
    )


def _apply_weather(m: Mission, spec: dict, rng: random.Random) -> None:
    """Map the spec's one-word weather to a cloud preset + winds."""
    word = spec["weather"]
    weather = m.weather

    wind_speed = {"clear": (0, 4), "scattered": (1, 6), "broken": (2, 8),
                  "overcast": (3, 10), "rain": (5, 12)}[word]
    direction = rng.randint(0, 359)
    weather.wind_at_ground = Wind(direction, rng.uniform(*wind_speed))
    weather.wind_at_2000 = Wind((direction + rng.randint(-20, 20)) % 360,
                                rng.uniform(*wind_speed) * 1.8)
    weather.wind_at_8000 = Wind((direction + rng.randint(-40, 40)) % 360,
                                rng.uniform(*wind_speed) * 3.0)

    if word == "clear":
        weather.clouds_density = 0
        return

    prefix = {"scattered": "Scattered", "broken": "Broken",
              "overcast": "Overcast", "rain": "OvercastAndRain"}[word]
    presets = [c.value for c in Clouds if c.name.startswith(prefix)]
    if not presets:  # future-proofing: fall back to any preset
        presets = [c.value for c in Clouds]
    preset = presets[rng.randrange(len(presets))]
    weather.clouds_preset = preset
    weather.clouds_base = rng.randint(int(preset.min_base), int(preset.max_base))


def _pick_airbase_pair(terrain, spec: dict, rng: random.Random):
    """Choose (blue, red) airports roughly ``distance_nm`` apart.

    If the player named an airbase, honor it. Otherwise search random
    pairs inside a widening distance window so every terrain works.

    Among valid pairs, strongly prefer those whose midpoint is close to
    the terrain's default map view center: that's where the Mission
    Editor opens, and where map detail is richest. Without this bias a
    pair at the far map edge is a valid but miserable pick - the user
    opens the ME and sees nothing (all content off-screen).
    """
    airports = [a for a in terrain.airports.values() if a.runways]
    if len(airports) < 2:
        raise SpecError(f"terrain {spec['terrain']!r} has fewer than 2 usable airports")

    map_center = terrain.map_view_default.position
    wanted = spec["distance_nm"] * NM
    requested = spec["player"].get("airbase")
    blue_candidates = airports
    if requested:
        matches = [a for a in airports if a.name.lower() == requested.lower()]
        if not matches:
            names = sorted(a.name for a in airports)
            raise SpecError(
                f"airbase {requested!r} not found on {spec['terrain']}. Available: {names}"
            )
        blue_candidates = matches

    best = None
    for tolerance in (0.25, 0.5, 1.0, 10.0):
        lo, hi = wanted * (1 - tolerance), wanted * (1 + tolerance)
        pairs = [
            (b, r) for b in blue_candidates for r in airports
            if r is not b and lo <= b.position.distance_to_point(r.position) <= hi
        ]
        if pairs:
            # Rank by midpoint distance to the map center, then pick randomly
            # among the best few to keep seed-driven variety.
            pairs.sort(
                key=lambda pair: Point(
                    (pair[0].position.x + pair[1].position.x) / 2,
                    (pair[0].position.y + pair[1].position.y) / 2,
                    terrain,
                ).distance_to_point(map_center)
            )
            shortlist = pairs[:max(1, min(len(pairs) // 4, 8))]
            best = shortlist[rng.randrange(len(shortlist))]
            break
    if best is None:  # degenerate terrain; just take the farthest pair
        b = blue_candidates[0]
        r = max((a for a in airports if a is not b),
                key=lambda a: b.position.distance_to_point(a.position))
        best = (b, r)

    blue_ap, red_ap = best
    blue_ap.set_blue()
    red_ap.set_red()
    return blue_ap, red_ap


# --------------------------------------------------------------------------
# Player and support flights
# --------------------------------------------------------------------------

def _spawn_player(ctx: BuildContext, maintask) -> None:
    spec = ctx.spec
    type_id = spec["player"]["aircraft"]
    cls = aircraft_class(type_id)
    callsign = BLUE_CALLSIGNS[ctx.rng.randrange(len(BLUE_CALLSIGNS))]
    name = f"{callsign} 1"

    if spec["player"]["start"] == "air":
        # Air start facing the objective, 5000 ft AGL-ish cruise block.
        pos = ctx.point_toward_blue(ctx.objective, spec["distance_nm"] * 0.6)
        alt_ft = 8000 if is_helicopter(type_id) is False else 1500
        fg = ctx.mission.flight_group_inflight(
            ctx.blue, name, cls, pos, int(alt_ft * FT), maintask=maintask,
        )
    else:
        fg = ctx.mission.flight_group_from_airport(
            ctx.blue, name, cls, ctx.blue_airport,
            maintask=maintask, start_type=START_TYPES[spec["player"]["start"]],
        )
    try:
        fg.load_task_default_loadout(maintask)
    except Exception:
        pass  # not every airframe has a default loadout for every task
    fg.units[0].set_client()
    ctx.player_group = fg


def _clamp_to_map(terrain, point: Point) -> Point:
    """Clamp a point into the bounding box of the terrain's airports.

    Geometry helpers happily project points past the map edge (e.g. a
    support orbit 25 nm "behind" an airbase that is itself on the edge);
    the airport bounding box is a safe proxy for the usable map area.
    """
    xs = [a.position.x for a in terrain.airports.values()]
    ys = [a.position.y for a in terrain.airports.values()]
    return Point(
        min(max(point.x, min(xs)), max(xs)),
        min(max(point.y, min(ys)), max(ys)),
        terrain,
    )


def _spawn_support(ctx: BuildContext) -> None:
    spec, m, rng = ctx.spec, ctx.mission, ctx.rng
    rear = _clamp_to_map(
        ctx.mission.terrain, ctx.point_toward_blue(ctx.blue_airport.position, 25)
    )
    if spec["support"].get("awacs"):
        awacs_type = ctx.catalog["blue_awacs"][spec["era"]]
        m.awacs_flight(
            ctx.blue, "Overlord", aircraft_class(awacs_type), None, rear,
            race_distance=60 * NM, heading=(ctx.heading + 90) % 360,
            altitude=int(30000 * FT), frequency=251,
        )
        ctx.briefing_lines.append("AWACS: Overlord, 251.00 MHz AM")
    if spec["support"].get("tanker"):
        tanker_type = ctx.catalog["blue_tanker"][spec["era"]]
        m.refuel_flight(
            ctx.blue, "Texaco", aircraft_class(tanker_type), None,
            _clamp_to_map(ctx.mission.terrain,
                          rear.point_from_heading((ctx.heading + 90) % 360, 20 * NM)),
            race_distance=40 * NM, heading=(ctx.heading + 90) % 360,
            altitude=int(22000 * FT), frequency=252, tacanchannel="38X",
        )
        ctx.briefing_lines.append("Tanker: Texaco, 252.00 MHz AM, TACAN 38X, FL220")


# --------------------------------------------------------------------------
# Briefing
# --------------------------------------------------------------------------

_TYPE_TITLES = {
    "dogfight": "Air Combat Maneuvering", "cap": "Combat Air Patrol",
    "sead": "Suppression of Enemy Air Defenses", "strike": "Precision Strike",
    "escort": "Bomber Escort", "cas": "Close Air Support", "intercept": "Intercept Scramble",
}


def _apply_briefing(ctx: BuildContext) -> None:
    spec = ctx.spec
    b = spec["briefing"]
    title = b.get("title") or f"{_TYPE_TITLES[spec['type']]} - {spec['terrain']}"
    lines = [
        title,
        "",
        b.get("situation") or "Regional tensions have escalated into open conflict.",
        "",
        f"OBJECTIVE: {b.get('objective') or 'See tasking below.'}",
        "",
        f"Departure: {ctx.blue_airport.name}",
        f"Objective area: {spec['distance_nm']:.0f} nm out, bearing {ctx.heading:.0f}",
        f"Weather: {spec['weather']}, time: {spec['time_of_day']}, era: {spec['era']}",
        "",
        *ctx.briefing_lines,
        "",
        f"(Generated by DCSActualIntel, seed {spec['seed']})",
    ]
    ctx.mission.set_description_text("\n".join(lines))


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------

def build_mission(spec: dict, out_path: Optional[str] = None) -> Path:
    """Build the mission described by a *normalized* spec and save it.

    ``spec`` must already have passed :func:`dcsintel.spec.normalize`.
    Returns the path of the saved ``.miz``.
    """
    if spec["type"] == "sead_training":
        from .missions.sead_training import build_training
        return Path(build_training(spec, out_path))

    from . import missions  # deferred: missions imports helpers from this module

    terrain_cls = TERRAIN_CLASSES.get(spec["terrain"])
    if terrain_cls is None:
        raise SpecError(
            f"terrain {spec['terrain']!r} not supported. "
            f"Supported: {sorted(TERRAIN_CLASSES)}"
        )

    rng = random.Random(spec["seed"])
    catalog = load_data("catalog")
    m = Mission(terrain_cls())

    _apply_start_time(m, spec, rng, catalog)
    _apply_weather(m, spec, rng)

    blue = m.country("USA")
    red = m.country("Russia")
    blue_ap, red_ap = _pick_airbase_pair(m.terrain, spec, rng)
    heading = blue_ap.position.heading_between_point(red_ap.position)

    # The objective sits short of the red airbase so targets aren't parked
    # on the ramp; each mission type may refine this.
    objective = red_ap.position.point_from_heading((heading + 180) % 360, 10 * NM)

    ctx = BuildContext(
        mission=m, spec=spec, rng=rng, catalog=catalog,
        blue=blue, red=red, blue_airport=blue_ap, red_airport=red_ap,
        heading=heading, objective=objective,
    )

    builder = missions.BUILDERS[spec["type"]]
    maintask = builder.PLAYER_TASK
    _spawn_player(ctx, maintask)
    builder.build(ctx)
    _spawn_support(ctx)
    _apply_briefing(ctx)

    if out_path is None:
        out_path = f"{spec['type']}_{spec['terrain']}_{spec['seed']}.miz"
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out))
    return out


def validate_miz(path: str) -> dict:
    """Reload a .miz with pydcs and sanity-check it.

    Returns a summary dict; raises ValueError with details on failure.
    """
    m = Mission()
    messages = m.load_file(str(path))

    clients = [
        u for coalition in m.coalition.values()
        for country in coalition.countries.values()
        for group in country.plane_group + country.helicopter_group
        for u in group.units
        if u.skill in (Skill.Client, Skill.Player)
    ]
    if not clients:
        raise ValueError(f"{path}: no player/client slot found in mission")

    red = m.coalition["red"]
    red_units = sum(
        len(g.units)
        for c in red.countries.values()
        for g in c.plane_group + c.helicopter_group + c.vehicle_group + c.ship_group
    )
    if red_units == 0:
        raise ValueError(f"{path}: mission has no red units (no opposition)")

    return {
        "path": str(path),
        "terrain": m.terrain.name,
        "player_aircraft": clients[0].type,
        "start_time": str(m.start_time),
        "red_units": red_units,
        "load_messages": [str(msg) for msg in messages],
    }
