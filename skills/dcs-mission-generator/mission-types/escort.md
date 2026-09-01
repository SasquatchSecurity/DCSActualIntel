# Bomber Escort

Shepherd a friendly AI bomber stream to the target and back while enemy
interceptors try to cut the route.

## What the generator builds

- Hammer flight: 2 blue AI bombers (B-1B/B-52H) flying spawn -> target ->
  return at FL260
- Red interceptors (`enemy.fighters`) cutting the route from the flank at
  the midpoint
- Player waypoints shadow the bomber route 4000 ft above it
- AWACS and tanker on by default

## Authoring guidance

- The bombers are AI - the user does NOT need to own them; only the player's
  fighter must be owned
- `enemy.fighters: 2` is a fair fight; 4 forces sorting and target discipline
- Longer `distance_nm` (100-140) means more time in the escort saddle and a
  more realistic profile
- Position matters more than kills here - say so in the briefing: the
  mission fails if the bombers die

## Example specs

```json
{"type": "escort", "player": {"aircraft": "F-15C"},
 "era": "modern", "enemy": {"fighters": 2}}
```

```json
{"type": "escort", "distance_nm": 120,
 "enemy": {"fighters": 4, "skill": "High"},
 "briefing": {"title": "Ride Shotgun",
              "objective": "Hammer must survive to the target. Kills are secondary."}}
```
