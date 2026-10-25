// ============================================================================
// data/sprite-parts.js — 32×32 chibi sprite part layers (procedural source art)
// ----------------------------------------------------------------------------
// Pure data. Each PART is a set of directional LAYERS. A layer is a 32-row grid
// of 32 chars. Each non-space, non-"." char is a TOKEN resolved through the
// layer's `bind` map via PaletteService:
//
//   bind: { "k": ["group","name"] }      e.g. { "s":["skin","fair"] }
//   then a cell char is "<bindKey><stop>" is NOT used here for compactness;
//   instead each cell is a single char whose default stop is encoded by case/
//   symbol in SHADE below. This keeps the grids readable.
//
// CELL ALPHABET (single char per pixel):
//   "." or " "  transparent
//   skin:   a=outline b=shadow c=base d=light e=highlight   (bind key "skin")
//   hair:   f=outline g=shadow h=base i=light j=highlight   (bind key "hair")
//   eye:    p=rim q=iris                                    (bind key "eyes")
//   armor:  A=outline R=shadow M=base L=light G=highlight   (bind key "armor")
//   mouth:  m  (uses skin outline)
//
// Proportions: CHIBI 2-head-tall in 32px. Head occupies rows ~3–15, body rows
// ~15–29. Big head, short body — classic FF2 PR overworld read.
//
// Phase B ships ONE character (dovahkiin) with body+hair+eyes for down/up/left.
// right is produced by mirroring left at generation time. Walk frames are
// produced by the generator shifting the leg rows, so only 1 base pose per
// direction is authored here.
//
// Loaded before sprite-gen-service. Shares global scope (no import/export).
// ============================================================================

var SPRITE_PARTS = {

  // Skin/body base (the under-layer for every character). Generic chibi torso,
  // arms, legs, and head shape. Armor and hair paint over this.
  body: {
    bind: { skin: null }, // skin name supplied per-character at gen time
    down: [
      "................................",
      "................................",
      "................................",
      "..........aaaaaaaa..............",
      ".........abbbbbbbba.............",
      ".........abcccccccba............",
      ".........abcdddddcba............",
      ".........abcdddddcba............",
      ".........abcdddddcba............",
      ".........abcddeddcba............",
      ".........abcdddddcba............",
      "..........abcdddcba............",
      "...........abcccba.............",
      "............aaaaa..............",
      "...........abcccba.............",
      "..........abccccccba...........",
      ".........abcccccccba...........",
      ".........abcdddddcba...........",
      ".........abcdddddcba...........",
      ".........abcdddddcba...........",
      ".........abcdddddcba...........",
      "..........abcdddcba............",
      "...........abcccba.............",
      "...........ab...ba.............",
      "...........ab...ba.............",
      "...........ab...ba.............",
      "..........abc...cba............",
      "..........abb...bba............",
      "..........aaa...aaa............",
      "................................",
      "................................",
      "................................"
    ],
    up: [
      "................................",
      "................................",
      "................................",
      "..........aaaaaaaa..............",
      ".........abbbbbbbba.............",
      ".........abhhhhhhhba............",
      ".........abhhhhhhhba............",
      ".........abhhhhhhhba............",
      ".........abhhhhhhhba............",
      ".........abhhhhhhhba............",
      ".........abhhhhhhhba............",
      "..........abhhhhba.............",
      "...........abhhhba.............",
      "............aaaaa..............",
      "...........abcccba.............",
      "..........abccccccba...........",
      ".........abcccccccba...........",
      ".........abcdddddcba...........",
      ".........abcdddddcba...........",
      ".........abcdddddcba...........",
      ".........abcdddddcba...........",
      "..........abcdddcba............",
      "...........abcccba.............",
      "...........ab...ba.............",
      "...........ab...ba.............",
      "...........ab...ba.............",
      "..........abc...cba............",
      "..........abb...bba............",
      "..........aaa...aaa............",
      "................................",
      "................................",
      "................................"
    ],
    left: [
      "................................",
      "................................",
      "................................",
      "...........aaaaaa..............",
      "..........abbbbbba.............",
      "..........abccccba.............",
      "..........abcdddba.............",
      "..........abcdddba.............",
      "..........abcddeba.............",
      "..........abcdddba.............",
      "..........abcdddba.............",
      "...........abcdba.............",
      "...........abccba.............",
      "............aaaa..............",
      "...........abccba.............",
      "..........abccccba............",
      "..........abccccba............",
      "..........abcdddba............",
      "..........abcdddba............",
      "..........abcdddba............",
      "..........abcdddba............",
      "...........abcdba.............",
      "...........abccba.............",
      "...........ab.ba..............",
      "...........ab.ba..............",
      "...........ab.ba..............",
      "..........abc.cba.............",
      "..........abb.bba.............",
      "..........aaa.aaa.............",
      "................................",
      "................................",
      "................................"
    ]
  },

  // Hair — "long_warrior". Frames the face down/left, covers the scalp up.
  hair: {
    bind: { hair: null }, // hair name supplied per-character
    down: [
      "................................",
      "................................",
      "................................",
      "..........ffffffff..............",
      ".........fgggggggggf............",
      ".........fghhhhhhhgf............",
      ".........fhhiiiiihhf............",
      ".........fhi.....ihf............",
      ".........fh.......hf............",
      ".........f.........f............",
      ".........f.........f............",
      ".........fh.......hf............",
      ".........fgh.....hgf...........",
      ".........fggh...hggf...........",
      ".........ffgh...hgff...........",
      "..........ffh...hff............",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................"
    ],
    up: [
      "................................",
      "................................",
      "................................",
      "..........ffffffff..............",
      ".........fgggggggggf............",
      ".........fghhhhhhhgf............",
      ".........fhiiiiiiiihf...........",
      ".........fhiijjjiiihf...........",
      ".........fhiijjjiiihf...........",
      ".........fhiiiiiiiihf...........",
      ".........fhhiiiiihhf............",
      ".........fghhhhhhhgf............",
      ".........fgghhhhhggf...........",
      ".........ffgggggggff...........",
      "..........fffffffff............",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................"
    ],
    left: [
      "................................",
      "................................",
      "................................",
      "...........ffffff..............",
      "..........fggggggf.............",
      "..........fghhhhgf.............",
      "..........fhiiiihf.............",
      "..........fhi..ihf.............",
      "..........fh....hf.............",
      "..........f.....hf.............",
      "..........f.....hf.............",
      "..........fh...hgf.............",
      "..........fgh.hggf.............",
      "..........fggh.gff.............",
      "...........ffh.ff..............",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................"
    ]
  },

  // Eyes — only meaningful facing down and left. Empty up (back of head).
  eyes: {
    bind: { eyes: null },
    down: [
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "............p...p...............",
      "............q...q...............",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................"
    ],
    up: null,
    left: [
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "............p..................",
      "............q..................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................",
      "................................"
    ]
  }
};

