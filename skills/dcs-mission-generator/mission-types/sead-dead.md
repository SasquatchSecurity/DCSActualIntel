# SEAD / DEAD

Roll back an enemy air defense network. Spec `type` is `sead` (covers both
suppression and destruction taskings - phrase the difference in the briefing).

## What the generator builds

- One full SAM site per entry in `enemy.sam_types`, scattered within ~8 nm of
  the objective (waypoint 2), each with proper search/track radars and a
  launcher ring
- An EWR radar deeper in enemy territory
- Optional red CAP (`enemy.cap_flights`)
- Player route: ingress (wp 1) -> target area (wp 2) -> egress (wp 3)

## SAM catalog by era

| Era | Available `sam_types` |
|---|---|
| `modern` | `SA-6` `SA-8` `SA-10` `SA-11` `SA-15` `SA-19` `AAA` |
| `coldwar` | `SA-2` `SA-3` `SA-6` `AAA` |

Threat mix guidance: one long-range site (`SA-10` modern / `SA-2` coldwar)
plus one or two mobile/short-range systems makes a layered, realistic IADS.
`SA-15` actively shoots down HARMs - include it only for experienced players.

## Authoring guidance

- Default (omit `sam_types`) picks 2-3 era-appropriate systems randomly
- HARM shooters (F-16C, FA-18C) pair well with `SA-10`/`SA-11` at
  `distance_nm` 80+; gun/rocket DEAD (A-10, Su-25T) wants `SA-6`/`SA-8`/`AAA`
  at 40-60 nm
- Night SEAD is brutal; keep `time_of_day` daylight unless asked

## Example specs

```json
{"type": "sead", "player": {"aircraft": "F-16C_50"}, "era": "modern",
 "enemy": {"sam_types": ["SA-10", "SA-11"], "cap_flights": 1},
 "briefing": {"title": "Iron Hand"}}
```

```json
{"type": "sead", "player": {"aircraft": "Su-25T"}, "era": "coldwar",
 "distance_nm": 45, "enemy": {"sam_types": ["SA-3", "SA-6", "AAA"]}}
```
