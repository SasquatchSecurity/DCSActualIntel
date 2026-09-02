# Usage

`dcsintel` has four commands: `detect`, `generate`, `training`, and `validate`. All print JSON on stdout. Exit code 0 on success; failures return `{"error": "..."}` and exit 1.

Missions save to `Saved Games/DCS/Missions/` unless you pass `--out`.

---

## With an AI agent

After you [install the skill](INSTALL.md#agent-skill), talk to the agent like you would a human wingman:

- *"Random SEAD for my F-16 on Syria."*
- *"Cold-war dogfight, close merge."*
- *"F-16 JDAM training, routine tier, seed 2001."*

The agent should:

1. Run `dcsintel detect` (or use cached ownership).
2. Read the doctrine file for the mission type under `skills/dcs-mission-generator/mission-types/`.
3. Write a spec JSON with briefing text filled in.
4. Run `dcsintel generate --spec ...` or `dcsintel training ...`.
5. Run `dcsintel validate` on the output and give you the path plus seed.

Same spec and seed always produce the same `.miz`. Save the seed if you want to refly a sortie.

---

## CLI quick examples

```bash
# Inventory
dcsintel detect
dcsintel detect --refresh

# Random mission (one flag)
dcsintel generate --type sead

# Pin aircraft, map, threat tier, seed
dcsintel generate --type sead --aircraft F-16C_50 --terrain Syria --difficulty contested --seed 42

# Full control from a file
dcsintel generate --spec my_mission.json

# F-16 training syllabus
dcsintel training --curriculum sead_viper --difficulty routine --seed 1001

# Sanity check
dcsintel validate "C:/Users/you/Saved Games/DCS/Missions/sead_Syria_42.miz"
```

CLI flags override the same fields inside `--spec`.

---

## Threat tiers (random play)

Used by `dcsintel generate`. Briefing screen labels are plain English:

| Tier ID | Label | Rough picture |
|---|---|---|
| `training` | TRAINING | Light SAMs, low skill, clear weather, full support |
| `routine` | ROUTINE | Default — typical threats |
| `contested` | CONTESTED | Heavier IADS, CAP, worse weather, no tanker |
| `high_threat` | HIGH THREAT | Stacked SAMs and CAP, poor weather, no AWACS/tanker |

Set in spec: `"difficulty": "contested"` or `--difficulty contested`.

### Scenario twists

Optional modifiers. Auto-picked at higher tiers, or set explicitly:

```json
"twists": ["night_ops", "bandits_airborne"]
```

| Twist | Effect |
|---|---|
| `low_visibility` | Overcast weather |
| `night_ops` | Night start |
| `bandits_airborne` | Extra red CAP flight |
| `thin_support` | No AWACS or tanker |
| `compressed_timeline` | Shorter transit to the target area |

Explicit spec fields (weather, enemy skill, support flags, etc.) are not overwritten by difficulty or twists.

---

## F-16 training

`dcsintel training` builds scripted sorties: fixed popups and procedures, random geometry per seed.

| Curriculum | Munition / focus |
|---|---|
| `sead_viper` | HTS → HARM SEAD |
| `jdam_viper` | GBU-38 JDAM |
| `maverick_viper` | AGM-65 Maverick |
| `cas_viper` | TGP ID, rockets, TIC |
| `cap_viper` | CAP station, AIM-120 BVR |
| `escort_viper` | Strike package escort |

Same four threat tiers as random play. Training teaches the same steps at every tier; only the threat density changes.

Example spec:

```json
{
  "curriculum": "jdam_viper",
  "difficulty": "routine",
  "terrain": "Caucasus",
  "seed": 2001
}
```

---

## Command reference

### `dcsintel detect`

| Flag | Meaning |
|---|---|
| `--refresh` | Ignore cache (`~/.dcsintel/detected.json`) and rescan |

Typical output fields: `dcs_install`, `saved_games`, `modules`, `terrains`, `source`.

Detection order: `DCSINTEL_DCS_PATH` → `dcsintel.config.json` → Windows registry → common install paths. Then scan `Mods/aircraft/` and `Mods/terrains/`. `Su-25T` and `TF-51D` count as owned (base game).

Supported terrain names include Caucasus, Nevada, Normandy, Persian Gulf, Syria, Mariana Islands, Falklands, Sinai, Kola, Germany, The Channel.

### `dcsintel generate`

Requires `--type` or `--spec`.

| Flag | Meaning |
|---|---|
| `--spec FILE` | MissionSpec JSON |
| `--type TYPE` | `dogfight` `cap` `sead` `strike` `escort` `cas` `intercept` |
| `--terrain NAME` | e.g. `Syria` |
| `--aircraft ID` | e.g. `F-16C_50` |
| `--difficulty TIER` | `training` `routine` `contested` `high_threat` |
| `--seed N` | Reproducible RNG |
| `--out PATH` | Output `.miz` |
| `--no-ownership-check` | Skip module/terrain validation |

### `dcsintel training`

| Flag | Meaning |
|---|---|
| `--curriculum ID` | See table above |
| `--difficulty TIER` | Same four tiers |
| `--spec FILE` | TrainingSpec JSON |
| `--terrain` `--seed` `--out` | Same idea as generate |
| `--no-ownership-check` | Skip ownership validation |

### `dcsintel validate MISSION.miz`

Reloads the file with pydcs and reports terrain, player aircraft, unit counts, and load warnings.

---

## MissionSpec (random play)

Only `"type"` is required. Omitted fields are filled from the seed.

```json
{
  "type": "sead",
  "terrain": "Caucasus",
  "era": "modern",
  "difficulty": "routine",
  "twists": ["bandits_airborne"],
  "time_of_day": "dawn",
  "weather": "scattered",
  "player": {
    "aircraft": "F-16C_50",
    "start": "hot",
    "airbase": "Kutaisi"
  },
  "enemy": {
    "skill": "Good",
    "fighters": 2,
    "cap_flights": 1,
    "sam_types": ["SA-10", "SA-6"]
  },
  "support": { "awacs": true, "tanker": true },
  "distance_nm": 80,
  "briefing": {
    "title": "Iron Hand",
    "situation": "...",
    "objective": "..."
  },
  "seed": 42
}
```

| Field | Values | Default when omitted |
|---|---|---|
| `type` | see mission types | required |
| `difficulty` | four tier IDs | `routine` |
| `twists` | list of twist IDs | tier-dependent random |
| `terrain` | owned map name | random owned |
| `era` | `modern`, `coldwar` | tier-weighted |
| `time_of_day` | `dawn` `day` `dusk` `night` `random` | tier-weighted |
| `weather` | `clear` … `rain`, `random` | tier-weighted |
| `player.aircraft` | DCS type id | random owned |
| `player.start` | `cold` `hot` `runway` `air` | `hot` (`air` for dogfight) |
| `player.airbase` | name on terrain | auto-picked |
| `enemy.skill` | `Average` … `Excellent`, `Random` | from tier |
| `enemy.fighters` | 1–8 | tier + type |
| `enemy.cap_flights` | 0–4 | from tier |
| `enemy.sam_types` | SAM keys below | tier + era |
| `support.awacs`, `support.tanker` | booleans | tier + type |
| `distance_nm` | 15–300 | type default |
| `briefing.*` | free text | filled at build if null |
| `seed` | integer | random |

SAM keys: `SA-2` `SA-3` `SA-6` `SA-8` `SA-10` `SA-11` `SA-15` `SA-19` `AAA`. Cold-war era allows `SA-2` `SA-3` `SA-6` `AAA` only.

Validation errors are written for agents — e.g. unowned terrain lists what you do own so the agent can fix the spec without asking you.

---

## Troubleshooting

**Mission feels empty in the Mission Editor**  
Units may be far from the default map view. Recent builds bias airbase pairs toward the map center; if you still see it, try a different seed or lower `distance_nm`.

**Helo mission too long**  
Set `distance_nm` to 20–35 in the spec. Defaults assume fixed-wing transit.

**Agent wrote invalid SAM for the era**  
Use era-appropriate types or omit `enemy.sam_types` and let the tier pick.

**Training vs random**  
Training = `dcsintel training` with a `curriculum`. Random = `dcsintel generate` with a `type`. Legacy `generate --type sead_training` still maps to SEAD training.

---

## Extending the tool

### Repo layout (short)

```
skills/dcs-mission-generator/   Agent skill + doctrine per mission type
src/dcsintel/
  cli.py          Commands
  detect.py       Install scan
  spec.py         MissionSpec normalize
  builder.py      Shared mission plumbing (uses pydcs)
  missions/       One builder per mission type
  training/       F-16 training curricula
  data/           Units, SAM templates, module folder map
```

### New mission type

1. Add `src/dcsintel/missions/<name>.py` with `PLAYER_TASK` and `build(ctx)`.
2. Register in `missions/__init__.py` and `spec.py::MISSION_TYPES`.
3. Add `skills/dcs-mission-generator/mission-types/<name>.md`.
4. `dcsintel generate --type <name> --no-ownership-check` then `validate`.

### New units or modules

Edit JSON under `src/dcsintel/data/`. Strings must match DCS type names (pydcs `plane_map` / `vehicle_map` keys).

---

Back to [README](../README.md) · [Installation](INSTALL.md) · [FAQ](FAQ.md)
