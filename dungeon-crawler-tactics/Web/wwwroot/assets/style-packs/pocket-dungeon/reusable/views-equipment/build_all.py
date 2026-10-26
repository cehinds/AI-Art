"""Rebuild all retained generated six-view atlases offline from this pack's raw/ files."""
from build_batch import process

BATCHES = [
    ('raw/arsenal-dagger-rapier-longsword.png', [('arsenal-dagger','Dagger'),('arsenal-rapier','Rapier'),('arsenal-longsword','Longsword')], 'arsenal'),
    ('raw/arsenal-greatsword-scimitar-katana.png', [('arsenal-greatsword','Greatsword'),('arsenal-scimitar','Scimitar'),('arsenal-katana','Katana')], 'arsenal'),
    ('raw/arsenal-handaxe-battleaxe-hammer.png', [('arsenal-hand-axe','Hand axe'),('arsenal-battle-axe','Battle axe'),('arsenal-war-hammer','War hammer')], 'arsenal'),
    ('raw/arsenal-morningstar-spear-halberd.png', [('arsenal-morning-star','Morning star'),('arsenal-spear','Spear'),('arsenal-halberd','Halberd')], 'arsenal'),
    ('raw/arsenal-trident-quarterstaff-bow.png', [('arsenal-trident','Trident'),('arsenal-quarterstaff','Quarterstaff'),('arsenal-recurve-bow','Recurve bow')], 'arsenal'),
    ('raw/arsenal-heavycrossbow-sling-throwingknives.png', [('arsenal-heavy-crossbow','Heavy crossbow'),('arsenal-sling','Sling'),('arsenal-throwing-knives','Throwing knives')], 'arsenal'),
    ('raw/arsenal-arcane-fire-frost.png', [('arsenal-arcane-staff','Arcane staff'),('arsenal-fire-wand','Fire wand'),('arsenal-frost-wand','Frost wand')], 'arsenal'),
    ('raw/arsenal-lightning-knuckles-dynamite.png', [('arsenal-lightning-rod','Lightning rod'),('arsenal-spiked-knuckles','Spiked knuckles'),('arsenal-dynamite-bundle','Dynamite bundle')], 'arsenal'),
    ('raw/armor-headwear.png', [('armor-cloth-hood','Cloth hood'),('armor-leather-cap','Leather cap'),('armor-chain-coif','Chain coif')], 'armor'),
    ('raw/gear-first-tools.png', [('gear-rope-coil','Rope coil'),('gear-grappling-hook','Grappling hook'),('gear-pickaxe','Pickaxe')], 'gear'),
    ('raw/gear-second-tools.png', [('gear-shovel','Shovel'),('gear-hand-lantern','Hand lantern'),('gear-compass','Compass')], 'gear'),
    ('raw/gear-travel-supplies.png', [('gear-rolled-map','Rolled map'),('gear-bedroll','Bedroll'),('gear-waterskin','Waterskin')], 'gear'),
]
for sequence, label in [('carl-kick','Carl kick'),('donut-cast','Princess Donut cast'),('katia-punch','Katia punch'),('mongo-bite','Mongo bite')]:
    for chunk, frames in [('01-03',(1,2,3)),('04-06',(4,5,6))]:
        BATCHES.append((f'raw/attacks-{sequence}-{chunk}.png', [(f'attacks-{sequence}-0{i}',f'{label} pose {i}') for i in frames], 'attacks'))

if __name__ == '__main__':
    for raw, objects, kind in BATCHES:
        process(raw, objects, kind)
    from apply_targeted_repairs import apply_all
    apply_all()
