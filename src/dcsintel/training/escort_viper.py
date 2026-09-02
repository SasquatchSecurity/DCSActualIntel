"""F-16 escort curriculum: stay with strike package, threat reaction."""

from __future__ import annotations

import random

import dcs.task
from dcs.task import Escort

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
from .threats import TrainingThreatCtx, maybe_add_cap, pick_defense_types, spawn_point_defense


def build_escort_viper(spec: dict, out_path: str | None = None) -> str:
    prof = spec["difficulty_profile"]
    messages = load_data("curricula")["curricula"]["escort_viper"]["messages"]
    rng = random.Random(spec["seed"])
    catalog = load_data("catalog")

    m, blue, red, heading, blue_ap, red_ap = open_training_mission(spec, rng)
    objective = red_ap.position.point_from_heading((heading + 180) % 360, 12 * NM)

    package_spawn = blue_ap.position.point_from_heading(heading, 8 * NM)
    strikers = catalog["blue_bombers"][spec["era"]]
    strike_type = strikers[rng.randrange(len(strikers))]
    package = m.flight_group_inflight(
        blue, "Strike Package", _aircraft(strike_type), package_spawn,
        int(22000 * FT), maintask=dcs.task.GroundAttack,
    )
    package.add_waypoint(objective, int(18000 * FT))

    escort_spawn = inbound_spawn(package_spawn, heading, 4)
    alt_ft = 22000
    fg, player = spawn_player_air(
        m, blue, spec["aircraft"], escort_spawn, Escort, alt_ft,
        apply_f16_cap_loadout, inbound_heading=heading,
    )
    fg.add_waypoint(objective, int(alt_ft * FT))

    ctx = TrainingThreatCtx(m, spec, rng, catalog, red, blue, heading, objective)
    fighters = catalog["red_fighters"][spec["era"]]
    bandit_type = fighters[rng.randrange(len(fighters))]
    intercept_spawn = objective.point_from_heading(heading, 20 * NM)
    bandits = spawn_red_flight(
        ctx, "Red Intercept", bandit_type, intercept_spawn,
        altitude_ft=alt_ft,
        group_size=max(2, prof["site_count"] * 2),
        maintask=dcs.task.Intercept, toward=package_spawn,
    )

    era_sams = set(catalog["sam_by_era"][spec["era"]])
    defense_key = pick_defense_types(rng, tuple(prof["sam_pool"]), era_sams, 1)[0]
    spawn_point_defense(ctx, defense_key, objective, "Target IADS", spec["enemy"]["skill"])
    maybe_add_cap(ctx, prof["cap_flights"], objective)

    zone_scale = prof["zone_scale"]
    add_training_intro(m, messages["intro"])

    zone_brief(m, escort_spawn, int(6000 * zone_scale), player.id, 1, messages["phase1_escort"], 55)
    zone_brief(
        m,
        intercept_spawn.point_from_heading((heading + 180) % 360, 8 * NM),
        int(10000 * zone_scale),
        player.id,
        2,
        messages["phase2_engagement"],
        60,
    )

    on_group_dead(m, bandits.id, 50, [message(m, messages["training_complete"], 50)])

    write_briefing(m, spec, prof)
    terrain_name = spec["terrain"]
    diff_slug = prof["label"].lower().replace(" ", "_")
    default_name = f"training_{spec['curriculum']}_{diff_slug}_{terrain_name}_{spec['seed']}.miz"
    saved = resolve_output_path(spec, default_name, out_path)
    m.save(saved)
    return saved


def _aircraft(type_id: str):
    from ..builder import aircraft_class

    return aircraft_class(type_id)
