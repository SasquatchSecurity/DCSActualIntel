"""Intercept / QRA scramble: raiders are already inbound to your field.

The player starts on the ground (spec validation enforces this) while a
red package - strikers with escorts, or bombers - is partway to the blue
airbase. Time pressure is the mission.
"""

import dcs.task

from ..builder import BuildContext, spawn_red_flight


PLAYER_TASK = dcs.task.Intercept


def build(ctx: BuildContext) -> None:
    spec, rng = ctx.spec, ctx.rng

    use_bombers = rng.random() < 0.4
    raider_pool = ctx.catalog["red_bombers" if use_bombers else "red_strikers"][spec["era"]]
    raider_type = raider_pool[rng.randrange(len(raider_pool))]

    # Raiders spawn just under halfway in, giving the player time to get airborne.
    raid_spawn = ctx.point_toward_blue(ctx.red_airport.position, spec["distance_nm"] * 0.45)
    spawn_red_flight(
        ctx, "Raid", raider_type, raid_spawn,
        altitude_ft=rng.choice([16000, 22000, 30000]),
        group_size=2, maintask=dcs.task.GroundAttack, toward=ctx.blue_airport.position,
    )

    escort_count = max(spec["enemy"]["fighters"] - 2, 0)
    escort_type = None
    if escort_count:
        fighters = ctx.catalog["red_fighters"][spec["era"]]
        escort_type = fighters[rng.randrange(len(fighters))]
        spawn_red_flight(
            ctx, "Raid Escort", escort_type, ctx.scatter(raid_spawn, 6),
            altitude_ft=rng.choice([20000, 26000]),
            group_size=escort_count, maintask=dcs.task.Escort,
            toward=ctx.blue_airport.position,
        )

    if spec["briefing"]["objective"] is None:
        threat = f"2x {raider_type}"
        if escort_type:
            threat += f" with {escort_count}x {escort_type} escort"
        spec["briefing"]["objective"] = (
            f"SCRAMBLE. {threat} inbound to {ctx.blue_airport.name}, "
            f"bearing {ctx.heading:.0f}, roughly {spec['distance_nm'] * 0.55:.0f} nm out. "
            "Get airborne and splash the raid before it reaches the field."
        )
    ctx.briefing_lines.append("This is a scramble: expedite your startup")
