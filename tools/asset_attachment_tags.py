#!/usr/bin/env python3
"""Add editorial attachment tags to art metadata without modifying PNGs.

Builders call enrich_library(pack, index) before writing sidecars. After all
libraries are built, run --apply to refresh central compatibility groups and
all JSON documents under assets; --check verifies the same deterministic output.
These suggestions never change collision, walkability, anchors or footprints.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSETS = ROOT / 'dungeon-crawler-tactics/Web/wwwroot/assets'
RULES_NAME = 'attachment-rules.json'
AUTHORITY = 'editorial-semantic-inference'
SURFACES = ['floor', 'wall', 'ceiling', 'water', 'lava', 'doorway', 'stairs', 'tabletop', 'screen']
MATERIALS = ['stone', 'wood', 'metal', 'iron', 'steel', 'gold', 'crystal', 'glass', 'ice', 'snow', 'sand', 'mud', 'brick', 'cloth', 'leather', 'water', 'lava', 'bone', 'moss', 'grass']
ENVIRONMENTS = ['dungeon', 'sewer', 'cavern', 'forest', 'desert', 'castle', 'crypt', 'temple', 'industrial', 'underwater', 'volcanic', 'frozen', 'garden', 'city', 'safe-room']


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def tokens(asset):
    values = [asset.get('id', ''), asset.get('name', ''), asset.get('label', ''), asset.get('role', ''), asset.get('category', ''), asset.get('kind', '')]
    # Generated editorial tags must not feed back into semantic classification.
    previous = set(asset.get('attachment_generated_tags', []))
    values += [v for v in asset.get('tags', []) if isinstance(v, str) and v not in previous]
    result = set(re.findall(r'[a-z0-9]+', ' '.join(values).lower()))
    for word, material in {'wooden':'wood', 'stonework':'stone', 'metallic':'metal', 'icy':'ice', 'snowy':'snow', 'sandy':'sand', 'muddy':'mud', 'golden':'gold'}.items():
        if word in result:result.add(material)
    return result


def style_of(pack):
    name = Path(pack).name
    return name if name in ('pocket-dungeon', 'dungeon-after-dark', 'ink-and-lanterns') else 'gameplay'


def group_id(style, requires):
    digest = hashlib.sha256(json.dumps(requires, sort_keys=True).encode()).hexdigest()[:12]
    return f'{style}--attachment-{digest}'


def supporting_furniture(asset):
    """An object noun supplies support; a prop's location/modifier does not."""
    furniture = {'table', 'desk', 'workbench', 'counter', 'altar'}
    role = asset.get('procedural', {}).get('role', asset.get('role', asset.get('category')))
    if role in furniture:
        return True
    subject = str(asset.get('name') or asset.get('label') or asset.get('id', '')).lower()
    subject = re.sub(r'[-_]+', ' ', subject)
    subject = re.sub(r'\s+(?:front|top|right|left|bottom|rear)$', '', subject)
    head = re.split(r'\b(?:on|with|beside|at|in|under)\b', subject, maxsplit=1)[0]
    # Grouped furniture retains its support surface ("desk and chairs"),
    # while each coordinated noun still excludes modifiers ("desk candle").
    for subject in re.split(r'\band\b|&', head):
        words = re.findall(r'[a-z0-9]+', subject)
        if words and words[-1] in furniture:
            return True
    return False


