# Intercept / QRA Scramble

Raiders are already inbound to the player's airbase when the mission starts.
Get airborne, build the picture, kill the raid before it hits the field.

## What the generator builds

- Red raid: 2 strikers or bombers (40% chance of Tu-22M3/Tu-95 heavies)
  spawned just under halfway in, headed for the player's field
- Escorts join if `enemy.fighters` > 2 (fighters minus 2 = escort size)
- Player starts ON THE GROUND - `player.start: "air"` is rejected for this
  type. `hot` is a fair scramble; `cold` is hard mode (full startup under
  time pressure)
- AWACS on by default to call the picture

## Authoring guidance

- Time pressure is the whole mission: `distance_nm` 50-70 with a hot start is
  tight but winnable; 80-90 or a cold start needs a fast climber
- `enemy.fighters: 2` means an unescorted raid (target practice);
  `4` adds a 2-ship escort you must fight through or avoid
- Interceptor-flavored airframes shine: F-15C, F-14, MiG-21Bis, M-2000C, F-4E

## Example specs

```json
{"type": "intercept", "player": {"aircraft": "F-15C", "start": "hot"},
 "era": "modern", "distance_nm": 60}
```

Cold-war GCI scramble, escorted raid:

```json
{"type": "intercept", "player": {"aircraft": "MiG-21Bis", "start": "cold"},
 "era": "coldwar", "distance_nm": 80, "enemy": {"fighters": 4},
 "briefing": {"title": "Klaxon Klaxon Klaxon"}}
```
