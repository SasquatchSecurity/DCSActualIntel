"""Point-defense spawning for strike and CAS training."""

from __future__ import annotations

import random

from dcs.mapping import Point

from ..builder import NM, add_red_cap, set_group_skill, spawn_sam_site, spawn_vehicle_cluster


class TrainingThreatCtx:
    """Minimal context for SAM and vehicle spawn helpers."""

    def __init__(self, mission, spec, rng, catalog, red, blue, heading, objective):
        self.mission = mission
        self.spec = spec
        self.rng = rng
        self.catalog = catalog
        self.red = red
        self.blue = blue
        self.heading = heading
        self.objective = objective

    def scatter(self, center: Point, max_nm: float) -> Point:
        return center.point_from_heading(
            self.rng.uniform(0, 360), self.rng.uniform(0, max_nm) * NM,
        )


def pick_defense_types(
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


def spawn_supply_target(ctx: TrainingThreatCtx, center: Point, name: str):
    type_id = ctx.rng.choice(ctx.catalog["red_soft"])
    return spawn_vehicle_cluster(ctx, ctx.red, name, [type_id], center, spread_nm=0.35)[0]


def spawn_point_defense(
    ctx: TrainingThreatCtx,
    sam_key: str,
    center: Point,
    name: str,
    skill: str,
):
    groups = spawn_sam_site(ctx, sam_key, ctx.scatter(center, 0.8), name)
    for group in groups:
        set_group_skill(group, skill)
    return groups


def maybe_add_cap(ctx: TrainingThreatCtx, count: int, station: Point) -> None:
    if count:
        add_red_cap(ctx, count, station)
