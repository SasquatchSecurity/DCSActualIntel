"""Dogfight / BFM: red fighters converge on the player for a merge.

Geometry: the player (usually air-started by the builder) is roughly
40% of the way to the objective; red fighters spawn at the objective
and fly toward the player's spawn area, giving a head-on setup that
closes in a couple of minutes.
"""

import dcs.task

from ..builder import BuildContext, spawn_red_flight


PLAYER_TASK = dcs.task.FighterSweep


def build(ctx: BuildContext) -> None:
    spec, rng = ctx.spec, ctx.rng
    fighters = ctx.catalog["red_fighters"][spec["era"]]
    type_id = fighters[rng.randrange(len(fighters))]
    count = spec["enemy"]["fighters"]

    player_area = ctx.point_toward_blue(ctx.objective, spec["distance_nm"] * 0.6)
    spawn_red_flight(
        ctx, "Bandit 1", type_id, ctx.objective,
        altitude_ft=rng.choice([12000, 18000, 24000]),
        group_size=count, maintask=dcs.task.FighterSweep, toward=player_area,
    )

    if spec["briefing"]["objective"] is None:
        spec["briefing"]["objective"] = (
            f"Engage and destroy {count}x {type_id} approaching head-on. "
            "Fight's on when you're tally."
        )
    ctx.briefing_lines.append(f"Threat: {count}x {type_id}, closing from bearing {ctx.heading:.0f}")
