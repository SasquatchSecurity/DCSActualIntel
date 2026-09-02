"""F-16 Maverick strike curriculum: TGP slave, seeker lock, launch."""

from __future__ import annotations

import random

from dcs import triggers
from dcs.task import GroundAttack

from ..builder import FT, NM
from ..data import load_data
from .common import (
    apply_f16_maverick_loadout,
    message,
    on_group_dead,
    resolve_output_path,
    zone_brief,
)
from .layout import (
    open_training_mission,
    spawn_player_air,
    threat_axis_points,
    write_briefing,
)
from .threats import (
    TrainingThreatCtx,
    maybe_add_cap,
    pick_defense_types,
    spawn_point_defense,
    spawn_supply_target,
)


def build_maverick_viper(spec: dict, out_path: str | None = None) -> str:
    prof = spec["difficulty_profile"]
    messages = load_data("curricula")["curricula"]["maverick_viper"]["messages"]
    rng = random.Random(spec["seed"])
    catalog = load_data("catalog")

    m, blue, red, heading, _blue_ap, red_ap = open_training_mission(spec, rng)
    target_count = prof["site_count"]
    targets = threat_axis_points(red_ap.position, heading, prof, target_count)

    spawn = targets[0].point_from_heading((heading + 180) % 360, prof["spawn_nm"] * NM)
    alt_ft = 12000
    fg, player = spawn_player_air(
        m, blue, spec["aircraft"], spawn, GroundAttack, alt_ft, apply_f16_maverick_loadout,
    )

    wp_hold = spawn.point_from_heading(heading, prof["hold_nm"] * NM)
    fg.add_waypoint(wp_hold, int(alt_ft * FT))
    for tgt in targets:
        fg.add_waypoint(tgt, int(8000 * FT))

    ctx = TrainingThreatCtx(m, spec, rng, catalog, red, blue, heading, targets[0])
    era_sams = set(catalog["sam_by_era"][spec["era"]])
    defense_keys = pick_defense_types(rng, tuple(prof["sam_pool"]), era_sams, target_count)

    target_groups = []
    for i, (tgt, sam_key) in enumerate(zip(targets, defense_keys)):
        target_groups.append(spawn_supply_target(ctx, tgt, f"TRG {i + 1}"))
        spawn_point_defense(ctx, sam_key, tgt, f"DEF {i + 1}", spec["enemy"]["skill"])

    maybe_add_cap(ctx, prof["cap_flights"], targets[-1])

    zone_scale = prof["zone_scale"]
    hold_radius = int(6000 * zone_scale)
    approach_radius = int(8000 * zone_scale)

    tr0 = triggers.TriggerStart(comment="training intro")
    tr0.add_action(message(m, messages["intro"], 60))
    m.triggerrules.triggers.append(tr0)

    zone_brief(m, wp_hold, hold_radius, player.id, 1, messages["phase1_route"], 55)
    zone_brief(
        m,
        targets[0].point_from_heading((heading + 180) % 360, 8 * NM),
        approach_radius,
        player.id,
        2,
        messages["phase2_lock"],
        60,
    )

    for i, group in enumerate(target_groups):
        is_last = i == len(target_groups) - 1
        text = messages["training_complete"] if is_last else messages["target_complete"]
        on_group_dead(m, group.id, 20 + i, [message(m, text, 50 if is_last else 45)])

    if target_count > 1:
        zone_brief(
            m,
            targets[1].point_from_heading((heading + 180) % 360, 10 * NM),
            approach_radius,
            player.id,
            3,
            messages["phase3_next_target"],
            50,
        )

    write_briefing(m, spec, prof)
    terrain_name = spec["terrain"]
    diff_slug = prof["label"].lower().replace(" ", "_")
    default_name = f"training_{spec['curriculum']}_{diff_slug}_{terrain_name}_{spec['seed']}.miz"
    saved = resolve_output_path(spec, default_name, out_path)
    m.save(saved)
    return saved
