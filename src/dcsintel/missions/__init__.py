"""Mission-type builders.

Each module exposes:

- ``PLAYER_TASK``: the pydcs main task assigned to the player flight
  (drives default loadouts and AI wingman behavior).
- ``build(ctx)``: adds the type-specific content to the mission using the
  precomputed :class:`dcsintel.builder.BuildContext`.

To add a new mission type: create a module here, register it in
``BUILDERS``, add the type name to ``dcsintel.spec.MISSION_TYPES``, and
write a matching skill doc in ``skills/dcs-mission-generator/mission-types/``.
"""

from . import cap, cas, dogfight, escort, intercept, sead, strike

BUILDERS = {
    "dogfight": dogfight,
    "cap": cap,
    "sead": sead,
    "strike": strike,
    "escort": escort,
    "cas": cas,
    "intercept": intercept,
}
