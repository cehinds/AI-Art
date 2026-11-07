# Combat followthrough QA evidence

Open `index.html` for comparison captures and `qa-summary.json` for status and scope. Final browser outputs live under `after/`; `baseline/` comes from the retained pre-change publication. `rejected-overlay-iteration/` preserves a rejected layout which covered the lower board. `pre-support-fix-passing/` preserves a passing browser iteration before the generic ally/self support-skill engine correction.

All final game interactions use actual keyboard/pointer controls against the published .NET8 WebAssembly host. Public `rpgView` is read to route and assert; no game commands, saves, state fixtures or camera overrides are injected. The preparation harness adds event observers for input timing/blur without altering gameplay state. Its route uses 1440×1000 for some sections and 390×844 responsive menus; new targeted screenshots/assertions explicitly use 1280×720 and 390×844.

`source-before-publish.json` hashes all Core source, Web C# source, presentation files and authored skill data. `published-sha256.json` hashes the final host/data/framework files (assets separately checked by the checksum manifest). `core-suite.log` records all 16 passing core groups, including Strike multiplier, ground/direct Bomb targeting, per-target defenses, chains, friendly-fire and generic support-skill parity. Browser targeted checks cover natural first-encounter Bomb and movement; broader core formulas and chain coverage are deterministic regressions rather than fabricated browser setups. No Unity validation or pixel-perfect art claim.

Reproduce with the published host at 127.0.0.1:8765:

```sh
python3 Tools/playtest_combat_followthrough.py --url http://127.0.0.1:8765
python3 Tools/playtest_block_b.py --smoke --url http://127.0.0.1:8765 --output Rebuild/CombatFollowthroughComparison/after/smoke
python3 Tools/playtest_block_b.py --url http://127.0.0.1:8765 --output Rebuild/CombatFollowthroughComparison/after/preparation
python3 Tools/playtest_block_b.py --full-route --url http://127.0.0.1:8765 --output Rebuild/CombatFollowthroughComparison/after/full-route
```
