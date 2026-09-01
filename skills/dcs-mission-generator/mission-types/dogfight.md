# Dogfight / BFM

Head-on setup against enemy fighters. The player usually air-starts pointed
at the threat; the merge happens within a few minutes.

## What the generator builds

- Red fighter group (1-2 by default, up to 8) spawned at the objective point,
  flying toward the player's spawn area at 12-24k ft
- Player air-start about 60% of the way between the bases (or ground start
  if `player.start` is changed)

## Authoring guidance

- `distance_nm` 30-50 gives a BVR-ish start that closes fast; use 15-25 for
  a near-instant merge (guns practice)
- `enemy.fighters: 1` with `skill: Average` for learning; `2` at `High` for
  a real fight
- Era matters: `coldwar` red fighters are MiG-21/MiG-23/MiG-19; `modern`
  brings Su-27/MiG-29S/MiG-31/J-11A/Su-30
- AWACS defaults off for this type - it's a knife fight, not a picture
  exercise; enable `support.awacs` if the user wants GCI calls

## Example specs

Guns-only feel, quick merge:

```json
{"type": "dogfight", "distance_nm": 20, "era": "coldwar",
 "enemy": {"fighters": 1, "skill": "Average"}, "time_of_day": "day"}
```

Two-ship of Flankers, serious fight:

```json
{"type": "dogfight", "era": "modern",
 "enemy": {"fighters": 2, "skill": "High"},
 "briefing": {"title": "Two v One over the Ridge"}}
```
