# CAS (Close Air Support)

Friendly troops in contact: kill an enemy armor column pressing a smaller
blue element at the front line.

## What the generator builds

- Red column at the objective: tanks, IFVs, APCs plus embedded mobile SHORAD
  (Shilka/SA-8 family - it bites)
- Blue ground element 3 nm on the friendly side - check-fire discipline
  required
- Optional red CAP (`enemy.cap_flights`)
- Player waypoints: holding point (wp 1, ~12 nm back) then the front line (wp 2)

## Authoring guidance

- Natural fit for A-10C/A-10C_2, Su-25T, AV-8B, and attack helicopters
  (AH-64D, Ka-50, Mi-24P)
- **Helicopters: set `distance_nm` 20-35** - the default 40-80 is a fixed-wing
  transit
- Emphasize the friendlies in the briefing; strafing blue armor is the classic
  CAS failure
- `weather: "clear"` or `"scattered"` keeps the target area workable; overcast
  CAS with dumb weapons is misery

## Example specs

```json
{"type": "cas", "player": {"aircraft": "A-10C_2"},
 "era": "modern", "distance_nm": 50, "weather": "clear"}
```

Helicopter example (note the short distance):

```json
{"type": "cas", "player": {"aircraft": "AH-64D_BLK_II", "start": "hot"},
 "distance_nm": 25, "time_of_day": "dawn",
 "briefing": {"title": "Danger Close at the River"}}
```
