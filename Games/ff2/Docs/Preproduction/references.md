# Reference ledger

Checked 2026-10-24. The baseline is the 1988 Japanese Famicom Final Fantasy II, not North American SNES FFII/FFIV. These are references, not imported production assets.

| ID | Source | Use and boundary |
|---|---|---|
| ORIGINAL-OVERVIEW | [Nintendo original FFII Virtual Console manual](https://www.nintendo.co.jp/wii/vc/vc_ff2/vc_ff2_01.html) | Identifies the 1988 Famicom release; action-dependent growth and weapon/magic proficiency. Primary baseline. |
| ORIGINAL-SCREENS | [Map/menu/battle overview](https://www.nintendo.co.jp/wii/vc/vc_ff2/vc_ff2_04.html) | Original screen families and navigation; compare structure, not translated labels. |
| ORIGINAL-WORLD | [World and transport](https://www.nintendo.co.jp/wii/vc/vc_ff2/vc_ff2_05.html) | Traversal restrictions and transport reference. |
| ORIGINAL-KEYWORDS | [Town, dungeon, and conversation](https://www.nintendo.co.jp/wii/vc/vc_ff2/vc_ff2_06.html) | Learn/Ask/Item conversation flow. Sample prototype dialogue is newly written. |
| ORIGINAL-MENU | [Original menu and saving](https://www.nintendo.co.jp/wii/vc/vc_ff2/vc_ff2_08.html) | Five menu categories; equipment and item-slot behavior; four world-map save slots. |
| ORIGINAL-BATTLE | [Original battle flow](https://www.nintendo.co.jp/wii/vc/vc_ff2/vc_ff2_09.html) | Choose all party commands before round resolution. Observe enemy-left/party-right composition and result states. |
| GBA-QUALITY | [Nintendo Dawn of Souls page](https://www.nintendo.com/en-gb/Games/Game-Boy-Advance/Final-Fantasy-I-II-Dawn-of-Souls-266694.html) | GBA presentation benchmark only; later-port additions and rules are not adopted automatically. |
| LATER-PORT | [Square Enix FFII Pixel Remaster](https://www.jp.square-enix.com/ff_pixelremaster/ff2/) | Clearly marked later release; identity cross-check, not original-layout authority. |
| UNITY-PIXELS | [Unity pixel-perfect preparation](https://docs.unity.com/en-us/engine/6000.3/manual/unity2d/2d-urp/2d-pixelperfect/prep-sprites) | Point filtering, aligned pixels-per-unit, reference resolution. URP guidance; this initial sandbox has no URP package installed. |

## What is and is not verified

The sources establish game identity and the listed system boundaries. Original screen coordinates, complete map geometry, animation timing, balance formulas, character colors and every story event have not been exhaustively transcribed. Concept board layouts are invented study layouts, not exact Altair or dungeon reconstructions. English text and illustrative statistics in the wireframes are not canonical translations or balance data.

The proposed 256x240 square-pixel canvas is 16:15. A 4:3 display presentation is a separate pixel-aspect decision. No silent stretching is approved. GBA visual quality does not imply adopting the GBA viewport.

## Before production asset approval

For each screen, record the original version, location/event, source capture, crop and scale; compare actor footprint, tile density, UI panel geometry and colors beside the candidate at native size. Measure discrepancies and obtain approval of explicit deviations. Current concept sheets are mood/material/silhouette studies and cannot pass that exact-layout gate by themselves.

