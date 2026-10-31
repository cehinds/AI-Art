# ShopInteriorsV1 tool

Python3.13 with Pillow12.3.0. The working local interpreter is:

`C:\Users\const\AppData\Local\Programs\Python\Python313\python.exe`

From the staging root or the published art-repository root:

```powershell
& 'C:\Users\const\AppData\Local\Programs\Python\Python313\python.exe' Tools/shop-interiors-v1/build.py verify
```

Read-only verification does not rebuild assets. To reproduce the owned exports/proofs deliberately:

```powershell
& 'C:\Users\const\AppData\Local\Programs\Python\Python313\python.exe' Tools/shop-interiors-v1/build.py build
```

Other workstations can install the pinned dependency using `python -m pip install -r Tools/shop-interiors-v1/requirements.txt`.

`kit.json` supplies the approved unchanged reuse inventory, selected generated source registrations and sibling terrain dependency. The tool derives its root from this file location, so an absolute script path works from any working directory. Full sources, density, layers, collision-proposal limitations and provenance are documented in [Docs/ShopInteriorsV1](../../Docs/ShopInteriorsV1/README.md).

Only this isolated kit's individual assets and room candidates are written; no game code or scenes. Existing differing individual component bytes cause failure. Owned room-proof revisions are preserved as iterations before refresh. Verification checks ten generation registrations, source/provenance/output hashes, fifty production PNGs, binary cutouts, layer reconstruction and clear proposed entrance/service lanes. Static NPCs only; no runtime/animation claim.
