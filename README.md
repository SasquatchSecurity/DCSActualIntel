# DCSActualIntel

**AI-driven random mission generator for DCS World.**

Ask your AI coding agent (Cursor, Claude Code, GitHub Copilot, or anything
else that supports [Agent Skills](https://agentskills.io)) for *"a random
SEAD mission for my F-16"* and get a valid, flyable `.miz` in your
`Saved Games/DCS/Missions` folder - built around the aircraft modules and
terrains you actually own.

The name is a play on **DCS AI**: the AI supplies the *actual intel* - the
scenario, threat picture, and briefing - while deterministic Python
(built on [pydcs](https://github.com/pydcs/dcs)) guarantees the mission
file is always valid.

## Mission types

| Type | You fly | Opposition |
|---|---|---|
| `dogfight` | BFM setup, usually air-start | 1-8 enemy fighters, head-on merge |
| `cap` | A patrol station | Strike package + escorts pushing your field |
| `sead` | Iron Hand / DEAD tasking | Layered SAM network + EWR, optional red CAP |
| `strike` | Precision attack | Defended supply concentration |
| `escort` | Bomber escort | Interceptors cutting the bomber route |
| `cas` | Troops-in-contact support | Armor column with mobile SHORAD |
| `intercept` | QRA scramble from the ramp | Raid already inbound to your field |

Every mission supports two eras (`modern`, `coldwar`) that change the entire
threat catalog, plus randomized (or specified) weather, time of day, terrain,
and geometry. Same spec + same seed = byte-identical mission, every time.

## How it works

```
You: "give me a cold-war CAP mission for the F-14"
          |
          v
 AI agent (via the dcs-mission-generator skill)
          |  1. dcsintel detect         <- what do you own?
          |  2. reads CAP doctrine doc  <- what makes a good CAP mission?
          |  3. writes a MissionSpec    <- creative choices, briefing text
          v
 dcsintel generate --spec spec.json     <- deterministic Python + pydcs
          |
          v
 Saved Games/DCS/Missions/cap_Caucasus_1337.miz   (validated, ready to fly)
```

The **MissionSpec** is the contract between the two halves: a JSON document
where only `"type"` is required and every omitted field gets a seeded random
value. The AI is never allowed to write mission Lua by hand; the Python side
is never asked to be creative.

## Installation

Requires **Python 3.10+** (3.13 works - see [Troubleshooting](#troubleshooting))
and Git. A DCS World install on the same machine is recommended (for module
auto-detection) but not required - see
[Module & terrain detection](#module--terrain-detection).

### Full install (recommended: CLI + agent skill)

```bash
git clone https://github.com/SasquatchSecurity/DCSActualIntel.git
cd DCSActualIntel
pip install .
```

> Prefer isolation? Create a venv first (`python -m venv .venv` then
> `.venv\Scripts\activate` on Windows / `source .venv/bin/activate`
> elsewhere) and run the same `pip install .` inside it.

Then install the agent skill into your harness(es):

```bash
python scripts/install_skills.py                    # all harnesses, user-wide
python scripts/install_skills.py --harness cursor   # just Cursor
python scripts/install_skills.py --harness claude   # just Claude Code
python scripts/install_skills.py --scope project    # commit into a repo instead
```

| Harness | User scope | Project scope |
|---|---|---|
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| GitHub Copilot | - | `.github/skills/` |

Restart your agent session afterward, then just ask for a mission.

To update later: `git pull`, `pip install .`, and rerun
`scripts/install_skills.py` (it overwrites the installed skill copy).

### CLI-only install (no clone, no agent skill)

If you just want the `dcsintel` command:

```bash
pip install git+https://github.com/SasquatchSecurity/DCSActualIntel.git
```

## Using it with your AI agent

Once the skill is installed, talk to your agent in plain English:

> *"Generate a random SEAD mission for my F-16."*
> *"Make me a cold-war dogfight, guns only vibes, something close-in."*
> *"I have 30 minutes - quick intercept scramble, surprise me on everything else."*

The agent will detect your modules, read the doctrine doc for that mission
type, write a MissionSpec (including a hand-written briefing), generate the
`.miz` into `Saved Games/DCS/Missions/`, validate it, and hand you the path
plus the tasking summary. Repeat a mission you liked by giving the agent the
seed it reported.

## Using the CLI directly (no AI required)

```bash
# What do I own? (cached; --refresh to rescan after buying modules)
dcsintel detect

# Fastest possible mission: one flag
dcsintel generate --type dogfight

# Pin things down
dcsintel generate --type sead --aircraft F-16C_50 --terrain Syria --seed 42

# Full creative control via a spec file
dcsintel generate --spec my_mission.json

# Sanity-check any generated mission
dcsintel validate "C:/Users/you/Saved Games/DCS/Missions/sead_Syria_42.miz"
```

All commands print JSON (designed to be equally readable by humans and
agents). Missions land in `Saved Games/DCS/Missions/` unless `--out` says
otherwise. On failure you get exit code 1 and `{"error": "..."}` with an
actionable message.

### CLI reference

`dcsintel detect`

| Flag | Meaning |
|---|---|
| `--refresh` | Ignore the cache (`~/.dcsintel/detected.json`) and rescan |

`dcsintel generate` (requires `--spec` or `--type`)

| Flag | Meaning |
|---|---|
| `--spec FILE` | MissionSpec JSON file (full creative control) |
| `--type TYPE` | Mission type; everything else randomized |
| `--terrain NAME` | Override terrain (e.g. `Syria`) |
| `--aircraft ID` | Override player aircraft (e.g. `F-16C_50`) |
| `--seed N` | Reproducible randomness; same spec+seed = identical .miz |
| `--out PATH` | Output path (default: `Saved Games/DCS/Missions/`) |
| `--no-ownership-check` | Skip module/terrain ownership validation |

CLI flags override the same fields in `--spec`, so you can keep a favorite
spec file and vary just the seed or aircraft per run.

`dcsintel validate MISSION.miz` - reloads the file with pydcs and reports:

```json
{
  "path": "intercept_Caucasus_2026.miz",
  "terrain": "Caucasus",
  "player_aircraft": "F-15C",
  "start_time": "1979-05-11 19:00:00",
  "red_units": 4,
  "load_messages": []
}
```

### MissionSpec reference

```json
{
  "type": "sead",
  "terrain": "Caucasus",
  "era": "modern",
  "time_of_day": "dawn",
  "weather": "scattered",
  "player": {"aircraft": "F-16C_50", "start": "hot", "airbase": "Kutaisi"},
  "enemy": {"skill": "Good", "fighters": 2, "cap_flights": 1,
            "sam_types": ["SA-10", "SA-6"]},
  "support": {"awacs": true, "tanker": true},
  "distance_nm": 80,
  "briefing": {"title": "...", "situation": "...", "objective": "..."},
  "seed": 42
}
```

| Field | Values | Default when omitted |
|---|---|---|
| `type` (required) | `dogfight` `cap` `sead` `strike` `escort` `cas` `intercept` | - |
| `terrain` | any owned terrain | random owned |
| `era` | `modern`, `coldwar` | random |
| `time_of_day` | `dawn` `day` `dusk` `night` `random` | random (day-weighted) |
| `weather` | `clear` `scattered` `broken` `overcast` `rain` `random` | random |
| `player.aircraft` | any owned flyable module id | random owned |
| `player.start` | `cold` `hot` `runway` `air` | `hot` (`air` for dogfight) |
| `player.airbase` | airbase name on the terrain | picked to fit `distance_nm` |
| `enemy.skill` | `Average` `Good` `High` `Excellent` `Random` | `Good` |
| `enemy.fighters` | 1-8 | type-appropriate |
| `enemy.cap_flights` | 0-4 | 0-1 |
| `enemy.sam_types` | era-appropriate SAM keys (see below) | random 1-3 |
| `support.awacs`, `support.tanker` | booleans | type-appropriate |
| `distance_nm` | 15-300 | type-appropriate |
| `briefing.*` | free text | generated |
| `seed` | integer | random |

SAM keys: `SA-2` `SA-3` `SA-6` `SA-8` `SA-10` `SA-11` `SA-15` `SA-19` `AAA`
(cold war allows `SA-2` `SA-3` `SA-6` `AAA`).

Validation errors are written for agents: requesting Nevada when you only own
Caucasus returns `terrain 'Nevada' is not owned. Owned terrains: ['Caucasus']`,
so an agent can self-correct without you touching anything.

## Module & terrain detection

`dcsintel detect` finds your DCS install via (in order): the
`DCSINTEL_DCS_PATH` environment variable, `dcsintel.config.json`, the Windows
registry (standalone stable/openbeta and Steam), and standard filesystem
locations. It then reads `Mods/aircraft/` and `Mods/terrains/` to determine
what you own. `Su-25T` and `TF-51D` are always included (free with the base
game). Typical output:

```json
{
  "dcs_install": "C:\\Program Files\\Eagle Dynamics\\DCS World",
  "saved_games": "C:\\Users\\you\\Saved Games\\DCS",
  "modules": ["A-10C_2", "F-15C", "F-16C_50", "FA-18C_hornet", "Su-25T", "TF-51D"],
  "terrains": ["Caucasus", "Nevada", "Syria"],
  "unknown_module_folders": [],
  "source": "scan"
}
```

Supported terrains: Caucasus, Nevada, Normandy, Persian Gulf, Syria,
Mariana Islands, Falklands (South Atlantic), Sinai, Kola, Germany (Cold War),
The Channel. Detection is Windows-only (DCS is Windows-only), but mission
*generation* runs anywhere via the config-file fallback below - handy for
building missions on a laptop or in CI.

No DCS install on this machine? Create `dcsintel.config.json` next to where
you run the tool (or at `~/.dcsintel/config.json`):

```json
{
  "modules": ["F-16C_50", "FA-18C_hornet", "Su-25T"],
  "terrains": ["Caucasus", "Syria"]
}
```

You can also *supplement* a scan with `"extra_modules"` / `"extra_terrains"`,
or point at a non-standard install with `"dcs_install"`.

If detect reports `unknown_module_folders`, a module folder isn't in the
mapping yet - add it to `src/dcsintel/data/modules.json` and open a PR.

## Repository layout

```
skills/dcs-mission-generator/   The portable Agent Skill (SKILL.md + doctrine
                                docs per mission type). Copied verbatim by
                                scripts/install_skills.py.
src/dcsintel/
  cli.py                        dcsintel detect | generate | validate
  detect.py                     Install discovery + module/terrain scan
  spec.py                       MissionSpec validation & random fill (seeded)
  builder.py                    Shared plumbing: terrain, weather, airbases,
                                player flight, AWACS/tanker, briefing, save
  missions/<type>.py            What makes a SEAD a SEAD (one file per type)
  data/catalog.json             Unit catalogs: SAM site templates, aircraft
                                by era/role, ground units
  data/modules.json             Mods/aircraft folder -> flyable module ids
tests/                          pytest suite (detection, validation, and a
                                build-save-reload golden path per type)
docs/superpowers/specs/         Design documents
```

### Adding a mission type

1. Create `src/dcsintel/missions/<name>.py` with `PLAYER_TASK` and `build(ctx)`
   (see any existing type; `BuildContext` gives you airbases, rng, catalog,
   and geometry helpers).
2. Register it in `missions/__init__.py::BUILDERS` and add the name to
   `spec.py::MISSION_TYPES`.
3. Write `skills/dcs-mission-generator/mission-types/<name>.md`.
4. The parametrized test in `tests/test_generate.py` picks it up automatically.

### Adding units, SAMs, or modules

Edit the JSON in `src/dcsintel/data/` - no code changes needed. Unit strings
are exact DCS type names (pydcs `plane_map` / `vehicle_map` keys).

## Testing

```bash
pip install -e ".[dev]"
pytest
```

The suite builds, saves, and *reloads* a mission of every type, so a pydcs
API drift or bad unit name fails loudly in CI rather than silently in DCS.

## Troubleshooting

**`pip install pydcs` crashes on import (KeyError: 'country_list')** -
PyPI's pydcs 0.15.0 is incompatible with Python 3.13 (PEP 667 changed
`exec()`/`locals()` semantics and broke its livery scanner). This project
pins a fixed pydcs commit from GitHub in `pyproject.toml`, so installing
*this* package is sufficient. Don't install pydcs separately.

**"no owned modules detected"** - run `dcsintel detect --refresh`; if your
install is somewhere exotic, set `DCSINTEL_DCS_PATH` or write
`dcsintel.config.json` (see above).

**Mission won't fit a helicopter** - set `distance_nm` to 20-35 in the spec;
defaults assume fixed-wing transit speeds.

**Stale ownership after buying a module** - detection is cached at
`~/.dcsintel/detected.json`; run `dcsintel detect --refresh`.

## Roadmap

- Carrier ops (Case I/III) mission type
- Multiplayer client slot layouts
- Kneeboard generation with the threat picture
- WW2 era catalog

## Contributing

Issues and PRs welcome. The lowest-friction contributions are pure data:
new module folder mappings in `data/modules.json` (paste your
`unknown_module_folders` output) and new units or SAM templates in
`data/catalog.json`. For new mission types, see
[Adding a mission type](#adding-a-mission-type) - the test suite picks new
types up automatically. Please run `pytest` before opening a PR.

**Privacy standard:** no committed file may contain personal or
environment-identifying details (real user-profile paths, hostnames, install
paths from your machine). Use placeholders like `C:/Users/you/...` in docs -
`tests/test_no_pii.py` enforces this, and command output pasted into
documentation is the most common way leaks happen, so scrub it first.

## License

MIT - see [LICENSE](LICENSE).
