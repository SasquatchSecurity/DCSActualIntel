# CAP (Combat Air Patrol)

Hold a station and stop an inbound red strike package before it reaches the
friendly airbase.

## What the generator builds

- Player CAP station at the midpoint with a 20 nm racetrack leg (waypoints 1-2)
- Red package: 2 strikers heading for the blue airbase plus an escort flight
  of `enemy.fighters` aircraft
- Optional extra red CAP loitering deep (`enemy.cap_flights`)
- AWACS and tanker on by default

## Authoring guidance

- `distance_nm` 60-100 gives time to establish the station before the picture
  builds; shorter is more frantic
- `enemy.fighters` is the escort size - the real fight. 2 is honest, 4 is busy
- Cold-war era makes this a MiG-21/23 fight with Su-17/MiG-27 strikers -
  great for F-14A/F-4/Mirage F1 owners

## Example specs

```json
{"type": "cap", "player": {"aircraft": "F-14B"},
 "era": "coldwar", "enemy": {"fighters": 2}, "time_of_day": "dawn"}
```

```json
{"type": "cap", "distance_nm": 70,
 "enemy": {"fighters": 4, "cap_flights": 1, "skill": "High"},
 "briefing": {"title": "Hold the Line"}}
```
