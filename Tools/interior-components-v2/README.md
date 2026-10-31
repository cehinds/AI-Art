# Interior Components V2

Assets only. 166 native components; no game code, Unity scene, build, integration, collision, door traversal, or release change.

Inventory: four32px floor families; three32x64 cream/timber north-facing wall/open-door/closed-door faces; sixteen32px top-down straight, convex, concave and threshold cutcaps; three complete47-mask transparent carpet families (red/gold, navy/cream, lilac/cream);32x64 north stair flight and32px down well. Floor, rug, cap, tall face, stairs and furniture are separate layers. Tall front faces are used only at north boundaries, bottom anchored above the floor. They are not rotated onto side/south boundaries.

All five generated masters and exact generation prompts are preserved under ArtSource/InteriorComponentsV2. Source hashes, crop/fit registration, excluded wrong-terminal cap cells, deterministic asset IDs/GUIDs and native output hashes are in the production manifest. Caps use12px native bands; their concave joints come from authored convex-joint source subcrops because generated row3 stair shapes have incorrect terminals. Carpet inner-joint crops exclude unrelated outer borders. Red floor uses a quieter256px square source crop at960,240; the rest of each material source is unchanged. These are crop, nearest resize, reflection, source-fragment assembly and alpha normalization operations, not code-painted artwork.

Floors and tall faces are opaque. Cutcaps, carpets and stairs use binary alpha at128 threshold, with invisible RGB cleared. Full carpet interior mask255 is naturally opaque. Original generated source alpha remains preserved. Import metadata declares point filtering, no mipmaps and32PPU; this has not been validated in Unity Editor.

The three decorated proofs use unchanged V1 furniture; the manifest records every dependency hash. Counter/furniture joins have not been fixed or re-authored. HQ uses warm flagstone/red carpet; refuge uses warm flagstone/blue rug; shop uses red floor/lilac carpet in an L-shaped room. Wood and lilac stone are demonstrated separately in repeat proofs. The gallery also shows every inward cutcap joint, floor planes, doorway threshold, stair placement, rug shape and palette-specific contacts.

Independent verification reads emitted PNGs. It checks eight floor repeats, nine tall-face pairs,116 cutcap geometric pairs and1176 carpet pairs derived from all4096 local world occupancy patches across three palettes. It checks945 actual proof joins, full RGBA four pixels inward from each edge, family completeness, source/config/dependency hashes, opaque/binary alpha, zero invisible RGB, point/PPU metadata and rejection of an in-memory mutation at depth4. Different-material face-to-floor boundaries are intentional visual transitions, not equal-pixel repeat edges. These checks do not prove retail-art parity, collision, door traversal or runtime behavior.

Reference differences remain: carpet ornament is thinner/simpler, wall panels repeat visibly, and cutcaps retain a bold outline. Mechanical PASS is separate from visual review. No1:1 FFII Pixel Remaster fidelity claim is made.

From the art repository root:

```powershell
node Tools/interior-components-v2/export.cjs
node Tools/interior-components-v2/verify.cjs
```

Requires Node.js and Sharp (`npm install` in the tools directory on a new machine). All output/source paths are relative to the art repository root. In the staged checkout only, the unchanged V1 furniture can be read from `ART_DEPENDENCY_ROOT`; this workstation falls back to C:/repos/AI-Art-FF2. After copying into the art repository the relative dependency paths resolve directly. Review/interior-components-v2/index.html links the production manifest, verifier result and reference comparison.
