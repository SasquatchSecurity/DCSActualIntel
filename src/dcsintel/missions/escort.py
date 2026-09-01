"""Bomber Escort: shepherd a friendly bomber stream past enemy interceptors.

Blue AI bombers fly from behind the player's base to the objective; red
interceptors launch to cut them off. The player's waypoints shadow the
bomber route, offset high so the escort starts in position.
"""

import dcs.task

from ..builder import NM, FT, BuildContext, aircraft_class, set_group_skill, spawn_red_flight


PLAYER_TASK = dcs.task.Escort


def build(ctx: BuildContext) -> None:
    spec, rng = ctx.spec, ctx.rng

    bombers = ctx.catalog["blue_bombers"][spec["era"]]
    bomber_type = bombers[rng.randrange(len(bombers))]
    bomber_alt_ft = 26000
    bomber_spawn = ctx.point_toward_blue(ctx.blue_airport.position, 15)
    bfg = ctx.mission.flight_group_inflight(
        ctx.blue, "Hammer", aircraft_class(bomber_type), bomber_spawn,
        int(bomber_alt_ft * FT), maintask=dcs.task.GroundAttack, group_size=2,
    )
    set_group_skill(bfg, "High")
    bfg.add_waypoint(ctx.objective, int(bomber_alt_ft * FT))
    bfg.add_waypoint(bomber_spawn, int(bomber_alt_ft * FT))

    fighters = ctx.catalog["red_fighters"][spec["era"]]
    interceptor_type = fighters[rng.randrange(len(fighters))]
    count = spec["enemy"]["fighters"]
    # Interceptors cut the route at its midpoint, coming from the flank.
    route_mid = ctx.point_toward_blue(ctx.objective, spec["distance_nm"] * 0.4)
    intercept_spawn = route_mid.point_from_heading(
        (ctx.heading + rng.choice([70, -70])) % 360, 35 * NM
    )
    spawn_red_flight(
        ctx, "Red Intercept", interceptor_type, intercept_spawn,
        altitude_ft=rng.choice([20000, 28000]),
        group_size=count, maintask=dcs.task.Intercept, toward=route_mid,
    )

    # Player shadows the bombers 4000 ft above.
    ctx.player_group.add_waypoint(route_mid, int((bomber_alt_ft + 4000) * FT))
    ctx.player_group.add_waypoint(ctx.objective, int((bomber_alt_ft + 4000) * FT))

    if spec["briefing"]["objective"] is None:
        spec["briefing"]["objective"] = (
            f"Escort Hammer flight (2x {bomber_type}, FL{bomber_alt_ft // 100}) to the "
            f"target and back. Intel expects {count}x {interceptor_type} to contest the route."
        )
    ctx.briefing_lines.append(f"Package: Hammer, 2x {bomber_type} at FL{bomber_alt_ft // 100}")
    ctx.briefing_lines.append(f"Threat: {count}x {interceptor_type} QRA on the route flank")
