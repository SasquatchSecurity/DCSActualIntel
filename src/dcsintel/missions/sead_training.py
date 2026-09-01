"""Guided F-16 HTS + HARM SEAD training mission (scripted popups, phased sites)."""

from __future__ import annotations

import random
from datetime import datetime, timezone

import dcs
from dcs import action, condition, triggers
from dcs.cloud_presets import Clouds
from dcs.mapping import Point
from dcs.mission import Mission, StartType
from dcs.task import SEAD
from dcs.translation import String
from dcs.unit import Skill
from dcs.weather import Wind

from ..builder import (
    NM, FT, TERRAIN_CLASSES, _pick_airbase_pair, aircraft_class, spawn_sam_site,
)
from ..data import load_data
from ..spec import SpecError

# F-16C pylon map (Block 50): wingtips = 1 & 9, HTS = 10.
AIM120C = "{40EF17B7-F508-45de-8566-6FFECC0C1AB8}"
HARM = "{B06DD79A-F21E-4EB9-BD9D-AB3844618C93}"
HTS = "{AN_ASQ_213}"

PLAYER_GROUP = "Viper 1"
FLAG_REARMED = 50


def _apply_training_loadout(unit) -> None:
    unit.pylons = {
        1: {"CLSID": AIM120C},
        3: {"CLSID": HARM},
        4: {"CLSID": HARM},
        6: {"CLSID": HARM},
        7: {"CLSID": HARM},
        9: {"CLSID": AIM120C},
        10: {"CLSID": HTS},
    }


def _msg(mission: Mission, text: str, seconds: int = 50) -> action.MessageToAll:
    mission.translation.set_string(text, text)
    return action.MessageToAll(String(text), seconds, clearview=False)


def _zone_brief(
    mission: Mission,
    position: Point,
    radius_m: int,
    unit_id: int,
    flag: int,
    text: str,
    seconds: int = 50,
) -> None:
    """One-shot popup when the player enters a trigger zone (guided phase gate)."""
    zone = mission.triggers.add_triggerzone(
        position, radius_m, hidden=True, name=f"TRN_Z{flag}",
    )
    tr = triggers.TriggerCondition(comment=f"training zone {flag}")
    tr.add_condition(condition.UnitInZone(unit_id, zone.id))
    tr.add_condition(condition.FlagIsFalse(flag))
    tr.add_action(_msg(mission, text, seconds))
    tr.add_action(action.SetFlag(flag))
    mission.triggerrules.triggers.append(tr)


def _on_group_dead(
    mission: Mission,
    group_id: int,
    flag: int,
    actions: list,
) -> None:
    tr = triggers.TriggerCondition(comment=f"group dead {group_id}")
    tr.add_condition(condition.GroupDead(group_id))
    tr.add_condition(condition.FlagIsFalse(flag))
    for act in actions:
        tr.add_action(act)
    tr.add_action(action.SetFlag(flag))
    mission.triggerrules.triggers.append(tr)


