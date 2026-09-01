"""Combat Air Patrol: hold a station and stop a red push toward friendly lines.

The player gets a CAP station at the midpoint; a red strike package
(strikers plus escorts) launches from enemy territory toward the blue
airbase and must come through the player's station.
"""

import dcs.task

from ..builder import NM, FT, BuildContext, add_red_cap, spawn_red_flight


PLAYER_TASK = dcs.task.CAP


def build(ctx: BuildContext) -> None:
    spec, rng = ctx.spec, ctx.rng

    # CAP station: midpoint, with a racetrack leg perpendicular to the threat axis.
    station = ctx.point_toward_blue(ctx.objective, spec["distance_nm"] * 0.5)
    leg_end = station.point_from_heading((ctx.heading + 90) % 360, 20 * NM)
    ctx.player_group.add_waypoint(station, int(20000 * FT))
    ctx.player_group.add_waypoint(leg_end, int(20000 * FT))

    strikers = ctx.catalog["red_strikers"][spec["era"]]
    striker_type = strikers[rng.randrange(len(strikers))]
    package_spawn = ctx.scatter(ctx.red_airport.position, 5)
    spawn_red_flight(
        ctx, "Red Package", striker_type, package_spawn,
        altitude_ft=rng.choice([8000, 12000, 16000]),
        group_size=2, maintask=dcs.task.GroundAttack, toward=ctx.blue_airport.position,
    )

    escort_count = spec["enemy"]["fighters"]
    fighters = ctx.catalog["red_fighters"][spec["era"]]
    escort_type = fighters[rng.randrange(len(fighters))]
    spawn_red_flight(
        ctx, "Red Escort", escort_type, ctx.scatter(package_spawn, 8),
        altitude_ft=rng.choice([18000, 24000]),
        group_size=escort_count, maintask=dcs.task.Escort, toward=ctx.blue_airport.position,
    )

    add_red_cap(ctx, spec["enemy"]["cap_flights"], ctx.objective)

    if spec["briefing"]["objective"] is None:
        spec["briefing"]["objective"] = (
            f"Establish CAP at waypoint 1 and prevent the inbound strike package "
            f"(2x {striker_type} escorted by {escort_count}x {escort_type}) from "
            f"reaching {ctx.blue_airport.name}."
        )
    ctx.briefing_lines.append(
        f"Picture: strike package inbound from {ctx.red_airport.name}, escorts in trail"
    )