def classify(asset, style):
    t = tokens(asset)
    # Library/location prefixes describe the setting, not the support surface:
    # a Palace paving floor in hunting-river is still solid ground. Prefer the
    # authored object name for liquid/hazard inference; keep full tokens for
    # environmental search tags and existing attachment role classification.
    subject = asset.get('name') or asset.get('label') or asset.get('id', '')
    surface_words = set(re.findall(r'[a-z0-9]+', str(subject).lower()))
    solid_water_crossing = bool(surface_words & {'bridge', 'dock', 'pier', 'jetty', 'riverbank', 'bank'})
    explicit_water = bool(surface_words & {'water', 'pool', 'flooded', 'liquid'})
    named_waterway = bool(surface_words & {'river', 'canal'}) and not surface_words & {
        'stone', 'paving', 'pavement', 'cobblestone', 'palace', 'wall', 'stairs'}
    water_surface = (explicit_water or named_waterway) and not solid_water_crossing
    category = asset.get('category', '')
    kind = asset.get('kind', '')
    procedural = asset.get('procedural', {})
    role_hint = procedural.get('role', asset.get('role', category))
    wall_mounted = 'wallmounted' in t or {'wall', 'mounted'} <= t
    tabletop_provider = supporting_furniture(asset)
    map_reference = (kind in ('atlas', 'concept', 'reconstruction')
                     and str(asset.get('file', '')).endswith('.json') and 'source' in asset)
    patch = map_reference or kind in ('reconstruction_patch', 'composition_layer') or ('residual' in t and asset.get('reusable') is False)
    physical = bool(asset.get('views', {}).get('applicable')) or kind in ('tile', 'terrain_tile') or role_hint in ('ground', 'floor', 'wall', 'door', 'stairs', 'terrain')
    ui = kind in ('ui', 'ui_region', 'interface', 'icon', 'portrait') or category in ('ui', 'interface', 'menu') or (not physical and bool(t & {'tooltip', 'hotbar', 'hud', 'button', 'screen', 'portrait', 'badge', 'dialog', 'widget', 'panel'}))
    # An authored screen crop is always screen-space even when its name mentions
    # a floor/weapon; baked world crops are never procedural attachment providers.
    offered = []
    provider = False
    if not patch and not ui:
        floor = role_hint in ('ground', 'floor') or kind in ('terrain_tile', 'tile') and bool(t & {'floor', 'ground', 'surface', 'paving', 'cobblestone', 'cobbles'})
        mounted = wall_mounted or bool(t & {'torch', 'sconce', 'lamp', 'lantern', 'banner', 'sign', 'decoration', 'painting', 'clock', 'control'})
        wall = (role_hint == 'wall' or 'wall' in t) and not mounted
        if floor:
            provider = True
            offered.append('surface:lava' if 'lava' in surface_words else 'surface:water' if water_surface else 'surface:floor')
        if wall:
            provider = True; offered.append('surface:wall')
        if t & {'doorway', 'threshold'} or 'door' in t and bool(t & {'frame', 'opening'}):
            provider = True; offered.append('surface:doorway')
        if role_hint == 'stairs' or t & {'stairs', 'stair', 'stairway', 'staircase'}:
            provider = True; offered.append('surface:stairs')
        if 'ceiling' in t and not t & {'lamp', 'lantern', 'chandelier', 'hanging', 'pendant'}:
            provider = True; offered.append('surface:ceiling')
        if tabletop_provider:
            provider = True; offered.append('surface:tabletop')
    requires = {'any': [], 'all': [], 'none': []}
    if patch:
        space, role, reason = 'reconstruction', 'reconstruction', 'Baked source or residual crop: exact reconstruction only; no procedural attachment claim.'
        if map_reference:
            reason = 'Source reconstruction map reference; its JSON defines placements. No world support tile applies to the map document.'
    elif ui:
        space, role, reason = 'screen', 'screen', 'Screen-space composition only; world tile attachment does not apply.'
        requires['all'] = ['surface:screen']
        offered = ['surface:screen'] if t & {'panel', 'screen', 'hud', 'hotbar', 'dialog'} else []
    else:
        space, role = 'world', 'provider' if provider else 'object'
        reason = 'Editorial semantic suggestion; does not establish runtime placement, collision, seam, scale, or support geometry.'
        if provider and set(offered) & {'surface:floor', 'surface:water', 'surface:lava'} and set(offered) <= {'surface:floor', 'surface:water', 'surface:lava', 'surface:doorway'}:
            reason = 'Base surface provider; authored layout defines support and adjacency. No parent tile required.'
        else:
            target = 'floor'
            if wall_mounted:target = 'wall'
            elif t & {'hanging', 'chandelier', 'pendant'} or 'ceiling' in t and bool(t & {'lamp','lantern'}):target = 'ceiling'
            elif t & {'sconce', 'banner', 'walltorch', 'wallmounted'} or 'wall' in t and bool(t & {'torch', 'lamp', 'sign', 'decoration', 'lantern', 'control', 'painting', 'clock'}):target = 'wall'
            elif t & {'boat', 'raft', 'aquatic', 'fish'}:target = 'water'
            elif not tabletop_provider and t & {'tabletop', 'cutlery', 'plate', 'goblet'}:target = 'tabletop'
            elif t & {'door', 'doorway', 'gateway'} and 'surface:doorway' not in offered:target = 'doorway'
            requires['any'] = [f'surface:{target}']
            if target == 'floor':
                requires['none'] = ['hazard:water', 'hazard:lava', 'hazard:void', 'hazard:pit', 'hazard:chasm', 'surface:water', 'walkability:blocked']
                if category in ('actor', 'character', 'enemy') or kind == 'character':
                    requires['any'].append('surface:stairs')
                elif not provider and not t & {'rack', 'chest', 'barrel', 'crate', 'bed', 'chair', 'bench', 'bookcase', 'wardrobe', 'barricade', 'gate'} and (
                    category in ('equipment', 'weapon', 'armor', 'gear', 'consumable', 'loot') or
                    t & {'potion', 'antidote', 'bottle', 'scroll', 'book', 'key', 'coin', 'gem', 'ring', 'amulet', 'goblet', 'ration', 'sword', 'dagger', 'wand', 'shield'}):
                    requires['any'].append('surface:tabletop')
            elif target == 'water':requires['none'] = ['hazard:lava', 'surface:lava']
    generated = {'attachment-tagged', f'role:{role}', f'style:{style}'}
    for material in MATERIALS:
        if material in t:generated.add('material:' + material)
    for environment in ENVIRONMENTS:
        if environment in t or set(environment.split('-')) <= t:generated.add('environment:' + environment)
    authored = set(asset.get('tags', [])) - set(asset.get('attachment_generated_tags', []))
    if not any(v.startswith('environment:') for v in generated | authored):generated.add('environment:unspecified')
    if not any(v.startswith('material:') for v in generated | authored):generated.add('material:unspecified')
    generated.update(offered)
    generated.update('attachment:' + v.split(':', 1)[1] for v in requires['any'] + requires['all'] if v.startswith('surface:'))
    if 'surface:water' in offered:generated.add('hazard:water')
    if 'surface:lava' in offered:generated.add('hazard:lava')
    for hazard in ('void', 'pit', 'chasm'):
        if hazard in surface_words and provider:generated.add('hazard:' + hazard)
    walkable = procedural.get('walkable', asset.get('walkable'))
    if isinstance(walkable, bool):generated.add('walkability:' + ('allowed' if walkable else 'blocked'))
    return sorted(generated), {'schema_version': 1, 'authority': AUTHORITY, 'space': space, 'role': role,
        'requires': requires, 'provides': sorted(set(offered)),
        'exclude_self': True,
        'compatibility_group': group_id(style, requires) if space == 'world' and any(requires.values()) else None,
        'reason': reason}


