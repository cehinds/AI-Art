# Skyrim FF2 — External Assets

Place this `assets/` folder next to `skyrim-ff2.html`.
All folders are optional — the game falls back to built-in assets if files are missing.

## maps/
JSON or TXT tile maps loaded at startup, replacing built-in maps if valid.

| File | Contents |
|---|---|
| `manifest.json` | List of map IDs to load |
| `town.json` | Whiterun city map (22×32 tiles) |
| `dun.json` | Bleak Falls Barrow (24×34 tiles) |

**JSON format:**
```json
{
  "id": "town",
  "name": "Whiterun",
  "tiles": ["#,,,,h...", "..."],
  "spawn": [11, 12]
}
```
**TXT format:** one row per line, `#` lines are comments.

Maps are validated before use. Missing required tiles (B,F,W,A,I,C,U,G for town;
X,c,K,V,O,T for dun) cause the built-in to be kept and a console warning to appear.

## sprites/
PNG or SVG image overrides for canvas-baked sprites. Filename = sprite key + extension.

| Key | Character |
|---|---|
| `dovahkiin` | Player character (Dragonborn) |
| `lydia`, `aela`, `farkas`, `jzargo`, `erandur` | Companions |
| `balgruuf`, `farengar`, `adrianne`, `arcadia`, `hulda`, `guard` | Town NPCs |
| `bandit`, `draugr`, `overlord`, `skeever`, `wolf`, `icewraith`, `atronach` | Enemies |
| `mirmulnir` | Boss dragon (32×20 px) |

SVG placeholders (editable pixel art) are included for all 39 sprites.
Replace with PNGs at the same pixel dimensions (see `manifest.json` for sizes).

## bg/
Battle background images. Name matches CSS class (e.g. `bg-cave.jpg`).
Recommended size: 248×124px.

| File | Used for |
|---|---|
| `bg-cave` | Random outdoor/cave encounters |
| `bg-crypt` | Dungeon encounters |
| `bg-icecave` | Mirmulnir dragon fight |
| `bg-ruins` | Draugr Overlord boss |

Or set **Settings → Battle background** to any filename in this folder (e.g. `night-sky.jpg`).

## music/
MP3/OGG background music tracks. Enable in **Settings → Audio**.

| File | Plays during |
|---|---|
| `field.mp3` | Exploring Whiterun |
| `battle.mp3` | Random encounters |
| `boss.mp3` | Boss fights |
| `victory.mp3` | Battle victory |
| `inn.mp3` | Bannered Mare inn |

Missing files = silence, no errors.

## config.json
Optional top-level config loaded at startup. Overrides built-in defaults but is
itself overridden by your in-game saved settings (localStorage). Delete any key
to fall back to its default; delete the file entirely for all defaults.

```json
{
  "settings": { "startGold": 500, "enableAutoBattle": false, "growthMult": 2.0 },
  "keybinds": { "confirm": ["Enter", " "], "cancel": ["Escape"] }
}
```

**Sections:**
- `settings` — any value from the in-game Settings screen (speeds, multipliers, feature toggles, HP-bar visibility, music, `startGold`, `partySizeCap`, etc.)
- `features` — alias merged into `settings` (use either)
- `keybinds` — per-action key lists (see Controls below)

Keys beginning with `_` (e.g. `_comment`) are ignored, so you can annotate the file freely.

## Controls (keyboard + gamepad)
The game is fully playable without a mouse.

| Action | Default keys | Gamepad |
|---|---|---|
| Move | WASD / Arrow keys | D-pad / left stick |
| Confirm / Interact | Enter / Space / E | A |
| Cancel / Back | Esc / Backspace / Q | B |
| Open Menu | Tab / M | Start |
| Toggle Auto-battle | X | X |
| Defend / Wait | F | — |

Rebind any action live in **Settings → Controls**. Click **Rebind**, press a key,
press Esc to cancel. Bindings save to localStorage and can also be set as defaults
in `config.json` under `keybinds`.
