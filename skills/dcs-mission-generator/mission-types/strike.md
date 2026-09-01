# Strike

Destroy a defended ground target cluster - a supply concentration of trucks
and flak near the objective.

## What the generator builds

- Target cluster: soft vehicles (fuel/ammo trucks, ZU-23 flak trucks) within
  ~0.5 nm of waypoint 2
- Point defense SAM guarding the target: `SA-15` in modern era, `AAA`
  (Shilkas) in cold war
- Optional red CAP (`enemy.cap_flights`)
- Route: ingress (wp 1) -> target (wp 2) -> egress (wp 3)

## Authoring guidance

- Precision platforms (F-16C, FA-18C, A-10C_2, F-15E) handle `modern` point
  defenses from standoff; dumb-bomb era jets should get `era: "coldwar"` so
  the defense is guns, not `SA-15`
- Add `enemy.cap_flights: 1` to force the player to consider the air picture
  during the attack run
- `time_of_day: "night"` plus a targeting-pod aircraft is a good sensor
  workout

## Example specs

```json
{"type": "strike", "player": {"aircraft": "A-10C_2"}, "era": "coldwar",
 "distance_nm": 50, "weather": "scattered"}
```

```json
{"type": "strike", "player": {"aircraft": "F-16C_50"}, "era": "modern",
 "enemy": {"cap_flights": 1},
 "briefing": {"title": "Cut the Supply Line",
              "situation": "The enemy offensive runs on this fuel depot."}}
```