def enrich_library(pack, index):
    """Mutate metadata in memory; safe before a builder writes every sidecar."""
    pack = Path(pack)
    style = style_of(pack)
    assets = index.get('assets', [])
    by_id = {a['id']: a for a in assets}
    # View generators can copy source tags without copying their ownership list.
    # Keep inherited generated roles replaceable when a clean world-space view
    # is derived from a reconstruction-only crop.
    inherited_generated = {a['id']: set(a.get('attachment_generated_tags', [])) for a in assets}
    for asset in assets:
        previous = set(asset.get('attachment_generated_tags', []))
        if asset.get('view') not in ('source', None):
            parent_id = asset.get('canonical_asset_id') or asset.get('object_id')
            previous.update(inherited_generated.get(parent_id, set()) & set(asset.get('tags', [])))
        asset['attachment_generated_tags'] = sorted(previous)
        tags, attachment = classify(asset, style)
        # Preserve all existing authored tags. Replace only our previous output.
        old = [v for v in asset.get('tags', []) if isinstance(v, str) and v not in previous]
        asset['tags'] = sorted(set(old + tags))
        asset['attachment_generated_tags'] = sorted(set(tags) - set(old))
        asset['attachment'] = attachment
    for asset in assets:
        parent_id = asset.get('canonical_asset_id') or asset.get('object_id')
        parent = by_id.get(parent_id)
        if parent is not None and parent is not asset and asset.get('view') not in ('source', None):
            if parent['attachment']['space'] == 'reconstruction' and asset.get('kind') not in ('reconstruction_patch', 'composition_layer') and asset.get('reusable') is not False:
                semantic = {**parent, 'kind': asset.get('kind', 'sprite'),
                    'category': asset.get('category') if asset.get('category') not in (None, 'reconstruction', 'composition') else 'prop',
                    'reusable': True, 'views': {'applicable': True}}
                tags, attachment = classify(semantic, style)
                own = [v for v in asset['tags'] if v not in asset['attachment_generated_tags']]
                asset['tags'] = sorted(set(own) | set(tags))
                asset['attachment_generated_tags'] = sorted(set(tags) - set(own))
                asset['attachment'] = attachment
                attachment['inferred_proxy_for'] = parent_id
                attachment['reason'] += ' This clean view is an inferred proxy for a baked source crop, not an exact recovered hidden surface.'
                continue
            asset['attachment'] = copy.deepcopy(parent['attachment'])
            asset['attachment']['inherited_from'] = parent_id
            own = [v for v in asset['tags'] if v not in asset['attachment_generated_tags']]
            asset['tags'] = sorted(set(own) | set(parent['tags']))
            asset['attachment_generated_tags'] = sorted(set(parent['tags']) - set(own))
    index['tags'] = sorted(set(index.get('tags', [])) | {'asset-library', 'attachment-tagged', 'metadata-document', 'style:' + style})
    # Pack roots live at either assets/style-packs/x, assets/book-tiles/x, or assets/reusable-gameplay.
    assets_root = next((p for p in [pack, *pack.parents] if p.name == 'assets'), DEFAULT_ASSETS)
    index['attachment_rules'] = Path(os.path.relpath(assets_root / RULES_NAME, pack)).as_posix()
    return index


