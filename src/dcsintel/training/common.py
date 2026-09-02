"""Shared trigger helpers and F-16 loadout for training missions."""

from __future__ import annotations

from dcs import action, condition, triggers
from dcs.mission import Mission
from dcs.translation import String

# F-16C pylon map (Block 50): wingtips = 1 & 9, HTS = 10.
AIM120C = "{40EF17B7-F508-45de-8566-6FFECC0C1AB8}"
HARM = "{B06DD79A-F21E-4EB9-BD9D-AB3844618C93}"
HTS = "{AN_ASQ_213}"

PLAYER_GROUP = "Viper 1"
FLAG_REARMED = 50


def apply_f16_sead_loadout(unit) -> None:
    unit.pylons = {
        1: {"CLSID": AIM120C},
        3: {"CLSID": HARM},
        4: {"CLSID": HARM},
        6: {"CLSID": HARM},
        7: {"CLSID": HARM},
        9: {"CLSID": AIM120C},
        10: {"CLSID": HTS},
    }


def message(mission: Mission, text: str, seconds: int = 50) -> action.MessageToAll:
    mission.translation.set_string(text, text)
    return action.MessageToAll(String(text), seconds, clearview=False)


def zone_brief(
    mission: Mission,
    position,
    radius_m: int,
    unit_id: int,
    flag: int,
    text: str,
    seconds: int = 50,
) -> None:
    """One-shot popup when the player enters a trigger zone."""
    zone = mission.triggers.add_triggerzone(
        position, radius_m, hidden=True, name=f"TRN_Z{flag}",
    )
    tr = triggers.TriggerCondition(comment=f"training zone {flag}")
    tr.add_condition(condition.UnitInZone(unit_id, zone.id))
    tr.add_condition(condition.FlagIsFalse(flag))
    tr.add_action(message(mission, text, seconds))
    tr.add_action(action.SetFlag(flag))
    mission.triggerrules.triggers.append(tr)


def on_group_dead(
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


def resolve_output_path(spec: dict, default_name: str, out_path: str | None) -> str:
    from pathlib import Path

    from ..detect import detect

    if out_path is None:
        out_path = default_name
    ownership = detect()
    if ownership.get("saved_games") and not Path(out_path).is_absolute():
        out_path = str(Path(ownership["saved_games"]) / "Missions" / Path(out_path).name)
    return out_path
