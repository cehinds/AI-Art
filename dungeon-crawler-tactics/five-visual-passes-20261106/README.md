# Five additional visual passes — actual WASM evidence

Exactly five sequential presentation stages follow the previous published renderer baseline. The two rejected intermediate captures remain under revisions/ with their original metadata and hashes. Each approved stage records seed 1337 boss and workshop rooms, unchanged camera/viewport, and a fixed renderer animation timestamp of 1000 ms. Camera framing and external DOM visibility are disclosed in each capture report. No gameplay state, geometry, assets or draw calls were injected.

Source reference: clean-map.png from the existing reference-layers asset folder. source-v-final.html/png compares that reference with the actual final browser crop. baseline-v-final.html/png compares the previous published renderer with the final actual crop. index.html and progression.png show all five approved stages and baseline.

stage-validation.json proves all six world.json hashes are identical and all six served renderer hashes distinct. Every approved pass has a served renderer hash matching its source renderer; the baseline uses the previous published renderer while the source tree already contained pass 1, as explicitly disclosed in baseline/capture.json.

Final verification under final-qa/ runs the published game with its normal animation clock, including desktop/mobile actual keyboard/UI battle, blocked walls and water, prop collision, and separate doorway/bridge keyboard traversal for seeds 1337 and 42. The clean environment crops are visual comparisons, not a claim of pixel parity. Actual combat captures retain full UI.

Art references and native assets remain separately hosted in AI-Art. This evidence package contains review screenshots and reports, not SDKs, build output or the game runtime.

Tested runtime commit: `c5b8d44e45e7e8d5a3f9ad10ebdc212cee4990d6`. The committed renderer and hosted asset manifest hashes match the reviewed and tested source. See tested-runtime.json for published fingerprints. Original pre-commit capture revision fields remain unchanged.