def matches(tags, rule):
    tags = set(tags)
    return (not rule['any'] or bool(tags & set(rule['any']))) and set(rule['all']) <= tags and not bool(tags & set(rule['none']))


def enrich_document(doc, style, by_id=None):
    """Pure in-memory JSON enrichment for every builder-generated document."""
    by_id = by_id or {}
    def visit(value, trail=()):
        if isinstance(value, dict):
            ident = value.get('id')
            if isinstance(ident, str) and ident in by_id:
                for field in ('tags', 'attachment', 'attachment_generated_tags'):
                    value[field] = copy.deepcopy(by_id[ident][field])
            elif isinstance(ident, str) and any(k in value for k in ('image','file','asset','sourceBox','bounds','image_path')):
                tags, attachment = classify(value, style)
                old = set(value.get('tags', [])) - set(value.get('attachment_generated_tags', []))
                value['tags'] = sorted(old | set(tags))
                value['attachment_generated_tags'] = sorted(set(tags) - old)
                value['attachment'] = attachment
            elif ('frames' in trail and all(k in value for k in ('x', 'y', 'width', 'height'))
                    and not any(k in trail for k in ('bounds', 'anchor', 'source_rect', 'sourceBox',
                        'provenance', 'source', 'sources', 'generation', 'crop_bounds_px', 'normalization'))):
                # Runtime sprite atlases often key frames by character/pose
                # rather than repeating IDs. Tag the frame, not its geometry.
                context = ' '.join(str(k) for k in trail if k != 'frames')
                parent_file = doc.get('file', doc.get('image', '')) if isinstance(doc, dict) else ''
                kind = 'ui' if 'ui' in str(parent_file) else 'tile' if 'terrain' in str(parent_file) else 'sprite'
                semantic = {**value, 'id': context, 'name': context, 'kind': kind,
                    'category': 'ui' if kind == 'ui' else 'terrain' if kind == 'tile' else 'actor'}
                tags, attachment = classify(semantic, style)
                old = set(value.get('tags', [])) - set(value.get('attachment_generated_tags', []))
                value['tags'] = sorted(old | set(tags))
                value['attachment_generated_tags'] = sorted(set(tags) - old)
                value['attachment'] = attachment
            elif (isinstance(value.get('file'), str)
                    and Path(value['file']).suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg')
                    and any(k in trail for k in ('sprites', 'characters', 'forms', 'items', 'tiles', 'assets', 'components', 'icons', 'portraits'))
                    and not any(k in trail for k in ('provenance', 'source', 'sources', 'derived', 'generation'))):
                # Legacy manifests often use the dictionary key as identity.
                # Tag actual file-bearing asset records without adding IDs or
                # touching source provenance, dimensions, bounds or anchors.
                context = ' '.join(str(k) for k in trail) + ' ' + Path(value['file']).stem
                actor = any(k in trail for k in ('characters', 'forms')) or (
                    'sprites' in trail and any(k in value for k in ('frames', 'bodyHeight', 'poses')))
                interface = any(k in trail for k in ('icons', 'portraits'))
                tile = 'tiles' in trail or value.get('role') in ('ground', 'floor', 'wall', 'stairs')
                semantic = {**value, 'id': context,
                    'kind': value.get('kind', 'ui' if interface else 'tile' if tile else 'sprite'),
                    'category': value.get('category', 'ui' if interface else 'actor' if actor else value.get('role', 'prop'))}
                tags, attachment = classify(semantic, style)
                old = set(value.get('tags', [])) - set(value.get('attachment_generated_tags', []))
                value['tags'] = sorted(old | set(tags))
                value['attachment_generated_tags'] = sorted(set(tags) - old)
                value['attachment'] = attachment
            for key, item in list(value.items()):
                if key not in ('tags', 'attachment', 'attachment_generated_tags'):visit(item, (*trail, key))
        elif isinstance(value, list):
            for number, item in enumerate(value):visit(item, (*trail, number))
    visit(doc)
    if isinstance(doc, dict) and (not isinstance(doc.get('id'), str) or doc.get('id') not in by_id):
        doc['tags'] = sorted(set(doc.get('tags', [])) | {'attachment-tagged', 'metadata-document'})
    return doc


