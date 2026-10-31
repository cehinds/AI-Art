# Room assembly review V1

Three asset-only room previews assembled from existing AI-Art PNG components: Tobul’s weapon shop, Scott’s refuge and the visible section of Hilda’s audience room.

No new image generation, game code, scene integration or build is part of this pass. Each room folder includes its source PNG snapshots, source hashes and placement records, a standalone composition script, separate image layers and a composite. Mechanical operations are cropping, nearest-neighbor scaling, tile repetition and alpha compositing.

The original gameplay captures remain in `ReferenceReview`, with attributed sources and exact crop rectangles. They are comparison material, never room-composition inputs. Hilda’s room is only the unobstructed visible portion of the reference. Player/dialogue omissions and reused asset mismatches are documented rather than presented as exact retail reproduction.

Open `index.html` for all three side-by-side comparisons. Each pair uses identical viewport bounds and display scaling. Production/gameplay readiness is not implied by a valid image composition.

Run each room’s `build.cjs` with Node.js. Sharp is required (`npm install sharp` or the available workstation runtime). Scripts use local input snapshots when present so the room pack can be rebuilt independently from its original checkout.
