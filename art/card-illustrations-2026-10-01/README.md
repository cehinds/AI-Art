# Deck editor card illustration starter set

Seven standalone paintings made with OpenAI's built-in image generation for the deck editor redesign. The previous deck editor mockups were used as style references only; no card pictures were cropped out of UI screenshots. The PNG sources are uncropped 1536 × 1024 paintings. `export.py` makes uncropped 1024 × 683 and 512 × 341 WebP derivatives in `assets/cards/` and writes `manifest.json` with dimensions and checksums.

| Existing card identity | Artwork |
| --- | --- |
| Equipment profile `bladeAttack` / Slashing Strike | `slashing-strike` |
| Equipment profile `shieldGuard` / Shield Defend | `shield-defend` |
| Authored card ID `gorefireSlash` / Gorefire Slash | `gorefire-slash` |
| Equipment profile `weaponTechnique` / Weapon Technique | `weapon-technique` |
| Authored card ID `bloodletting` / Bloodletting | `bloodletting` |
| Authored card ID `ironResolve` / Iron Resolve | `iron-resolve` |
| Authored card ID `lastStand` / Last Stand | `last-stand` |

The 3:2 masters allow a readable full illustration in a modal and a compact center crop on a card face or folded list. Preserve the full painting in the inspector. When placing in the current `.card .art` well (roughly 2.3:1 at 220px card width), use `object-fit: cover` and adjust `object-position` by card if needed. Card rules, values, names, and tags must continue to come from the game model; these files are only art.

Generated with the built-in `image_gen` tool on 2026-10-01. No third-party artwork was downloaded and no third-party asset license is claimed. Exact prompts: `prompts.json`.