def registry_libraries(root):
    registry = json.loads((root / 'reusable-library.json').read_text())
    result = []
    for entry in registry['libraries']:
        base = root / entry['base']
        index_path = root / entry['index']
        if not index_path.is_file():raise ValueError(f'Missing library index: {index_path}')
        result.append((entry, base, index_path, json.loads(index_path.read_text())))
    return result


def central_rules(libraries):
    tiles, groups = [], {}
    for entry, pack, path, index in libraries:
        style = style_of(pack)
        by_id = {asset['id']: asset for asset in index['assets']}
        providers = {}
        for asset in index['assets']:
            a = asset['attachment']
            # Only canonical source assets advertise tile targets; six views and
            # normalized variants resolve to that same canonical provider.
            canonical = asset.get('canonical_asset_id') or asset.get('object_id')
            if a['space'] == 'world' and a['provides'] and (not canonical or canonical == asset['id']) and asset.get('view') in ('source', None):
                providers[asset['id']] = {'id': entry['id'] + '::' + asset['id'], 'library_id': entry['id'], 'asset_id': asset['id'],
                    'style': style, 'tags': asset['tags'], 'provides': a['provides']}
            group = a['compatibility_group']
            if group is not None:
                groups.setdefault(group, {'id': group, 'style': style, 'requires': a['requires'], 'tile_ids': []})
        # Baked primary crops are reconstruction references, never usable
        # supports. A reviewed clean FRONT can represent their physical parent.
        # Reuse the portable contract's actual-file/source/six-view verification;
        # worker completion flags alone are not independent approval.
        if index.get('view_review'):
            from view_review_contract import load_review
            report = load_review(pack, index)
            approved = {record['object_id'] for record in report['sets'] if record.get('complete') is True}
            for group in index.get('view_sets', []):
                oid = group['object_id']
                parent = by_id.get(oid, {})
                if oid not in approved or oid in providers or parent.get('attachment', {}).get('space') != 'reconstruction':
                    continue
                reference = group.get('views', {}).get('front')
                leaf_id = reference.get('asset_id') if isinstance(reference, dict) else reference
                leaf = by_id.get(leaf_id, {})
                attachment = leaf.get('attachment', {})
                if (leaf.get('object_id') != oid or leaf.get('view') != 'front'
                        or leaf.get('reusable') is False or leaf.get('kind') in ('reconstruction_patch', 'composition_layer')
                        or not leaf.get('image', {}).get('path')
                        or attachment.get('space') != 'world' or not attachment.get('provides')):
                    continue
                providers[oid] = {'id': entry['id'] + '::' + oid, 'library_id': entry['id'],
                    'asset_id': leaf_id, 'canonical_asset_id': oid, 'representative_view': 'front',
                    'style': style, 'tags': leaf['tags'], 'provides': attachment['provides']}
        tiles.extend(providers.values())
    for group in groups.values():
        candidates = {t['id'] for t in tiles if matches(set(t['tags']) | set(t['provides']), group['requires'])}
        # Requirements are shared by many assets. Excluding every group member
        # would also remove OTHER valid supports. Consumers exclude only the
        # queried canonical asset, using attachment.exclude_self.
        group['tile_ids'] = sorted(candidates)
        group['preferred_tile_ids'] = sorted(t['id'] for t in tiles if t['style'] == group['style'] and t['id'] in candidates)
        group['reason'] = 'Editorial candidate providers across all styles; same-style providers are a visual preference. Geometry and runtime placement still require review.' if group['tile_ids'] else 'No registered provider advertises the required surface; author or review a provider before placement.'
    groups = [groups[k] for k in sorted(groups)]
    return {'schema_version': 1, 'tags': ['attachment-rules', 'editorial', 'placement-suggestions'], 'authority': AUTHORITY,
        'semantics': {'any': 'At least one listed tag must be offered; an empty list imposes no any requirement.',
            'all': 'Every listed tag must be offered.', 'none': 'No listed tag may be offered.',
            'scope': 'tile_ids contains semantic candidates across every registered library and style. preferred_tile_ids is the same-style visual subset; style never blocks semantic compatibility. Qualified IDs use library_id::asset_id.',
            'exclude_self': 'When attachment.exclude_self is true, remove only library_id::canonical_asset_id for the queried asset (fall back to object_id, then id). Shared group candidates may include that identity; other group members remain compatible.',
            'limits': 'Editorial semantic compatibility only. Does not change or certify walkability, collision, footprint, load bearing, scene geometry, or gameplay.'},
        'surface_vocabulary': ['surface:' + v for v in SURFACES],
        'groups': groups, 'tiles': sorted(tiles, key=lambda t: t['id'])}


