"""F-16 CAP curriculum: GCI flow, commit, BVR employment."""

from __future__ import annotations

import random

import dcs.task
from dcs.task import CAP

from ..builder import FT, NM, spawn_red_flight
from ..data import load_data
from .common import (
    add_training_intro,
    apply_f16_cap_loadout,
    message,
    on_group_dead,
    resolve_output_path,
    zone_brief,
)
from .layout import inbound_spawn, open_training_mission, spawn_player_air, write_briefing
from .threats import TrainingThreatCtx, maybe_add_cap


def build_cap_viper(spec: dict, out_path: str | None = None) -> str:
    prof = spec["difficulty_profile"]
    messages = load_data("curricula")["curricula"]["cap_viper"]["messages"]
    rng = random.Random(spec["seed"])
    catalog = load_data("catalog")

    m, blue, red, heading, blue_ap, red_ap = open_training_mission(spec, rng)
    station = blue_ap.position.point_from_heading(heading, spec["distance_nm"] * 0.45 * NM)
    leg = station.point_from_heading((heading + 90) % 360, 15 * NM)

    spawn = inbound_spawn(station, heading, 5)
    alt_ft = 20000
    fg, player = spawn_player_air(
        m, blue, spec["aircraft"], spawn, CAP, alt_ft,
        apply_f16_cap_loadout, inbound_heading=heading,
    )
    fg.add_waypoint(station, int(alt_ft * FT))
    fg.add_waypoint(leg, int(alt_ft * FT))

    ctx = TrainingThreatCtx(m, spec, rng, catalog, red, blue, heading, station)
    fighters = catalog["red_fighters"][spec["era"]]
    bandit_type = fighters[rng.randrange(len(fighters))]
    bandit_count = max(2, prof["site_count"] * 2)
    package_spawn = red_ap.position.point_from_heading(heading, spec["distance_nm"] * 0.35 * NM)
    bandits = spawn_red_flight(
        ctx, "Red Bandits", bandit_type, package_spawn,
        altitude_ft=alt_ft - 2000,
        group_size=bandit_count, maintask=dcs.task.FighterSweep, toward=blue_ap.position,
    )
    maybe_add_cap(ctx, prof["cap_flights"], station)

    zone_scale = prof["zone_scale"]
    add_training_intro(m, messages["intro"])

    zone_brief(m, station, int(8000 * zone_scale), player.id, 1, messages["phase1_cap"], 55)
    zone_brief(
        m,
        package_spawn,
        int(12000 * zone_scale),
        player.id,
        2,
        messages["phase2_commit"],
        60,
    )

    on_group_dead(m, bandits.id, 40, [message(m, messages["training_complete"], 50)])

    write_briefing(m, spec, prof)
    terrain_name = spec["terrain"]
    diff_slug = prof["label"].lower().replace(" ", "_")
    default_name = f"training_{spec['curriculum']}_{diff_slug}_{terrain_name}_{spec['seed']}.miz"
    saved = resolve_output_path(spec, default_name, out_path)
    m.save(saved)
    return saved
