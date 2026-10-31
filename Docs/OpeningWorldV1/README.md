# Opening World V1

Four generated component candidates: low-noise grass (32×32), conifer (32×48), Altair walled settlement (160×128), and Fynn castle-city (160×192). These are asset-only review outputs. Game integration is deferred.

The [contact sheet](../../Review/opening-world-v1/contact-sheet.png) and [gallery](../../Review/opening-world-v1/index.html) show native exports. [Generation prompts](../../ArtSource/OpeningWorldV1/generation-prompts.json) and unchanged masters are retained. The [manifest](../../Assets/Art/Production/OpeningWorldV1/manifest.json) records reference URLs, generated-source hashes, exact crops, output hashes, semantic roles, anchors and dimensions.

Opaque silhouettes use alpha ≥128 for bounds. City images keep their proportions and align to the bottom-center gate; conifer geometry is normalized to its declared canvas. Every resize uses nearest-neighbor sampling. Collision and portal behavior are not supplied by these images.

From the art repository, run `node Tools/opening-world-v1/verify.cjs` for read-only source/output hashes, dimensions, alpha and exact export reproduction. `node Tools/opening-world-v1/export.cjs` rebuilds this pack's derived files.

These are generated recreations informed by attributed FFII Pixel Remaster captures, not extracted retail sprites or a claim of exact retail parity. See the [component comparison](../../Review/world-layer-comparison-v1/index.html) and [combined review catalog](../../Review/component-art-v1/index.html).
