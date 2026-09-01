"""dcsintel: AI-driven random mission generator for DCS World.

The package exposes three operations, mirrored by the ``dcsintel`` CLI:

- :func:`dcsintel.detect.detect` - find the DCS install and enumerate
  owned flyable modules and terrains.
- :func:`dcsintel.builder.build_mission` - turn a MissionSpec (a plain
  dict, usually authored by an AI agent) into a saved ``.miz`` file.
- :func:`dcsintel.builder.validate_miz` - reload a generated ``.miz``
  and sanity-check it.

Design note: everything fragile (the .miz format, unit type names,
airbase data) lives here in Python on top of pydcs. Everything creative
(scenario, briefing, parameter choice) is left to the caller.
"""

__version__ = "0.1.0"
