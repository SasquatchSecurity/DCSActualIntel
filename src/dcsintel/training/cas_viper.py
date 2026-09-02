"""F-16 CAS curriculum: troops in contact, TGP ID, rocket employment."""

from __future__ import annotations

import random

from dcs.task import CAS

from ..builder import FT, NM, spawn_vehicle_cluster
from ..data import load_data
from .common import (
    add_training_intro,
    apply_f16_cas_loadout,
    message,
    on_group_dead,
    resolve_output_path,
    zone_brief,
)
from .layout import inbound_spawn, open_training_mission, spawn_player_air, write_briefing
from .threats import TrainingThreatCtx, maybe_add_cap, pick_defense_types, spawn_point_defense


def build_cas_viper(spec: dict, out_path: str | None = None) -> str:
    prof = spec["difficulty_profile"]
    messages = load_data("curricula")["curricula"]["cas_viper"]["messages"]
    rng = random.Random(spec["seed"])
    catalog = load_data("catalog")

    m, blue, red, heading, blue_ap, red_ap = open_training_mission(spec, rng)
    flot = red_ap.position.point_from_heading((heading + 180) % 360, spec["distance_nm"] * 0.55 * NM)

    spawn = inbound_spawn(flot, heading, 15)
    alt_ft = 10000
    fg, player = spawn_player_air(
        m, blue, spec["aircraft"], spawn, CAS, alt_ft,
        apply_f16_cas_loadout, inbound_heading=heading,
    )

    hold = flot.point_from_heading((heading + 180) % 360, 8 * NM)
    fg.add_waypoint(hold, int(alt_ft * FT))
    fg.add_waypoint(flot, int(8000 * FT))

    ctx = TrainingThreatCtx(m, spec, rng, catalog, red, blue, heading, flot)
    red_types = [rng.choice(catalog["red_armor"])]
    shorad = catalog["red_shorad"]
    red_types.append(shorad[0 if spec["era"] == "coldwar" else rng.randrange(len(shorad))])
    enemy_groups = spawn_vehicle_cluster(ctx, red, "Red Column", red_types, flot, spread_nm=0.8)

    blue_pos = flot.point_from_heading((heading + 180) % 360, 2 * NM)
    spawn_vehicle_cluster(ctx, blue, "Friendly Armor", catalog["blue_armor"], blue_pos, spread_nm=0.4)

    era_sams = set(catalog["sam_by_era"][spec["era"]])
    defense_key = pick_defense_types(rng, tuple(prof["sam_pool"]), era_sams, 1)[0]
    spawn_point_defense(ctx, defense_key, flot, "SHORAD", spec["enemy"]["skill"])
    maybe_add_cap(ctx, prof["cap_flights"], flot)

    zone_scale = prof["zone_scale"]
    hold_radius = int(5000 * zone_scale)

    add_training_intro(m, messages["intro"])

    zone_brief(m, hold, hold_radius, player.id, 1, messages["phase1_contact"], 55)
    zone_brief(m, flot, int(4000 * zone_scale), player.id, 2, messages["phase2_attack"], 60)

    if enemy_groups:
        on_group_dead(
            m, enemy_groups[-1].id, 30,
            [message(m, messages["training_complete"], 50)],
        )

    write_briefing(m, spec, prof)
    terrain_name = spec["terrain"]
    diff_slug = prof["label"].lower().replace(" ", "_")
    default_name = f"training_{spec['curriculum']}_{diff_slug}_{terrain_name}_{spec['seed']}.miz"
    saved = resolve_output_path(spec, default_name, out_path)
    m.save(saved)
    return saved
