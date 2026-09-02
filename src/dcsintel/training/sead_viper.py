"""F-16 SEAD curriculum: HTS search, HARM handoff, multi-site suppression."""

from __future__ import annotations

import random
from datetime import datetime, timezone

from dcs import action
from dcs.mapping import Point
from dcs.mission import Mission
from dcs.task import SEAD
from dcs.translation import String
from dcs.weather import Wind

from ..builder import (
    FT, NM, TERRAIN_CLASSES, _pick_airbase_pair, add_red_cap,
    set_group_skill, spawn_sam_site,
)
from ..data import load_data
from ..spec import SpecError
from .common import (
    PLAYER_GROUP,
    add_training_intro,
    apply_f16_sead_loadout,
    message,
    on_group_dead,
    resolve_output_path,
    zone_brief,
)
from .layout import inbound_spawn, spawn_player_air, write_briefing


class _SamCtx:
    """Minimal context for :func:`spawn_sam_site` and :func:`add_red_cap`."""

    def __init__(self, mission, spec, rng, catalog, red, heading, objective):
        self.mission = mission
        self.spec = spec
        self.rng = rng
        self.catalog = catalog
        self.red = red
        self.heading = heading
        self.objective = objective

    def scatter(self, center: Point, max_nm: float) -> Point:
        return center.point_from_heading(
            self.rng.uniform(0, 360), self.rng.uniform(0, max_nm) * NM,
        )


def _pick_sam_types(
    rng: random.Random,
    pool: tuple[str, ...],
    era_sams: set[str],
    count: int,
) -> list[str]:
    filtered = [s for s in pool if s in era_sams]
    if not filtered:
        filtered = list(era_sams)
    if count <= len(filtered):
        return list(rng.sample(filtered, count))
    return [filtered[rng.randrange(len(filtered))] for _ in range(count)]


def build_sead_viper(spec: dict, out_path: str | None = None) -> str:
    """Build the SEAD HTS/HARM training mission. Returns saved .miz path."""
    terrain_name = spec["terrain"]
    terrain_cls = TERRAIN_CLASSES.get(terrain_name)
    if terrain_cls is None:
        raise SpecError(f"terrain {terrain_name!r} not supported for training")

    prof = spec["difficulty_profile"]
    messages = load_data("curricula")["curricula"]["sead_viper"]["messages"]
    rng = random.Random(spec["seed"])
    catalog = load_data("catalog")
    m = Mission(terrain_cls())

    m.start_time = datetime(2016, 6, 15, 12, 0, tzinfo=timezone.utc)
    m.weather.wind_at_ground = Wind(270, 4)
    m.weather.clouds_density = 0

    blue = m.country("USA")
    red = m.country("Russia")
    blue_ap, red_ap = _pick_airbase_pair(m.terrain, spec, rng)
    heading = blue_ap.position.heading_between_point(red_ap.position)

    site_count = prof["site_count"]
    spacing = prof["site_spacing_nm"] * NM
    first_offset = prof["site_spacing_nm"] * 0.45 * NM
    site_a = red_ap.position.point_from_heading((heading + 180) % 360, first_offset)
    sites: list[Point] = [site_a]
    for i in range(1, site_count):
        sites.append(sites[-1].point_from_heading(heading, spacing))

    spawn_nm = prof["spawn_nm"]
    hold_nm = prof["hold_nm"]
    alt_ft = 12000
    spawn = inbound_spawn(sites[0], heading, spawn_nm)
    fg, player = spawn_player_air(
        m, blue, spec["aircraft"], spawn, SEAD, alt_ft,
        apply_f16_sead_loadout, inbound_heading=heading,
    )

    wp_hold = spawn.point_from_heading(heading, hold_nm * NM)
    fg.add_waypoint(wp_hold, int(alt_ft * FT))
    for site in sites:
        fg.add_waypoint(site, int(10000 * FT))

    sam_keys = _pick_sam_types(
        rng, tuple(prof["sam_pool"]), set(catalog["sam_by_era"][spec["era"]]), site_count,
    )
    site_names = ("TRN ALPHA", "TRN BRAVO", "TRN CHARLIE")
    sam_groups = []
    ctx = _SamCtx(m, spec, rng, catalog, red, heading, sites[0])
    skill = spec["enemy"]["skill"]
    for i, (site, sam_key) in enumerate(zip(sites, sam_keys)):
        groups = spawn_sam_site(ctx, sam_key, site, site_names[i])
        for group in groups:
            set_group_skill(group, skill)
        sam_groups.extend(groups)

    cap_count = prof["cap_flights"]
    if cap_count:
        add_red_cap(ctx, cap_count, sites[-1])

    zone_scale = prof["zone_scale"]
    hold_radius = int(6000 * zone_scale)
    approach_radius = int(8000 * zone_scale)

    add_training_intro(m, messages["intro"])

    zone_brief(
        m, wp_hold, hold_radius, player.id, 1,
        messages["phase1_hts"], 55,
    )

    zone_brief(
        m,
        sites[0].point_from_heading((heading + 180) % 360, 10 * NM),
        approach_radius,
        player.id,
        2,
        messages["phase2_handoff"],
        60,
    )

    rearm_lua = (
        f"local g=Group.getByName('{PLAYER_GROUP}'); "
        "if g then trigger.action.rearmGroup(g) end"
    )

    def _site_dead_actions(is_last: bool) -> list:
        if is_last:
            return [message(m, messages["training_complete"], 50)]
        return [
            message(m, messages["site_complete_rearm"], 45),
            action.DoScript(String(rearm_lua)),
        ]

    for i, sam_group in enumerate(sam_groups):
        is_last = i == len(sam_groups) - 1
        on_group_dead(m, sam_group.id, 10 + i, _site_dead_actions(is_last))

    if len(sam_groups) > 1:
        zone_brief(
            m,
            sites[1].point_from_heading((heading + 180) % 360, 12 * NM),
            approach_radius,
            player.id,
            3,
            messages["phase3_second_site"],
            50,
        )

    write_briefing(m, spec, prof)

    diff_label = prof["label"]
    default_name = f"training_{spec['curriculum']}_{diff_label.lower().replace(' ', '_')}_{terrain_name}_{spec['seed']}.miz"
    out_path = resolve_output_path(spec, default_name, out_path)
    m.save(out_path)
    return out_path
