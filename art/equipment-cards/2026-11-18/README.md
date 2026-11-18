# AshenSpire equipment card illustrations

Open [the gallery](gallery.html) to inspect the 49 new illustrations, or [the contact sheet](contact-sheet.jpg) to see them together. The [coverage catalog](coverage.json) maps all 90 names in the November 18 proposal to their artwork, including the 41 existing pieces. Six existing items previously borrowed another item's picture. Their entries include the prior asset ID.

The `asset` field is relative to the `hd/` or `light/` directory of this checkout. Proposed gear uses new art keys. The catalog includes no item definitions or balance values.

## Sources and exports

The PNG files in `masters/` are original outputs from OpenAI's built-in image generation for this proposal. [Prompt records](prompts.json) include the shared wording, per-item subjects, and exact replacement prompts under `finalOverrides`. Kris has its own prompt.

Each HD export crops the visible alpha bounds above 16, fits the entire item inside a 464-pixel square, centers it within 512 × 512 transparent pixels, and encodes WebP at quality 92. Arbalest and Bone Talisman have an extra alpha cleanup before cropping. Arbalest maps alpha 105–240 to 0–255; Bone Talisman maps 115–240 to 0–255, clamping at either end. The light exports use the art repository's mobile-art policy.

Run `python verify.py` from this folder with Pillow installed to check all 90 HD and light paths, the 49 source masters, distinct HD exports, alpha, dimensions and padding. The art repository's `node tools/mobile-art.mjs --check` and `node tools/manifest.mjs --check` verify the official twins and manifest.
