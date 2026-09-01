"""Strike: destroy a ground target cluster defended by point defenses.

The target is a supply concentration (trucks and flak) near the
objective, guarded by an era-appropriate short-range air defense unit.
"""

import dcs.task

from ..builder import FT, BuildContext, add_red_cap, spawn_sam_site, spawn_vehicle_cluster


PLAYER_TASK = dcs.task.GroundAttack


def build(ctx: BuildContext) -> None:
    spec, rng = ctx.spec, ctx.rng

    spawn_vehicle_cluster(
        ctx, ctx.red, "Supply Dump", ctx.catalog["red_soft"], ctx.objective, spread_nm=0.4,
    )

    # Point defense: one SHORAD site guarding the target.
    point_defense = "SA-15" if spec["era"] == "modern" else "AAA"
    if point_defense in spec["enemy"]["sam_types"]:
        point_defense = spec["enemy"]["sam_types"][0]
    spawn_sam_site(ctx, point_defense, ctx.scatter(ctx.objective, 1.5), "Target Defense")

    add_red_cap(ctx, spec["enemy"]["cap_flights"], ctx.red_airport.position)

    ingress = ctx.point_toward_blue(ctx.objective, 25)
    ctx.player_group.add_waypoint(ingress, int(18000 * FT))
    ctx.player_group.add_waypoint(ctx.objective, int(14000 * FT))
    ctx.player_group.add_waypoint(ingress, int(20000 * FT))

    if spec["briefing"]["objective"] is None:
        spec["briefing"]["objective"] = (
            "Destroy the enemy supply concentration at waypoint 2. "
            f"Expect {point_defense} point defense at the target."
        )
    ctx.briefing_lines.append(f"Target defense: {point_defense}")
