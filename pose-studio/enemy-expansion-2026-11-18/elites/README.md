# Elite enemy art

[Browse the 15 designs and their poses](index.html) or [open the seat overview](designs-preview.jpg). The five elite designs assigned to each seat follow that location when a run rotates the seat order.

Each enemy has an original transparent design, its reference-guided pose atlas, the generation prompts, a labeled contact sheet and an art record. Sources were made for this proposal using OpenAI's built-in image generation. The 4 × 4 pose atlas supplies the six stance holds, the attack, react and defend pairs and the downed frame. The original design supplies idle, scaled to match the atlas idle. Two extra study poses remain on the master.

The [category manifest](manifest.json) uses runtime asset paths relative to the HD and light pack roots. HD frames share a 512 × 512 canvas and one per-enemy scale, with ground at y=480. The light tier is 256 × 256. Run `python verify.py` with Pillow to verify both tiers and their source records.