// Per-character trait sheet (Phase B: dovahkiin only). Future characters and
// the character creator just add entries / edit these traits.
// 64b procedural pipeline reads: skin/hair/eyes trait names + an `equip` block
// { armor, weapon, weaponMat, shield, helm }. armor/weaponMat name materials
// from PALETTES.materials; weapon names a key in WPN (its cat picks the shape).
// The character creator / JSON loader (SpriteGenService.loadJSON) just adds or
// edits entries of this same shape.
var SPRITE_CHARS = {
  dovahkiin: { skin:"fair", hair:"dark_brown", eyes:"ice_blue",
    equip:{ armor:"steel", weapon:"ironSword", weaponMat:"iron", shield:false, helm:false } },
  lydia: { skin:"tan", hair:"black", eyes:"brown",
    equip:{ armor:"iron", weapon:"ironSword", weaponMat:"iron", shield:true, helm:true } },
  aela: { skin:"fair", hair:"red", eyes:"green",
    equip:{ armor:"hide", weapon:"huntingBow", weaponMat:"wood", shield:false, helm:false } },
  farkas: { skin:"tan", hair:"black", eyes:"grey",
    equip:{ armor:"steel", weapon:"nordGreataxe", weaponMat:"steel", shield:false, helm:false } },
  jzargo: { skin:"dark", hair:"white", eyes:"amber",
    equip:{ armor:"cloth", weapon:"steelDagger", weaponMat:"steel", shield:false, helm:false } },
  erandur: { skin:"pale", hair:"silver", eyes:"grey",
    equip:{ armor:"cloth", weapon:"steelDagger", weaponMat:"steel", shield:false, helm:false } }
};

// Procedural ENEMY models (64b), keyed by the `sprite` field on ENEMIES entries.
// model:"humanoid" reuses the character model (skin/hair/eyes/equip; hair:null =
// bald/undead). model:"beast" is a quadruped (fur material + glowing accent eye,
// big=boss scale). Enemies face RIGHT toward the party. Extend/override at
// runtime via SpriteGenService.loadEnemyJSON (assets/models.json, Phase 2).
var SPRITE_ENEMIES = {
  skeever: { model:"beast", fur:"hide",   accent:"fire"  },
  wolf:    { model:"beast", fur:"steel",  accent:"frost", },
  draugr:  { model:"humanoid", skin:"elf", hair:null, eyes:"ice_blue",
    equip:{ armor:"bronze", weapon:"ironSword", weaponMat:"iron", helm:true } },
  bandit:  { model:"humanoid", skin:"tan", hair:"black", eyes:"brown",
    equip:{ armor:"leather", weapon:"ironSword", weaponMat:"iron", helm:false } },
  overlord:{ model:"humanoid", skin:"elf", hair:null, eyes:"amber",
    equip:{ armor:"gold", weapon:"orcishAxe", weaponMat:"steel", helm:true } }
};
