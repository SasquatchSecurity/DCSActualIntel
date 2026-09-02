# FAQ

Short answers to common search-style questions. Details live in [Installation](INSTALL.md) and [Usage](USAGE.md).

## What is DCSActualIntel?

A **DCS World mission generator**: it builds flyable `.miz` files for the Mission Editor from a JSON spec. Random sorties (SEAD, CAP, strike, CAS, intercept, and more) and scripted **F-16 training** missions. Output goes to `Saved Games/DCS/Missions/`.

## How do I generate a random DCS mission?

Install the tool ([Installation](INSTALL.md)), then either:

```bash
dcsintel generate --type sead --aircraft F-16C_50 --terrain Caucasus --seed 42
```

or ask an AI agent with the `dcs-mission-generator` skill installed. The agent writes a MissionSpec; `dcsintel generate` builds the `.miz`.

## How do I make a random SEAD / Iron Hand mission?

```bash
dcsintel generate --type sead --difficulty contested --seed 100
```

Set `enemy.sam_types` in a spec file if you want specific SAM systems. See [Usage — MissionSpec](USAGE.md#missionspec-random-play).

## Does this work with Cursor or Claude Code?

Yes. Install the agent skill (`python scripts/install_skills.py`), restart the agent, and ask for a mission in plain language. The skill reads doctrine docs per mission type and calls `dcsintel` for you. Works with any host that supports [Agent Skills](https://agentskills.io).

## How does it know which DCS modules I own?

```bash
dcsintel detect
```

It scans your DCS install (or reads `dcsintel.config.json` if you have no local install). Missions only use aircraft and terrains you own.

## What is a `.miz` file?

DCS World’s mission package — what the Mission Editor opens. This project never asks you to edit mission Lua by hand; [pydcs](https://github.com/pydcs/dcs) writes valid files from Python.

## Can I replay the same mission?

Yes. Same MissionSpec JSON and same `seed` produce the same `.miz` every time. Save the seed the CLI prints.

## What are F-16 training missions?

Scripted syllabi with in-cockpit popups — HTS/HARM SEAD, JDAM, Maverick, CAS, CAP, escort. Layout randomizes per seed; the procedure stays the same.

```bash
dcsintel training --curriculum sead_viper --difficulty routine --seed 1001
```

## Do I need pydcs installed separately?

No. `pip install .` pulls a pinned pydcs commit from GitHub. Do not install the broken PyPI 0.15.0 wheel on Python 3.13. See [Installation — Troubleshooting](INSTALL.md#troubleshooting).

---

[Installation](INSTALL.md) · [Usage](USAGE.md) · [README](../README.md)
