"""Close Air Support: friendly troops in contact at the FLOT.

A red armor column faces a smaller blue element at the objective. Red
short-range air defense travels with the column, so the player has to
work the target area with some respect.
"""

import dcs.task

from ..builder import FT, BuildContext, add_red_cap, spawn_vehicle_cluster


PLAYER_TASK = dcs.task.CAS


def build(ctx: BuildContext) -> None:
    spec = ctx.spec

    flot = ctx.objective
    red_types = list(ctx.catalog["red_armor"])
    shorad = ctx.catalog["red_shorad"]
    red_types.append(shorad[0 if spec["era"] == "coldwar" else ctx.rng.randrange(len(shorad))])
    spawn_vehicle_cluster(ctx, ctx.red, "Red Column", red_types, flot, spread_nm=1.0)

    blue_pos = ctx.point_toward_blue(flot, 3)
    spawn_vehicle_cluster(ctx, ctx.blue, "Chevy Ground", ctx.catalog["blue_armor"], blue_pos, spread_nm=0.5)

    add_red_cap(ctx, spec["enemy"]["cap_flights"], ctx.red_airport.position)

    hold = ctx.point_toward_blue(flot, 12)
    ctx.player_group.add_waypoint(hold, int(10000 * FT))
    ctx.player_group.add_waypoint(flot, int(8000 * FT))

    if spec["briefing"]["objective"] is None:
        spec["briefing"]["objective"] = (
            "Friendly armor is in contact at waypoint 2. Destroy the enemy column. "
            "Expect mobile SHORAD with the formation - use standoff tactics or terrain."
        )
    ctx.briefing_lines.append("Friendlies 3 nm southwest of the enemy column - check your targets")
    ctx.briefing_lines.append("Threat: mobile SHORAD embedded with enemy armor")
