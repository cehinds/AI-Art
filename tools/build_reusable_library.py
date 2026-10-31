#!/usr/bin/env python3
"""Build independent reuse catalogs across styles, book kits and gameplay art.

Existing source files are never rewritten. Book normalized exports remain distinct
from lossless native crops. --check performs all calculations without writes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from PIL import Image
from validate_pocket_reusable import view_set_approved
from build_pocket_reusable import (Builder, ROOT, MANAGER, VIEWS, canonical_hash,
    default_views, file_hash, image_bytes, json_bytes, read_json, unique_records)

ASSETS = ROOT / 'dungeon-crawler-tactics/Web/wwwroot/assets'
STYLES = ('pocket-dungeon','ink-and-lanterns','dungeon-after-dark')
TITLES = {'pocket-dungeon':'Pocket Dungeon','ink-and-lanterns':'Ink & Lanterns','dungeon-after-dark':'Dungeon After Dark'}

class BookBuilder(Builder):
    def __init__(self, assets_root, style):
        self.pack = assets_root / 'book-tiles' / style
        self.outputs, self.assets, self.residuals, self.maps = {}, {}, {}, []
        self.existing_index = read_json(self.pack / 'reusable/index.json', {})
        self.pixel_inventory = {}
        self.manifest = {'id':style,'title':TITLES[style]+' book locations','assets':[],'sheets':{},'conceptFiles':[]}
        self.normalized=[]
        self.native=[]
        self.coverage=[]
        for manifest_path in sorted(self.pack.glob('*/manifest.json')):
            kit=read_json(manifest_path)
            source=ROOT/'dungeon-crawler-tactics'/kit['assets'][0]['source']['file']
            raw=source.read_bytes()
            atlas=Image.open(source).convert('RGBA')
            source_path=f'reusable/sources/{kit["id"]}.png'
            self.outputs[source_path]=raw
            self.manifest['sheets'][kit['id']]={'file':source_path,'sha256':file_hash(raw)}
            for original in kit['assets']:
                if original['source']['sha256'] != file_hash(raw):
                    raise ValueError(f'Changed book atlas: {source}')
                image_path=f'{kit["id"]}/{original["file"]}'
                asset_id=original['id']
                b=original['source']['bounds'];rect=[b[k] for k in ('x','y','width','height')]
                anchor=original['anchor']
                meta={'schema_version':1,'managed_by':MANAGER,'id':asset_id,'name':original['label'],
                    'kind':'tile' if original['role']=='ground' else 'sprite','category':original['role'],
                    'tags':sorted(set([style,'book-location',kit['id'],original['role'],*original['tags']])),
                    'image':self.image_info(image_path),'metadata_path':str(Path(image_path).with_suffix('.json')),
                    'anchor_px':[anchor['x'],anchor['y']],'object_id':asset_id,'view':'source','reusable':True,
                    'footprint_tiles':[original['footprint']['width'],original['footprint']['height']],
                    'provenance':{'method':'existing','source_image':source_path,'source_sha256':file_hash(raw),
                        'source_rect':rect,'extraction':original['source'],'normalization':original['derived'],
                        'source_projection':'Hybrid gameplay map projection; image axes are not uniformly world elevation axes.',
                        'physical_frame':{'square_layout':original.get('squareLayout'),
                            'world_up':'+Z','map_x':'+X','map_y':'+Y',
                            'wall_extent_axis':original.get('placement',{}).get('axis') if original['role']=='wall' else None,
                            'interpretation':'north-wall extends along world X; west-wall extends along world Y. The vertical west-wall map strip is not a tall post. L wall corners encode plan footprints.',
                            'qualification':'Role-based intended frame for inferred illustrative views, not calibrated 3D geometry or evidence that generated views passed review.'},
                        'notes':'Existing normalized gameplay export reused unchanged. Resampling and opaque ground matting prevent treating it as exact native source pixels.'},
                    'procedural':{'eligible':True,'role':original['role'],'walkable':original.get('walkable',False),
                        'placement':original.get('placement'),'reason':'Existing normalized book kit; adjacency and seam review still required.'},
                    'views':default_views(original['role'])}
                if 'edges' in original:
                    meta['edges'] = original['edges']
                self.normalized.append(meta)
                native_id=asset_id+'--native'
                native_path=f'reusable/native/{native_id}.png'
                crop=atlas.crop((b['x'],b['y'],b['x']+b['width'],b['y']+b['height']))
                crop_raw=image_bytes(crop)
                self.outputs[native_path]=crop_raw
                native={**meta,'id':native_id,'name':original['label']+' (native source crop)',
                    'image':self.image_info(native_path,crop,crop_raw),'metadata_path':native_path[:-4]+'.json',
                    'reusable':False,'view':'native-source','canonical_asset_id':asset_id,
                    'anchor_px':[crop.width/2,crop.height],
                    'provenance':{'method':'extracted','source_image':source_path,'source_sha256':file_hash(raw),
                        'source_rect':rect,'notes':'Lossless bounding rectangle, including native transparent pixels. Companion to normalized gameplay export; not resampled.'},
                    'procedural':{'eligible':False,'reason':'Use the normalized companion for grid placement.'},
                    'views':{'applicable':False,'complete':True,'reason':'Alternate native crop of the same object; principal views are attached to canonical_asset_id.'}}
                self.native.append(native)
                self.manifest['assets'].append({'id':native_id,'source':{'sheet':kit['id'],
                    'bounds':{'x':b['x']+4,'y':b['y']+4,'width':b['width'],'height':b['height']}}})
            self.coverage.append({'source':source_path,'source_kind':'book-atlas','kit':kit['id'],
                'native_asset_count':len(kit['assets']),'normalized_asset_count':len(kit['assets']),
                'notes':'Native crop plus residual map reconstructs atlas; normalized exports are separate reusable gameplay assets.'})
        unique_records(self.normalized,'id','book normalized components')
        self.outputs['manifest.json']=json_bytes(self.manifest)
        self.outputs['reusable/library-guide.json']=json_bytes({'schema_version':1,'tags':['metadata-document','library-guide'],'title':'Book location reuse library','notes':['Existing normalized components are reused unchanged.','Native crops and 64px residuals reconstruct the source atlases exactly.','Generated hidden views are inferred designs.','Floor tiles are modeled surfaces, not evidence of original unseen geometry.']})

    def add_procedural(self):
        import random
        tiles=[]
        for source in self.normalized:
            if source['category']!='ground':continue
            points=source['procedural']['placement']['points']
            x,y=min(p[0] for p in points),min(p[1] for p in points)
            right,bottom=max(p[0] for p in points),max(p[1] for p in points)
            if right-x!=128 or bottom-y!=128:raise ValueError('Book floor placement is not a128px square: '+source['id'])
            crop=self.open_image(source['image']['path']).crop((x,y,right,bottom))
            tile_id=source['id']+'--surface';path=f'reusable/procedural/tiles/{tile_id}.png';raw=image_bytes(crop)
            self.outputs[path]=raw
            tile={**source,'id':tile_id,'name':source['name']+' (128px square surface)',
                'kind':'terrain_tile','image':self.image_info(path,crop,raw),'metadata_path':path[:-4]+'.json',
                'canonical_asset_id':source['id'],'view':'normalized-surface','anchor_px':[0,0],
                'provenance':{'method':'extracted','source_image':source['image']['path'],
                    'source_sha256':source['image']['sha256'],'source_rect':[x,y,128,128],
                    'notes':'Exact crop of the existing normalized gameplay export, not native source-atlas pixels. No additional resampling.'},
                'procedural':{'eligible':True,'cell_size_px':128,'walkable':True,
                    'connections':[side for side in ('north','east','south','west')
                        if 'join.floor' in source.get('edges',{}).get(side,[]) and 'join.manual' not in source.get('edges',{}).get(side,[])],
                    'rotation_degrees':[0,90,180,270],
                    'edge_policy':'Authored side tags govern connections. Manual transition surfaces require placement review; visible repeat seams remain possible.'},
                'views':{'applicable':False,'complete':True,'reason':'Surface crop variant; physical tile views attach to canonical_asset_id.'}}
            self.metadata(tile);tiles.append(tile)
        rng=random.Random(23);width,height,size=12,10,128
        walk={(1,1)};x,y=1,1
        for _ in range(90):
            dx,dy=rng.choice(((1,0),(-1,0),(0,1),(0,-1)));x=max(1,min(width-2,x+dx));y=max(1,min(height-2,y+dy));walk.add((x,y))
        for x in range(1,width-1):walk.add((x,1))
        for y in range(1,height-1):walk.add((width-2,y))
        canvas=Image.new('RGBA',(width*size,height*size),(20,18,35,255));cells=[]
        # One kit keeps the example visually coherent; all186 material surfaces remain cataloged.
        candidates=[t for t in tiles if 'starter-dungeon' in t['tags'] and len(t['procedural']['connections'])==4]
        if not candidates:
            raise ValueError('Procedural sample requires a starter-dungeon floor with four authored join.floor sides')
        for y in range(height):
            for x in range(width):
                cell={'x':x,'y':y,'walkable':(x,y) in walk,'connections':[]}
                if (x,y) in walk:
                    tile=rng.choice(candidates);rotation=rng.choice((0,90,180,270))
                    canvas.alpha_composite(self.open_image(tile['image']['path']).rotate(rotation),(x*size,y*size))
                    cell.update(asset_id=tile['id'],path=tile['image']['path'],rotation_deg=rotation,position_px=[x*size,y*size],anchor_px=[0,0])
                    cell['connections']=[name for name,dx,dy in [('north',0,-1),('east',1,0),('south',0,1),('west',-1,0)] if (x+dx,y+dy) in walk]
                cells.append(cell)
        limitations='Surface PNGs are exact crops of existing normalized128px gameplay exports. They are not native atlas pixels. Repeat seams may be visible; dark cells are uncarved void, not walls. Wall/door adjacency still requires review.'
        recipe={'schema_version':1,'seed':23,'rotation_convention':'counterclockwise',
            'grid':{'width':width,'height':height,'cell_size_px':size},'entry':[1,1],'exit':[width-2,height-2],
            'validation':{'all_walkable_cells_connected':True,'reachable_walkable_cells':len(walk)},
            'cells':cells,'objects':[],'limitations':limitations,
            'generator':'tools/build_reusable_library.py --kind books --style '+self.manifest['id']}
        recipe_raw=json_bytes(recipe);preview_raw=image_bytes(canvas)
        self.outputs['reusable/procedural/sample.json']=recipe_raw;self.outputs['reusable/procedural/sample.png']=preview_raw
        return {'status':'sample-available','recipe':'reusable/procedural/sample.json','preview':'reusable/procedural/sample.png',
            'seed':23,'grid':recipe['grid'],'rotation_convention':'counterclockwise','generator':'python '+recipe['generator'],
            'recipe_sha256':file_hash(recipe_raw),'preview_sha256':file_hash(preview_raw),'limitations':limitations}

    def existing_components(self):
        for item in self.normalized+self.native:self.metadata(item)
        self.procedural_settings=self.add_procedural()

    def build(self):
        outputs=super().build()
        index=json.loads(outputs['reusable/index.json'])
        sets={x['object_id'] for x in index['view_sets'] if x.get('complete')}
        for row in self.coverage:
            parents=[a for a in self.normalized if row['kit'] in a['tags']]
            row['six_view_object_count']=sum(a['id'] in sets for a in parents)
            row['uncovered_object_ids']=[a['id'] for a in parents if a['id'] not in sets]
        index['coverage']=self.coverage
        index['statistics']['existing_components_reused']=len(self.normalized)
        index['statistics']['native_components_extracted']=len(self.native)
        index['statistics']['book_kit_count']=len(self.coverage)
        index['procedural']=self.procedural_settings
        outputs['reusable/index.json']=json_bytes(index)
        return outputs


def apply_association(region, style):
    region=dict(region)
    associations=read_json(ROOT/'tools/scene_object_associations.json',{'regions':{}})['regions']
    association=associations.get(style+':'+region['id'],associations.get(region['id']))
    if region['kind']=='reconstruction_patch':
        region['physical']=True
        region['notes']=region.get('notes','')+' Physical scene reference; clean principal views are tracked separately.'
    if association:
        region.update({key:association[key] for key in ('object_id','physical') if key in association})
        region['association']=association
    return region


def resolve_references(builder,index):
    groups={g['object_id']:g for g in index['view_sets']}
    assets={a['id']:a for a in index['assets']}
    for asset in index['assets']:
        if not asset.get('views',{}).get('applicable'):continue
        object_id=asset.get('object_id',asset['id']);group=groups.get(object_id)
        if not group:continue
        resolved={}
        for view in VIEWS:
            target=group['views'].get(view)
            if isinstance(target,dict):target=target.get('asset_id')
            valid=target in assets and assets[target].get('object_id')==object_id and assets[target].get('view')==view
            resolved[view]={'status':'inferred' if valid else 'missing','asset_id':target if valid else None}
        asset['views']={'applicable':True,'complete':view_set_approved(group) and all(r['asset_id'] for r in resolved.values()),**resolved}
        if not view_set_approved(group):asset['views']['reason']='Principal views exist but the set remains unapproved or unfinished.'
        for qa_field in ('quality_status','geometry_qa','quality_review'):
            if qa_field in group:asset['views'][qa_field]=group[qa_field]
        builder.outputs[asset['metadata_path']]=json_bytes(asset)
    index['statistics']['physical_assets_missing_six_views']=sum(a.get('views',{}).get('applicable',False) and not a['views'].get('complete',False) for a in index['assets'])
    physical=[a for a in index['assets'] if a.get('views',{}).get('applicable')]
    index['statistics']['physical_reference_count']=len(physical)
    index['statistics']['canonical_physical_object_count']=len({a.get('object_id',a['id']) for a in physical})
    index['statistics']['canonical_physical_objects_missing_six_views']=len({a.get('object_id',a['id']) for a in physical if not a['views'].get('complete')})
    index['scene_object_coverage']=[{'asset_id':a['id'],'object_id':a.get('object_id',a['id']),
        'source':a['provenance'].get('source_image'),'source_rect':a['provenance'].get('source_rect'),
        'label':a['name'],'six_views_complete':a['views'].get('complete',False),
        'association':a.get('association')} for a in index['assets'] if a['kind']=='reconstruction_patch' and a.get('views',{}).get('applicable')]
    return index


class StyleBuilder(Builder):
    def __init__(self, pack):
        super().__init__(pack)
        self.outputs.update(extract_style_regions(pack.name))

    def build(self):
        outputs=super().build();index=resolve_references(self,json.loads(outputs['reusable/index.json']))
        index['coverage']=[]
        for entry in index['maps']:
            native=[a for a in index['assets'] if a.get('provenance',{}).get('source_image')==entry['source'] and a.get('view') not in VIEWS and a['kind']!='reconstruction_patch']
            physical=[a for a in index['assets'] if a.get('provenance',{}).get('source_image')==entry['source'] and a.get('views',{}).get('applicable')]
            index['coverage'].append({'source':entry['source'],'source_kind':entry['kind'],
                'native_asset_count':len(native),'normalized_asset_count':0,
                'six_view_object_count':len({a.get('object_id',a['id']) for a in physical if a['views'].get('complete')}),
                'uncovered_object_ids':sorted({a.get('object_id',a['id']) for a in physical if not a['views'].get('complete')}),
                'statistics':entry.get('statistics',{})})
        outputs['reusable/index.json']=json_bytes(index);return outputs


def region_asset(builder, source_path, region, style):
    if getattr(builder,'_region_cached_path',None)!=source_path:
        builder._region_cached_path=source_path
        builder._region_cached_image=builder.open_image(source_path)
    source=builder._region_cached_image
    x,y,w,h=region['rect']
    if min(x,y)<0 or min(w,h)<=0 or x+w>source.width or y+h>source.height:
        raise ValueError(f'Region out of bounds: {region["id"]}')
    crop=source.crop((x,y,x+w,y+h))
    if region.get('mask'):
        import numpy as np
        from scipy import ndimage
        spec=region['mask'];pixels=np.array(crop)
        if spec['method']=='border-color-distance':
            border=np.concatenate((pixels[0,:,:3],pixels[-1,:,:3],pixels[:,0,:3],pixels[:,-1,:3]))
            background=np.median(border,axis=0)
            distance=np.linalg.norm(pixels[:,:,:3].astype(float)-background,axis=2)
            keep=(distance>spec.get('distance_threshold',45)) & (pixels[:,:,3]>0)
            labels,count=ndimage.label(keep,structure=np.ones((3,3)))
            sizes=np.bincount(labels.ravel());keep &= sizes[labels]>=spec.get('minimum_island_pixels',3)
            fraction=float(np.mean(keep))
            if fraction<0.015 or fraction>0.8:return None
        else:
            labels,_=ndimage.label(pixels[:,:,3]>spec.get('threshold',16),structure=np.ones((3,3)))
            sx,sy=spec['seed'];label=labels[sy-y,sx-x]
            if not label:raise ValueError(f'Alpha seed outside visible island: {region["id"]}')
            keep=labels==label
            if spec.get('fringe',2):keep=ndimage.binary_dilation(keep,iterations=spec.get('fringe',2))
        pixels[~keep]=0;crop=Image.fromarray(pixels)
    path=f'{getattr(builder, "native_directory", "reusable/native")}/{region["id"]}.png'
    raw=image_bytes(crop);builder.outputs[path]=raw
    physical=region.get('physical',False)
    if not hasattr(builder,'_region_source_info'):builder._region_source_info={}
    if source_path not in builder._region_source_info:builder._region_source_info[source_path]=builder.image_info(source_path)
    asset={'schema_version':1,'managed_by':MANAGER,'id':region['id'],'name':region['label'],
        'kind':region['kind'],'category':region.get('category',region['kind']),
        'tags':sorted(set([style,*region.get('tags',[])])),
        'image':builder.image_info(path,crop,raw),'metadata_path':path[:-4]+'.json',
        'anchor_px':region.get('anchor_px',[w/2,h]),'view':region.get('view','source'),
        'object_id':region.get('object_id',region['id']),'reusable':region.get('reusable',True),
        'provenance':{'method':'extracted','source_image':source_path,
            'source_sha256':builder._region_source_info[source_path]['sha256'],'source_rect':[x,y,w,h],
            'mask':region.get('mask'),'notes':region.get('notes','Lossless native-pixel extraction.')},
        'procedural':{'eligible':region.get('procedural',False),'reason':region.get('procedural_reason','Review scale, seams and collision before procedural placement.')},
        'views':default_views('prop') if physical else {'applicable':False,'complete':True,'reason':region.get('view_reason',
            'Alternate camera or native crop of the same physical pose; principal views attach to canonical_asset_id.' if region.get('canonical_asset_id') else
            'Screen-space graphic, effect or non-physical source region; no independent physical principal views.')}}
    if region.get('canonical_asset_id'):asset['canonical_asset_id']=region['canonical_asset_id']
    for field in ('pose','source_direction','character_id'):
        if field in region:asset[field]=region[field]
    if region.get('association'):asset['association']=region['association']
    if region.get('reconstruction_placement') is False:
        if physical or region.get('reusable',True):
            raise ValueError('Unplaced composition references must be nonphysical and nonreusable: '+region['id'])
        asset['reconstruction']={'placement':False,
            'reason':'Composition reference only. Individual occurrence crops and explicit residuals reconstruct this source.'}
    return asset


def extract_style_regions(style):
    specification=read_json(ROOT/'tools/style_scene_regions.json',{'sources':[]})
    pack=ASSETS/'style-packs'/style
    builder=Builder(pack);builder.native_directory="reusable/scene-assets";items=[];placements={}
    for source in specification['sources']:
        if source['style']!=style:continue
        for region in source['regions']:
            region=apply_association(region,style)
            asset=region_asset(builder,source['path'],region,style)
            # Scene integration is extension-owned; keep its metadata intact.
            asset['managed_by']='reusable-scene-extraction-v1'
            builder.metadata(asset);items.append(asset)
            placements.setdefault(source['path'],[]).append({'asset_id':asset['id'],'x':region['rect'][0],'y':region['rect'][1]})
            if ('icon' in region['id'] or 'toggle' in region['id']) and region['kind']=='ui' and region['rect'][2]<=110 and region['rect'][3]<=90 and 'spell' not in region['id'] and not (style=='dungeon-after-dark' and region['id'].endswith('--move-icon')):
                overlay={**region,'id':region['id']+'--transparent','label':region['label']+' transparent pixel overlay',
                    'mask':{'method':'border-color-distance','distance_threshold':45,'minimum_island_pixels':3},
                    'tags':[*region.get('tags',[]),'transparent-overlay','derived-alpha'],
                    'notes':'Native RGB/alpha pixels retained where they differ from median border color; remaining pixels cleared. Decorative backing/fringes may remain. The unmasked native crop is retained separately.',
                    'physical':False}
                transparent=region_asset(builder,source['path'],overlay,style)
                if transparent:
                    transparent['managed_by']='reusable-scene-extraction-v1'
                    builder.metadata(transparent);items.append(transparent)
                    placements[source['path']].append({'asset_id':transparent['id'],'x':region['rect'][0],'y':region['rect'][1]})
    if items:
        builder.outputs['reusable/scene-assets/index.json']=json_bytes({'schema_version':1,'assets':items,'placements':placements})
    return builder.outputs



class GameplayBuilder(Builder):
    def __init__(self):
        self.pack=ASSETS/'reusable-gameplay'
        self.outputs,self.assets,self.residuals,self.maps={},{},{},[]
        self.existing_index=read_json(self.pack/'reusable/index.json',{})
        self.pixel_inventory={}
        self.manifest={'id':'gameplay','title':'Gameplay, interface and concepts','assets':[],'sheets':{},'conceptFiles':[]}
        self.semantic=[];self.coverage=[]
        self.original_paths=[]
        excluded={'style-packs','book-tiles','fonts','reusable-gameplay'}
        manual=read_json(ROOT/'tools/all_asset_scene_regions.json',{'sources':[]})
        manual_by_path={x['path']:[dict(r) for r in x['regions']] for x in manual['sources']}
        for path,regions in manual_by_path.items():
            if path not in ('revamp/characters.png','revamp/enemies.png','revamp/mongo.png'):continue
            seen=set();prefix=path[:-4].replace('/','-')+'-'
            for r in regions:
                suffix=r['id'].removeprefix(prefix);name,pose=suffix.split('-',1)
                root=path[:-4].replace('/','--')+'--'+name
                first=root not in seen;seen.add(root)
                identity=root if first else root+'--'+pose
                r.update(id=identity,physical=True,canonical_asset_id=identity,object_id=identity,
                    pose=pose,character_id=root,view='source')
        source_files=[p for d in sorted(ASSETS.iterdir()) if d.is_dir() and d.name not in excluded for p in sorted(d.rglob('*.png'))]
        source_files+=sorted(ASSETS.glob('*.png'))
        for source in source_files:
                relative=source.relative_to(ASSETS).as_posix();self.original_paths.append(relative)
                source_path='reusable/sources/'+relative
                raw=source.read_bytes();self.outputs[source_path]=raw
                image=Image.open(source).convert('RGBA');sheet=relative[:-4].replace('/','--')
                self.manifest['sheets'][sheet]={'file':source_path,'sha256':file_hash(raw)}
                regions=manual_by_path.get(relative)
                if regions is None:regions=self.automatic_regions(relative,image)
                for region in regions:
                    region=apply_association(region,'gameplay')
                    asset=region_asset(self,source_path,region,'gameplay');self.semantic.append(asset)
                    x,y,w,h=region['rect']
                    if region.get('reconstruction_placement',True):
                        self.manifest['assets'].append({'id':asset['id'],'source':{'sheet':sheet,'bounds':{'x':x+4,'y':y+4,'width':w,'height':h}}})
                self.coverage.append({'source':source_path,'original_source':relative,'native_asset_count':len(regions),
                    'physical_object_count':sum(x.get('physical',False) for x in regions),
                    'status':'semantic-regions' if regions else ('derived-diagnostic-preview' if Path(relative).stem in ('projection-comparison','contact-sheet','roster-contact') else 'source-only-awaiting-review'),
                    'normalized_asset_count':0,
                    'notes':'Exact source reconstruction includes separately labeled residuals.'})
        unique_records(self.semantic,'id','gameplay extracted semantic assets')
        semantic_by_id={asset['id']:asset for asset in self.semantic}
        for suffix in ('a','b','c','d'):
            alias=semantic_by_id['room-kit--concept--stone-'+suffix]
            canonical=semantic_by_id['dungeon-stone--stone-'+suffix]
            if alias['image']['rgba_sha256']!=canonical['image']['rgba_sha256']:
                raise ValueError('Previously identical stone tile alias changed; review canonical identity')
            alias['object_id']=canonical['id'];alias['canonical_asset_id']=canonical['id']
            alias['deduplication']={'method':'exact-rgba','canonical_asset_id':canonical['id'],
                'reason':'Existing room-kit concept tile has identical dimensions and RGBA to the dungeon-stone tile. Reuse its physical views.'}

        self.outputs['manifest.json']=json_bytes(self.manifest)
        self.outputs['reusable/library-guide.json']=json_bytes({'schema_version':1,'tags':['metadata-document','library-guide'],'title':'Gameplay reuse library','notes':['Sources are unmodified copies of repository originals.','Native crops preserve pixels; residuals are reconstruction-only.','Existing animation poses are distinct from inferred principal views.']})

    def automatic_regions(self, relative, image):
        directory=relative.split('/')[0];name=Path(relative).stem;identity=relative[:-4].replace('/','--')
        manifest=read_json(ASSETS/directory/'manifest.json',{})
        def region(identity,label,rect,physical=True,**extra):
            return {'id':identity,'label':label,'rect':rect,'physical':physical,'kind':'sprite' if physical else 'ui','category':'prop' if physical else 'ui','tags':[directory,name],**extra}
        def frames_for(frames,root):
            result=[];pose_roots={}
            def visit(node,keys):
                if isinstance(node,dict) and all(k in node for k in ('x','y','width','height')):
                    first=not result;rid=root if first else root+'--'+'--'.join(keys)
                    directions={'se','sw','ne','nw','front','rear','right','left','top','bottom'}
                    pose='--'.join(k for k in keys if k not in directions) or 'idle'
                    new_pose=pose not in pose_roots
                    canonical=pose_roots.setdefault(pose,rid)
                    result.append(region(rid,rid.replace('--',' '),[node[k] for k in ('x','y','width','height')],new_pose,
                        canonical_asset_id=canonical,object_id=canonical,pose=pose,character_id=root,
                        source_direction=next((k for k in keys if k in directions),None),
                        view='source' if new_pose else 'animation-camera',kind='sprite',category='actor'))
                elif isinstance(node,dict):
                    for key,value in node.items():visit(value,keys+[str(key)])
                elif isinstance(node,list):
                    for i,value in enumerate(node):visit(value,keys+[str(i)])
            visit(frames,[]);return result
        for section in ('characters','forms'):
            for record in manifest.get(section,{}).values():
                if record.get('file')==Path(relative).name and '/' not in relative[len(directory)+1:]:
                    return frames_for(record['frames'],identity)
        for record in manifest.get('sprites',{}).values():
            if record.get('file')==Path(relative).name and record.get('frames'):
                width,height=record['frameWidth'],record['frameHeight']
                return [region(identity if i==0 else identity+f'--frame-{i}',name+f' frame {i}',[i*width,0,width,height],True,
                    canonical_asset_id=identity if i==0 else identity+f'--frame-{i}',object_id=identity if i==0 else identity+f'--frame-{i}',
                    pose=record.get('poses',[f'frame-{n}' for n in range(record['frames'])])[i],character_id=identity,
                    view='source',kind='sprite',category='actor') for i in range(record['frames'])]
        if directory=='revamp':
            for json_path in (ASSETS/directory).glob('*-art.json'):
                doc=read_json(json_path)
                records=[doc]+[v for v in doc.values() if isinstance(v,dict)]
                for record in records:
                    if record.get('file')==Path(relative).name and record.get('frames'):
                        result=[]
                        for object_name,frames in record['frames'].items():
                            result+=frames_for(frames,identity+'--'+object_name)
                        if name=='effects':
                            for item in result:item.update(physical=False,kind='effect',category='effect')
                        return result
                    if record.get('image')==Path(relative).name and record.get('sprites'):
                        return [region(identity+'--'+sprite,sprite,[i%record['columns']*record['cellWidth'],i//record['columns']*record['cellHeight'],record['cellWidth'],record['cellHeight']],True,kind='tile' if i<4 else 'sprite') for i,sprite in enumerate(record['sprites'])]
        raw_regions=[]
        def native(root, label, box, suffix='native'):
            x,y,right,bottom=box
            return region(root+'--'+suffix,label+' native source',[x,y,right-x,bottom-y],False,
                kind='sprite',category='source-variant',canonical_asset_id=root,view='native-pose',reusable=False,
                notes='Exact native source window; normalized companion is the canonical gameplay object.')
        if directory=='dungeon-stone' and '/source/' in relative:
            if name=='floors':
                for item in read_json(ASSETS/directory/'floors-manifest.json')['assets']:
                    raw_regions.append(native(directory+'--'+item['id'],item['id'],item['sourceBox']))
            elif name=='walls':
                for item in read_json(ASSETS/directory/'walls-manifest.json')['sprites'].values():
                    raw_regions.append(native(directory+'--'+Path(item['file']).stem,Path(item['file']).stem,item['sourceCrop']))
        if directory=='room-kit' and '/source/' in relative:
            for item in read_json(ASSETS/directory/'source/extraction.json',[]):
                if item['source']==Path(relative).name:
                    root=directory+'--'+item['output'][:-4].replace('/','--')
                    raw_regions.append(native(root,item['id'],item['sourceBox']))
        if directory=='house' and '/source/' in relative:
            for key,item in manifest['components'].items():raw_regions.append(native(directory+'--'+key,key,item['sourceCell']))
        grids={
            'bosses/source-atlas.png':(4,3,[f'{obj}--frame-{frame}' for obj in ('hoarder','juicer','swine') for frame in range(4)]),
            'expedition-enemies/source/elemental.png':(4,3,[f'{obj}--frame-{frame}' for obj in ('sludge','cinder','frost') for frame in range(4)]),
            'expedition-enemies/source/constructs.png':(4,3,[f'{obj}--frame-{frame}' for obj in ('spore','sentry','mauler') for frame in range(4)]),
            'scenario-props/source-atlas.png':(4,2,['garbage','bench','barrier','parts',*[f'scatterer--frame-{frame}' for frame in range(4)]]),
            'signatures/source/icons.png':(4,1,list(manifest.get('icons',{}))),
            'ui-kit/source/icons.png':(4,3,['kick','bomb','missile','move','heart','mana','potion','guard','bag','quest','wait','skills'])}
        if relative in grids:
            cols,rows,names=grids[relative]
            for i,label in enumerate(names):
                box=[round(i%cols*image.width/cols),round(i//cols*image.height/rows),round((i%cols+1)*image.width/cols),round((i//cols+1)*image.height/rows)]
                root=directory+'--'+label.split('--')[0]
                if '--frame-' in label and not label.endswith('--frame-0'):root=directory+'--'+label
                raw_regions.append(native(root,label,box,'native-'+label))
        if relative=='ui-kit/source/powerful-strike.png':raw_regions.append(native('ui-kit--powerful-strike','Powerful strike',[0,0,image.width,image.height]))
        if relative=='interface/source/frame.png':raw_regions.append(native('interface--ornate-frame','Ornate interface frame',[0,0,image.width,image.height]))
        if raw_regions:return raw_regions
        if '/source/' in relative or name in ('source-atlas','contact-sheet') or directory in ('concepts','menu-concepts','revamp'):
            # Known raw directional source boxes are useful native variants.
            measures=read_json(ASSETS/directory/'source/measurements.json',{})
            if name in measures:
                result=[]
                for row in measures[name]:
                    x,y,x2,y2=row['sourceBox'];root=directory+'--'+name
                    canonical=root if row['pose']=='idle' else root+'--se--'+row['pose']
                    result.append(region(identity+'--'+row['direction']+'--'+row['pose'],name+' native '+row['direction']+' '+row['pose'],[x,y,x2-x,y2-y],False,
                        kind='sprite',category='actor',canonical_asset_id=canonical,object_id=canonical,
                        pose=row['pose'],character_id=root,source_direction=row['direction'],view='native-pose',reusable=False))
                return result
            return []
        if '/' not in relative:
            if name=='contact-sheet':return []
            return [region('legacy--'+name,name.replace('-',' '),[0,0,image.width,image.height],True,
                kind='sprite',category='actor',pose='standing',character_id='legacy--'+name,
                source_direction='front',notes='Original standalone front-facing gameplay sprite, reused without modifying pixels. Other views require inferred geometry.')]
        physical=directory not in ('ui-kit','interface','signatures') and 'portrait' not in name and not (directory=='room-kit' and '/overlays/' in relative and name!='grate')
        kind='sprite' if physical else ('portrait' if 'portrait' in name else 'ui')
        return [region(identity,name.replace('-',' '),[0,0,image.width,image.height],physical,kind=kind)]

    def existing_components(self):
        for asset in self.semantic:self.metadata(asset)

    def build(self):
        outputs=super().build();index=resolve_references(self,json.loads(outputs['reusable/index.json']))
        for row in self.coverage:
            parents=[a for a in index['assets'] if a.get('provenance',{}).get('source_image')==row['source'] and a.get('views',{}).get('applicable')]
            completed={s['object_id'] for s in index['view_sets'] if s.get('complete')}
            row['six_view_object_count']=len({a.get('object_id',a['id']) for a in parents if a['views'].get('complete')})
            row['uncovered_object_ids']=sorted({a.get('object_id',a['id']) for a in parents if not a['views'].get('complete')})
        index['coverage']=self.coverage
        index['statistics']['source_image_count']=len(self.coverage)
        index['statistics']['sources_awaiting_semantic_review']=sum(r['status']=='source-only-awaiting-review' for r in self.coverage)
        outputs['reusable/index.json']=json_bytes(index)
        return outputs


def write_outputs(builder, check, finalize_views=False):
    builder.readonly_views=not finalize_views
    builder.build(); outputs=builder.finalize_outputs(); changed=[]
    from view_review_contract import attach_review
    legacy=builder.pack.resolve() == (ASSETS/'style-packs/pocket-dungeon').resolve()
    index=attach_review(builder.pack,json.loads(outputs['reusable/index.json']),legacy=legacy)
    outputs['reusable/index.json']=json_bytes(index)
    for relative,data in outputs.items():
        path=builder.pack/relative
        if not path.exists() or path.read_bytes()!=data:
            changed.append(relative)
    obsolete=[]
    current_index=json.loads(outputs['reusable/index.json'])
    current_ids={a['id'] for a in current_index['assets']}
    for previous in builder.existing_index.get('assets',[]):
        is_residual=previous.get('provenance',{}).get('method')=='residual'
        is_retired_scene=previous.get('managed_by')=='reusable-scene-extraction-v1' and previous['id'] not in current_ids
        if not (is_residual or is_retired_scene) or previous.get('metadata_path') in outputs:continue
        paths=[previous['image']['path'],previous['metadata_path']]
        prefix='reusable/residuals/' if is_residual else 'reusable/scene-assets/'
        if not all(path.startswith(prefix) for path in paths):raise ValueError('Unsafe obsolete managed output path')
        png=builder.pack/paths[0];sidecar=builder.pack/paths[1]
        if not png.exists() or file_hash(png.read_bytes())!=previous['image']['sha256'] or read_json(sidecar)!=previous:
            raise ValueError('Preserving locally modified obsolete residual: '+previous['id'])
        obsolete.extend(paths)
    if not check:
        for relative in changed:
            path=builder.pack/relative
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(outputs[relative])
        for relative in obsolete:(builder.pack/relative).unlink()
    return {'pack':str(builder.pack.relative_to(ASSETS)),'outputs':len(outputs),'changed':len(changed),
        'obsolete':len(obsolete),'examples':changed[:5]}


def registry():
    rows=[]
    for style in STYLES:
        for kind,base,label in [('style-pack',f'style-packs/{style}',TITLES[style]),('book-tiles',f'book-tiles/{style}',TITLES[style]+' — book locations')]:
            rows.append({'id':kind+'-'+style,'label':label,'index':base+'/reusable/index.json','base':base,'style':style,'kind':kind})
    rows.append({'id':'gameplay','label':'Gameplay, interface and concepts','index':'reusable-gameplay/reusable/index.json','base':'reusable-gameplay','style':'gameplay','kind':'gameplay'})
    return {'schema_version':1,'libraries':rows}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--style',choices=STYLES,action='append')
    p.add_argument('--kind',choices=['styles','books','gameplay','registry','all'],default='all')
    p.add_argument('--check',action='store_true')
    p.add_argument('--finalize-views',action='store_true',help='Enrich worker-owned view sidecars only after all generation workers are frozen')
    args=p.parse_args(); reports=[]
    for style in args.style or STYLES:
        if args.kind in ('all','styles'):
            builder_type=Builder if style=='pocket-dungeon' else StyleBuilder
            reports.append(write_outputs(builder_type(ASSETS/'style-packs'/style),args.check,args.finalize_views))
        if args.kind in ('all','books'):reports.append(write_outputs(BookBuilder(ASSETS,style),args.check,args.finalize_views))
    if args.kind in ('all','gameplay'):reports.append(write_outputs(GameplayBuilder(),args.check,args.finalize_views))
    if args.kind in ('all','registry'):
        from asset_attachment_tags import enrich_document
        path=ASSETS/'reusable-library.json';raw=json_bytes(enrich_document(registry(),'gameplay'));changed=not path.exists() or path.read_bytes()!=raw
        if changed and not args.check:path.write_bytes(raw)
        reports.append({'registry':str(path),'changed':int(changed)})
    print(json.dumps(reports,indent=2));return int(args.check and any(r['changed'] or r.get('obsolete') for r in reports))

if __name__=='__main__':raise SystemExit(main())