def apply(root=DEFAULT_ASSETS, check=False):
    root = Path(root).resolve()
    libraries = registry_libraries(root)
    for entry, pack, path, index in libraries:enrich_library(pack, index)
    central = central_rules(libraries)
    groups = {g['id']: g for g in central['groups']}
    by_pack = []
    planned = {root / RULES_NAME: central}
    asset_count = 0
    for entry, pack, index_path, index in libraries:
        by_id = {a['id']: a for a in index['assets']}
        for asset in index['assets']:
            metadata = asset.get('metadata_path')
            if metadata:
                destination = (pack / metadata).resolve()
                if not destination.is_relative_to(root):raise ValueError('Sidecar escapes assets root')
                planned[destination] = asset
            asset_count += 1
        planned[index_path] = index
        by_pack.append((pack, by_id))
    # Enrich original manifests, atlases, maps and JSON sidecars, including assets
    # outside registered reusable packs. Never reinterpret gameplay properties.
    preserved_generation_documents = 0
    for path in sorted(root.rglob('*.json')):
        if path in planned or '__pycache__' in path.parts:continue
        # Generation receipts, recipes, candidate manifests and snapshots pin
        # one another's exact bytes. They are evidence, not catalog assets.
        # Current asset sidecars (including nested ones) are already planned
        # above; keep enriching worker indexes, but preserve other documents
        # in the generation workspaces instead of invalidating their hashes.
        parts = path.relative_to(root).parts
        in_generation_workspace = any(
            part == 'reusable' and parts[i + 1].startswith('views-')
            for i, part in enumerate(parts[:-1]))
        is_worker_index = (path.name == 'set-index.json'
                           and path.parent.name.startswith('views-')
                           and path.parent.parent.name == 'reusable')
        if in_generation_workspace and not is_worker_index:
            preserved_generation_documents += 1
            continue
        doc = json.loads(path.read_text())
        local = next((items for pack, items in by_pack if path.is_relative_to(pack)), {})
        style = next((style_of(pack) for pack, items in by_pack if path.is_relative_to(pack)), 'gameplay')
        planned[path] = enrich_document(doc, style, local)
    # Anonymous legacy frames and original manifests may introduce additional
    # requirement combinations. Every JSON group reference must still resolve.
    def ensure_groups(value):
        if isinstance(value, dict):
            attachment = value.get('attachment')
            if isinstance(attachment, dict):
                ident = attachment.get('compatibility_group')
                if ident is not None and ident not in groups:
                    style = ident.split('--attachment-', 1)[0]
                    rule = attachment['requires']
                    candidates = [t for t in central['tiles'] if matches(t['tags'], rule)]
                    group = {'id': ident, 'style': style, 'requires': rule,
                        'tile_ids': sorted(t['id'] for t in candidates),
                        'preferred_tile_ids': sorted(t['id'] for t in candidates if t['style'] == style),
                        'reason': 'Editorial candidate providers across all styles; geometry and runtime placement still require review.' if candidates else 'No registered provider advertises the required surface; author or review a provider before placement.'}
                    groups[ident] = group
            for key, item in value.items():
                if key not in ('tags', 'attachment', 'attachment_generated_tags'):ensure_groups(item)
        elif isinstance(value, list):
            for item in value:ensure_groups(item)
    for doc in planned.values():ensure_groups(doc)
    central['groups'] = [groups[k] for k in sorted(groups)]
    # Qualified references and rule groups must resolve deterministically.
    tile_ids = {t['id'] for t in central['tiles']}
    assert len(tile_ids) == len(central['tiles'])
    for group in central['groups']:assert set(group['tile_ids']) <= tile_ids
    changed = []
    for path, doc in sorted(planned.items()):
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent.is_relative_to(root)):
            raise ValueError(f'Refusing symlink metadata path: {path}')
        text = encoded(doc)
        if not path.exists() or path.read_text() != text:
            changed.append(str(path.relative_to(root)))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True);path.write_text(text)
    if check and changed:raise ValueError(f'Attachment metadata is stale in {len(changed)} JSON files; first: {changed[:8]}')
    return {'assets': asset_count, 'json_documents': len(planned), 'changed': len(changed), 'groups': len(groups), 'tile_providers': len(tile_ids),
        'preserved_generation_documents': preserved_generation_documents,
        'empty_groups_with_explicit_reason': sum(not g['tile_ids'] for g in central['groups'])}


