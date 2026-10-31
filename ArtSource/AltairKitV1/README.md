# Altair Kit V1 sources

Keep each generated transparent full-building PNG under `sources/` and its paired binary roof mask under `masks/`. Preserve original generated image bytes and prompt/tool records. The mask is a segmentation file: white selects existing roof pixels and black retains existing facade pixels. Do not paint or fill occluded parts.

Exact source and mask paths are declared in `Tools/altair-kit-v1/kit.json`. The exporter derives `facade` and `roof`, trims only transparent margins, then resizes to the object tile footprint with nearest-neighbor sampling. Optional authored layers must use the complete source canvas and receive the same normalization.

Record generation tool, prompt, date, output ID, and source SHA-256 in a neighboring `.txt` or `.json` record. References inform composition and palette only; do not store screenshot crops as production art or treat Square Enix material as licensed content.
