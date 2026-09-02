"""Shared trigger helpers and F-16 loadout for training missions."""

from __future__ import annotations

from dcs import action, condition, triggers
from dcs.mission import Mission

# F-16C pylon map (Block 50): wingtips = 1 & 9, targeting pod = 10.
AIM120C = "{40EF17B7-F508-45de-8566-6FFECC0C1AB8}"
HARM = "{B06DD79A-F21E-4EB9-BD9D-AB3844618C93}"
HTS = "{AN_ASQ_213}"
LITENING = "{A111396E-D3E8-4b9c-8AC9-2432489304D5}"
GBU38 = "{GBU-38}"
AGM65D = "{444BA8AE-82A7-4345-842E-76154EFCCA47}"
HYDRA_M151 = "{BRU42LS_2*LAU131_HYDRA_70_M151_L}"

PLAYER_GROUP = "Viper 1"
FLAG_REARMED = 50
FLAG_INTRO_ACK = 100
INTRO_DISPLAY_SECONDS = 90
INTRO_ACK_SUFFIX = "\n\nSimulation is paused. Press SPACE when you are ready to begin."

_ASCII_SUBS = (
    ("\u2014", "-"),  # em dash
    ("\u2013", "-"),  # en dash
    ("\u2022", "-"),  # bullet
    ("\u2192", "->"),  # arrow
)


def ascii_text(text: str) -> str:
    """DCS trigger/briefing strings should be plain ASCII.

    Non-ASCII punctuation in training popups is normalized to ASCII for DCS.
    """
    for old, new in _ASCII_SUBS:
        text = text.replace(old, new)
    return text.encode("ascii", "replace").decode("ascii")


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


def apply_f16_jdam_loadout(unit) -> None:
    unit.pylons = {
        1: {"CLSID": AIM120C},
        3: {"CLSID": GBU38},
        4: {"CLSID": GBU38},
        6: {"CLSID": GBU38},
        7: {"CLSID": GBU38},
        9: {"CLSID": AIM120C},
        10: {"CLSID": LITENING},
    }


def apply_f16_maverick_loadout(unit) -> None:
    unit.pylons = {
        1: {"CLSID": AIM120C},
        3: {"CLSID": AGM65D},
        4: {"CLSID": AGM65D},
        6: {"CLSID": AGM65D},
        7: {"CLSID": AGM65D},
        9: {"CLSID": AIM120C},
        10: {"CLSID": LITENING},
    }


def apply_f16_cas_loadout(unit) -> None:
    unit.pylons = {
        1: {"CLSID": AIM120C},
        3: {"CLSID": HYDRA_M151},
        4: {"CLSID": HYDRA_M151},
        9: {"CLSID": AIM120C},
        10: {"CLSID": LITENING},
    }


def apply_f16_cap_loadout(unit) -> None:
    unit.pylons = {
        1: {"CLSID": AIM120C},
        2: {"CLSID": AIM120C},
        3: {"CLSID": AIM120C},
        7: {"CLSID": AIM120C},
        9: {"CLSID": AIM120C},
    }


def message(mission: Mission, text: str, seconds: int = 50) -> action.MessageToAll:
    text = ascii_text(text)
    # Must use DictKey_Translation_* ids. Using the message body as the key
    # produces invalid multiline dictionary entries and breaks DCS on load.
    string = mission.translation.create_string(text)
    return action.MessageToAll(string, seconds, clearview=False)


def add_training_intro(mission: Mission, intro_text: str) -> None:
    """Show the training briefing popup and pause until the pilot presses SPACE."""
    tr = triggers.TriggerStart(comment="training intro")
    tr.add_action(message(mission, intro_text + INTRO_ACK_SUFFIX, INTRO_DISPLAY_SECONDS))
    tr.add_action(action.StartWaitUserResponse(FLAG_INTRO_ACK))
    mission.triggerrules.triggers.append(tr)


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