def refresh_legacy_archives(root=DEFAULT_ASSETS, check=False):
    """Refresh JSON members only; preserve every existing non-JSON member byte.

    Reusable exports have localized indexes and are regenerated by their own
    packager, so they are deliberately outside this legacy archive operation.
    """
    root = Path(root).resolve()
    changed, members = [], 0
    for path in sorted(root.rglob('*.zip')):
        relative = path.relative_to(root)
        if 'reusable' in relative.parts or 'reusable-gameplay' in relative.parts:
            continue
        replacements = {}
        with ZipFile(path) as archive:
            infos = archive.infolist()
            if len({i.filename for i in infos}) != len(infos):raise ValueError(f'Duplicate archive members: {relative}')
            for info in infos:
                name = Path(info.filename)
                if name.is_absolute() or '..' in name.parts:raise ValueError(f'Unsafe archive member: {relative}')
                if name.suffix.lower() != '.json':continue
                source = next((parent / name for parent in [path.parent, *path.parent.parents] if parent.is_relative_to(root) and (parent / name).is_file()), None)
                if source is not None:
                    if not source.resolve().is_relative_to(root):raise ValueError(f'Archive source escapes assets: {relative}')
                    data = source.read_bytes()
                    if archive.read(info.filename) != data:replacements[info.filename] = data
            if not replacements:continue
            changed.append(relative.as_posix());members += len(replacements)
            if check:continue
            descriptor, temporary = tempfile.mkstemp(prefix='.attachment-zip-', suffix='.zip', dir=path.parent)
            os.close(descriptor)
            try:
                with ZipFile(temporary, 'w') as output:
                    output.comment = archive.comment
                    for info in infos:output.writestr(copy.copy(info), replacements.get(info.filename, archive.read(info.filename)))
                with ZipFile(temporary) as output:
                    if output.testzip() is not None:raise ValueError(f'Corrupt refreshed archive: {relative}')
                    for info in infos:
                        expected = replacements.get(info.filename, archive.read(info.filename))
                        if output.read(info.filename) != expected:raise ValueError(f'Archive byte mismatch: {relative}/{info.filename}')
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):os.unlink(temporary)
    if check and changed:raise ValueError(f'Stale legacy ZIP metadata in {len(changed)} archives: {changed[:5]}')
    return {'archives': len(changed), 'json_members': members, 'non_json_members_modified': 0}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--assets',type=Path,default=DEFAULT_ASSETS);p.add_argument('--refresh-archives',action='store_true');mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--apply',action='store_true');mode.add_argument('--check',action='store_true');args=p.parse_args()
    result=apply(args.assets,check=args.check)
    if args.refresh_archives:result['legacy_archives']=refresh_legacy_archives(args.assets,check=args.check)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