def build_training(spec: dict, out_path: str | None = None) -> str:
    """Build the HTS/HARM training mission. Returns saved .miz path.

    ``spec`` must already be normalized (``type`` = ``sead_training``).
    """
    terrain_name = spec["terrain"]
    terrain_cls = TERRAIN_CLASSES.get(terrain_name)
    if terrain_cls is None:
        raise SpecError(f"terrain {terrain_name!r} not supported for training")

    rng = random.Random(spec["seed"])
    catalog = load_data("catalog")
    m = Mission(terrain_cls())

    # Clear midday training weather.
    m.start_time = datetime(2016, 6, 15, 12, 0, tzinfo=timezone.utc)
    m.weather.wind_at_ground = Wind(270, 4)
    m.weather.clouds_density = 0

    blue = m.country("USA")
    red = m.country("Russia")
    blue_ap, red_ap = _pick_airbase_pair(m.terrain, spec, rng)
    heading = blue_ap.position.heading_between_point(red_ap.position)

    # Two sites along the threat axis; names are internal only.
    site_a = red_ap.position.point_from_heading((heading + 180) % 360, 8 * NM)
    site_b = site_a.point_from_heading(heading, 18 * NM)

  # Air start ~32 nm back, already oriented toward the first site.
    spawn = site_a.point_from_heading((heading + 180) % 360, 32 * NM)
    alt_ft = 12000
    fg = m.flight_group_inflight(
        blue, PLAYER_GROUP, aircraft_class("F-16C_50"), spawn,
        int(alt_ft * FT), maintask=SEAD,
    )
    player = fg.units[0]
    player.set_client()
    player.skill = Skill.Player
    _apply_training_loadout(player)

    # Route: hold point -> site A -> site B area.
    wp_hold = spawn.point_from_heading(heading, 12 * NM)
    fg.add_waypoint(wp_hold, int(alt_ft * FT))
    fg.add_waypoint(site_a, int(10000 * FT))
    fg.add_waypoint(site_b, int(10000 * FT))

    sam_a = spawn_sam_site(
        _Ctx(m, spec, rng, catalog, red, heading, site_a),
        "SA-2", site_a, "TRN ALPHA",
    )[0]
    sam_b = spawn_sam_site(
        _Ctx(m, spec, rng, catalog, red, heading, site_b),
        "SA-3", site_b, "TRN BRAVO",
    )[0]

    # --- Scripted training flow (popups are the lesson; sites are discovered in flight) ---
    intro = (
        "HTS / HARM TRAINING\n\n"
        "Loadout: 4x AGM-88, AIM-120C on wingtips only, HTS on station 10.\n"
        "AG master mode. Sensor select toggles HTS (6) vs TGP.\n\n"
        "Fly the route. Briefings will appear as you reach each phase."
    )
    tr0 = triggers.TriggerStart(comment="training intro")
    tr0.add_action(_msg(m, intro, 60))
    m.triggerrules.triggers.append(tr0)

    _zone_brief(
        m, wp_hold, 6000, player.id, 1,
        "PHASE 1 — HTS SEARCH\n\n"
        "Master mode AG. Press 6 for HTS (not HARM yet).\n"
        "DTK on the left DED: set range scale with DEP/RTN if the picture is empty.\n"
        "Fly toward the route — emitters appear as symbols when their radars are active.\n"
        "Cursor over a symbol: read the emitter line on the DED.",
        55,
    )

    _zone_brief(
        m, site_a.point_from_heading((heading + 180) % 360, 10 * NM), 8000, player.id, 2,
        "PHASE 2 — HANDOFF & SHACK\n\n"
        "With HTS cursor on a live emitter:\n"
        "  • TMS FWD (short) = handoff to HARM seeker\n"
        "  • Switch to HARM (7), select HAS or POS as briefed\n"
        "SHACK on the DED means the HARM has a valid seeker track — you may fire.\n"
        "No SHACK = do not launch. Break turn, reposition, hand off again.",
        60,
    )

    rearm_lua = (
        f"local g=Group.getByName('{PLAYER_GROUP}'); "
        "if g then trigger.action.rearmGroup(g) end"
    )
    _on_group_dead(
        m, sam_a.id, 10,
        [
            _msg(
                m,
                "PHASE 1 COMPLETE — REARMING\n\n"
                "First site is down. Your HARM load is being replenished.\n"
                "Continue to the next training area on the route.",
                45,
            ),
            action.DoScript(String(rearm_lua)),
        ],
    )

    _zone_brief(
        m, site_b.point_from_heading((heading + 180) % 360, 12 * NM), 8000, player.id, 3,
        "PHASE 3 — SECOND SITE\n\n"
        "Same flow: HTS (6) to build the picture, handoff, HARM (7), confirm SHACK, shoot.\n"
        "Multiple emitters? Cursor the track radar first, then mop up launchers.",
        50,
    )

    _on_group_dead(
        m, sam_b.id, 11,
        [
            _msg(
                m,
                "TRAINING COMPLETE\n\n"
                "Both sites suppressed. You now have the full HTS-to-HARM chain:\n"
                "HTS picture → handoff → SHACK → launch.\n"
                "RTB when ready.",
                50,
            ),
        ],
    )

    b = spec.get("briefing") or {}
    title = b.get("title") or "HTS / HARM Qualification"
    situation = b.get("situation") or (
        "A scripted training sortie over friendly range airspace. "
        "Follow the route; instructions will appear in sequence."
    )
    objective = b.get("objective") or (
        "Complete each training phase as briefed. "
        "Suppress all assigned sites along the route."
    )
    m.set_description_text(
        f"{title}\n\n{situation}\n\nOBJECTIVE: {objective}\n\n"
        f"(DCSActualIntel training mission, seed {spec['seed']})"
    )

    if out_path is None:
        out_path = f"sead_training_{terrain_name}_{spec['seed']}.miz"
    from pathlib import Path
    from ..detect import detect
    ownership = detect()
    if ownership.get("saved_games") and not Path(out_path).is_absolute():
        out_path = str(Path(ownership["saved_games"]) / "Missions" / Path(out_path).name)
    m.save(out_path)
    return out_path


class _Ctx:
    """Minimal stand-in for BuildContext used only by spawn_sam_site."""

    def __init__(self, mission, spec, rng, catalog, red, heading, objective):
        self.mission = mission
        self.spec = spec
        self.rng = rng
        self.catalog = catalog
        self.red = red
        self.heading = heading
        self.objective = objective

    def scatter(self, center, max_nm):
        return center.point_from_heading(
            self.rng.uniform(0, 360), self.rng.uniform(0, max_nm) * NM,
        )
