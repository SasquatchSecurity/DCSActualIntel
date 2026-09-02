---
name: dcs-mission-generator
description: Generate random, flyable DCS World missions (.miz files) of a chosen style - dogfight, CAP, SEAD/DEAD, strike, bomber escort, CAS, or intercept - matched to the aircraft modules and terrains the user owns. Use when the user asks to create, generate, or randomize a DCS World mission, asks for a training sortie of a specific type, or mentions .miz generation.
---

# DCS Mission Generator

Generates a valid `.miz` in three commands. You make the creative choices
(scenario, threats, briefing); the `dcsintel` Python CLI guarantees the file
format. Never write mission Lua or `.miz` contents by hand.

## Prerequisites (first use only)

`dcsintel` must be importable. If `dcsintel --help` fails, see
`docs/INSTALL.md` in the repo (Python 3.10+, `pip install .`, optional skill
install). Quick path:

```bash
pip install <path-to-DCSActualIntel-repo>
# or: pip install git+https://github.com/SasquatchSecurity/DCSActualIntel.git
```

Full CLI and MissionSpec reference: `docs/USAGE.md`.

## Workflow

### 1. Detect what the user owns

```bash
dcsintel detect          # add --refresh after the user installs new modules
```

Returns owned flyable `modules`, `terrains`, and the Saved Games path.
If `source` is `"none"`, tell the user to either install DCS or create
`dcsintel.config.json` with `{"modules": [...], "terrains": [...]}`.

### 2. Read the doctrine for the requested mission type

Read `mission-types/<type>.md` (same folder as this file) before authoring
the spec. It covers appropriate threats, distances, and example specs for:
`dogfight`, `cap`, `sead`, `strike`, `escort`, `cas`, `intercept`.

If the user's request doesn't name a type, map it (e.g. "kill some SAMs" ->
sead, "practice BFM" -> dogfight) or pick one at random if they say
"surprise me".

### 3. Ask only what is genuinely open

If the user has several owned aircraft that fit the mission, ask which one
(or offer "random"). Don't ask about things the spec can randomize (weather,
time, terrain) unless the user seems to care.

### 4. Author the MissionSpec and generate

Write a JSON spec file. Only `"type"` is required - every omitted field is
filled with seeded random choices. Be creative in the `briefing` fields;
that text is what the pilot reads on the briefing screen.

```json
{
  "type": "sead",
  "player": {"aircraft": "F-16C_50", "start": "hot"},
  "era": "modern",
  "enemy": {"sam_types": ["SA-10", "SA-11"], "cap_flights": 1},
  "briefing": {
    "title": "Iron Hand over the Valley",
    "situation": "Two SAM battalions moved up overnight to cover the enemy advance.",
    "objective": "Destroy the SA-10 and SA-11 sites at waypoint 2."
  },
  "seed": 20260831
}
```

```bash
dcsintel generate --spec spec.json
```

Quick one-liners also work: `dcsintel generate --type dogfight --aircraft F-15C`.

Output lands in `Saved Games/DCS/Missions/` by default (`--out` to override).

### 5. Validate and report

```bash
dcsintel validate "<path from generate output>"
```

Then tell the user: the `.miz` path, the mission objective, notable threats,
and the seed (same spec + seed regenerates the identical mission).

## Error handling

Every command prints JSON. On failure you get `{"error": "..."}` with an
actionable message (e.g. unowned terrain listing owned ones, era-inappropriate
SAM types listing allowed ones). Fix the spec and rerun - do not hand-edit
the `.miz`.

## Spec field reference

| Field | Values | Default |
|---|---|---|
| `type` (required) | `dogfight` `cap` `sead` `strike` `escort` `cas` `intercept` | - |
| `terrain` | owned terrain name (e.g. `Caucasus`, `Syria`) | random owned |
| `era` | `modern`, `coldwar` (drives threat catalog + date) | random |
| `time_of_day` | `dawn` `day` `dusk` `night` `random` | random, day-weighted |
| `weather` | `clear` `scattered` `broken` `overcast` `rain` `random` | random |
| `player.aircraft` | owned module id (e.g. `F-16C_50`, `FA-18C_hornet`) | random owned |
| `player.start` | `cold` `hot` `runway` `air` (no `air` for intercept) | `hot` (`air` for dogfight) |
| `player.airbase` | airbase name on the terrain | random suitable |
| `enemy.skill` | `Average` `Good` `High` `Excellent` `Random` | `Good` |
| `enemy.fighters` | 1-8 enemy fighter aircraft | type-appropriate |
| `enemy.cap_flights` | 0-4 extra red CAP flights | 0-1 |
| `enemy.sam_types` | see mission-types/sead-dead.md | era-appropriate random |
| `support.awacs` / `support.tanker` | booleans | type-appropriate |
| `distance_nm` | 15-300, base-to-objective | type-appropriate |
| `briefing.title/situation/objective` | free text - be creative | generated |
| `seed` | integer; same spec+seed = identical mission | random |

Aircraft ids are exact DCS type names: `F-16C_50`, `FA-18C_hornet`, `F-15C`,
`A-10C_2`, `F-14B`, `Su-25T`, `MiG-21Bis`, `AH-64D_BLK_II`, `Ka-50_3`, etc.
`dcsintel detect` output is always the source of truth for what's available.
