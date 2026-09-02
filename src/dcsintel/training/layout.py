"""Shared geometry and player spawn for scripted training sorties."""

from __future__ import annotations

import random
from datetime import datetime, timezone

from dcs.mapping import Point
from dcs.mission import Mission
from dcs.unit import Skill
from dcs.weather import Wind

from ..builder import FT, NM, TERRAIN_CLASSES, _pick_airbase_pair, aircraft_class
from ..spec import SpecError
from .common import PLAYER_GROUP, ascii_text


def open_training_mission(
    spec: dict, rng: random.Random,
) -> tuple[Mission, object, object, float, object, object]:
    """Create mission shell. Returns (mission, blue, red, heading, blue_ap, red_ap)."""
    terrain_cls = TERRAIN_CLASSES.get(spec["terrain"])
    if terrain_cls is None:
        raise SpecError(f"terrain {spec['terrain']!r} not supported for training")

    m = Mission(terrain_cls())
    m.start_time = datetime(2016, 6, 15, 12, 0, tzinfo=timezone.utc)
    m.weather.wind_at_ground = Wind(270, 4)
    m.weather.clouds_density = 0

    blue = m.country("USA")
    red = m.country("Russia")
    blue_ap, red_ap = _pick_airbase_pair(m.terrain, spec, rng)
    heading = blue_ap.position.heading_between_point(red_ap.position)
    return m, blue, red, heading, blue_ap, red_ap


def threat_axis_points(
    red_ap_position: Point,
    heading: float,
    prof: dict,
    count: int,
) -> list[Point]:
    """Place ``count`` points along the threat axis away from the red airfield."""
    spacing = prof["site_spacing_nm"] * NM
    first_offset = prof["site_spacing_nm"] * 0.45 * NM
    first = red_ap_position.point_from_heading((heading + 180) % 360, first_offset)
    points = [first]
    for _ in range(1, count):
        points.append(points[-1].point_from_heading(heading, spacing))
    return points


def inbound_spawn(objective: Point, heading: float, spawn_nm: float) -> Point:
    """Return an air-start point ``spawn_nm`` behind ``objective`` on the inbound axis."""
    return objective.point_from_heading((heading + 180) % 360, spawn_nm * NM)


def spawn_player_air(
    mission: Mission,
    blue,
    aircraft: str,
    spawn: Point,
    maintask,
    alt_ft: int = 12000,
    loadout_fn=None,
    inbound_heading: float | None = None,
):
    """Air-start the player inbound on the training route."""
    fg = mission.flight_group_inflight(
        blue, PLAYER_GROUP, aircraft_class(aircraft), spawn,
        int(alt_ft * FT), maintask=maintask,
    )
    player = fg.units[0]
    player.set_client()
    player.skill = Skill.Client
    if inbound_heading is not None:
        player.heading = inbound_heading
    if loadout_fn:
        loadout_fn(player)
    return fg, player


def write_briefing(mission: Mission, spec: dict, prof: dict) -> None:
    b = spec.get("briefing") or {}
    title = b.get("title") or "Training Sortie"
    situation = b.get("situation") or ""
    objective = b.get("objective") or ""
    mission.set_description_text(
        ascii_text(
            f"{title}\n"
            f"Threat level: {prof['label']}\n\n"
            f"{situation}\n\n"
            f"OBJECTIVE: {objective}\n\n"
            f"(DCSActualIntel training - {spec['curriculum']}, seed {spec['seed']})"
        )
    )
