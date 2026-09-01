"""SEAD/DEAD: roll back an integrated air defense network.

Sites from ``enemy.sam_types`` are scattered around the objective area,
backed by an early-warning radar deeper in enemy territory and optional
red CAP. The briefing lists the expected threats - actual intel.
"""

import dcs.task

from ..builder import NM, FT, BuildContext, add_red_cap, spawn_sam_site, vehicle_class


PLAYER_TASK = dcs.task.SEAD


def build(ctx: BuildContext) -> None:
    spec, rng = ctx.spec, ctx.rng

    sam_types = spec["enemy"]["sam_types"]
    for i, sam in enumerate(sam_types):
        center = ctx.scatter(ctx.objective, 8)
        spawn_sam_site(ctx, sam, center, f"SAM {sam} {i + 1}")

    ewr_types = ctx.catalog["ewr"]
    ewr_pos = ctx.objective.point_from_heading(ctx.heading, 15 * NM)
    ctx.mission.vehicle_group(
        ctx.red, "EWR Site", vehicle_class(ewr_types[rng.randrange(len(ewr_types))]), ewr_pos,
    )

    add_red_cap(ctx, spec["enemy"]["cap_flights"], ctx.red_airport.position)

    ingress = ctx.point_toward_blue(ctx.objective, 30)
    ctx.player_group.add_waypoint(ingress, int(22000 * FT))
    ctx.player_group.add_waypoint(ctx.objective, int(20000 * FT))
    ctx.player_group.add_waypoint(ingress, int(24000 * FT))

    if spec["briefing"]["objective"] is None:
        spec["briefing"]["objective"] = (
            f"Destroy the enemy air defense network near waypoint 2: "
            f"{', '.join(sam_types)}. Egress via waypoint 3 once the threat rings are down."
        )
    ctx.briefing_lines.append(f"Threats: {', '.join(sam_types)}; EWR active deeper in")
    if spec["enemy"]["cap_flights"]:
        ctx.briefing_lines.append("Red CAP is airborne - keep one eye on the scope")
