# Selected counter and sweep animations

These are the eight selections from `favorites.json`: five-choice review completed by the owner, followed by separate slash, arcane staff, gold palm and paired dagger effects. `index.html` retains the labeled Play/Pause/Step/Reset preview; `projects/` contains four portable Sprite Workshop projects with editable effect layers. Serve this directory with any local static HTTP server.

Original transparent PNGs are retained in `clips/`. Generated variant sheets and exact prompts are retained in `source/`; option 01 reuses the existing first-party class card paintings. `effects/` retains authored SVG sources and their transparent PNG exports. No third-party artwork or license is introduced.

The runtime uses three selected body phases, then the game's original `ready` image. It retains 260 ms total timing (55/60/65/80 ms), proportionally registers body and effect layers together around the [256,464] floor anchor, and exports 256 px WebPs. Contact and recovery effects are separate assets; stance and idle have no effect. Other character actions and original stance images are untouched.

Reproduce the high exports and generated game catalog from an AshenSpire checkout containing the original card catalog:

    python tools/player-counter-sweep.py art/player-counter-sweep-2026-10-09 . <AshenSpire-checkout>
    node tools/mobile-art.mjs
    node tools/manifest.mjs --write

The first argument can also be the original full authoring package. Light exports follow this repository's normal policy. The game integration pins the released asset pack; this source preview itself does not establish a shipped game build.
