#!/usr/bin/env python3
"""Build/check a standalone image-generated drainage expansion; never alters frozen libraries.
Input source/recipe.json lists exports: shape, view, source, crop [x,y,w,h].
All paths are expansion-relative. Recorded crops, alpha cleanup and normalization replay exactly; no art synthesis.
"""
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from asset_attachment_tags import enrich_document
from package_pocket_reusable import write_zip

ROOT = Path(__file__).resolve().parents[1] / 'dungeon-crawler-tactics/Web/wwwroot/assets'
DEFAULT = ROOT / 'expansions/drainage-channels-v1'
VIEWS = ('isometric', 'front', 'rear', 'left', 'right', 'top', 'bottom')
EDGES = {'straight': ['N', 'S'], 'corner': ['N', 'E'], 'tee': ['N', 'E', 'W']}
DIRECTIONS = ['N', 'E', 'S', 'W']
DELTA = {'N': (0,-1), 'E': (1,0), 'S': (0,1), 'W': (-1,0)}
SUPPORT = 'style-pack-pocket-dungeon::stone-floor'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())
def safe(root, path):
    result = (root / path).resolve()
    if not result.is_relative_to(root.resolve()): raise ValueError('Path escapes expansion')
    return result

def encoded(doc): return json.dumps(doc, indent=2, ensure_ascii=False) + '\n'
def document(doc): return enrich_document(doc, 'gameplay')
def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded(document(doc)))

def rotate(edges, degrees):
    if degrees not in (0,90,180,270): raise ValueError('Only clockwise quarter turns are supported')
    return sorted((DIRECTIONS[(DIRECTIONS.index(edge)+degrees//90)%4] for edge in edges), key=DIRECTIONS.index)

def validate_connections(recipe):
    cells = {}
    for p in recipe['placements']:
        key = tuple(p['cell'])
        if key in cells: raise ValueError('Overlapping drainage cells')
        cells[key] = rotate(EDGES[p['shape']], p['rotation_deg'])
    for (x,y), edges in cells.items():
        for edge in edges:
            dx,dy = DELTA[edge]; neighbor = (x+dx,y+dy)
            if neighbor in cells and DIRECTIONS[(DIRECTIONS.index(edge)+2)%4] not in cells[neighbor]:
                raise ValueError('Nonreciprocal channel connection')
    if 'open_boundaries' in recipe:
        actual = {(x,y,edge) for (x,y),edges in cells.items() for edge in edges if (x+DELTA[edge][0],y+DELTA[edge][1]) not in cells}
        declared = {(p['cell'][0],p['cell'][1],p['edge']) for p in recipe['open_boundaries']}
        if actual != declared: raise ValueError('Open channel boundaries differ from declaration')
    return cells

def clean_alpha(image, threshold=16, max_component=4):
    """Remove only alpha fringe and tiny secondary 8-connected components."""
    image=image.copy();alpha=image.getchannel('A');values=list(alpha.tobytes());width,height=image.size
    low=sum(0<v<threshold for v in values)
    values=[v if v>=threshold else 0 for v in values]
    remaining={i for i,v in enumerate(values) if v};components=[]
    while remaining:
        start=min(remaining);remaining.remove(start);stack=[start];component=[]
        while stack:
            current=stack.pop();component.append(current);x,y=current%width,current//width
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    nx,ny=x+dx,y+dy
                    if 0<=nx<width and 0<=ny<height:
                        index=ny*width+nx
                        if index in remaining:remaining.remove(index);stack.append(index)
        components.append(component)
    primary=max(components,key=len) if components else []
    removed=[c for c in components if c is not primary and len(c)<=max_component]
    for component in removed:
        for index in component:values[index]=0
    alpha.putdata(values);image.putalpha(alpha)
    return image,{'alpha_below_threshold_pixels_removed':low,'secondary_components_removed':len(removed),'secondary_component_pixels_removed':sum(map(len,removed)),'retained_component_count':len(components)-len(removed)}

def extract(root, entry):
    source = safe(root, entry['source'])
    x,y,w,h = entry['crop']
    with Image.open(source) as raw:
        if min(x,y)<0 or min(w,h)<=0 or x+w>raw.width or y+h>raw.height: raise ValueError('Crop outside source')
        image = raw.convert('RGBA').crop((x,y,x+w,y+h))
    norm = entry.get('normalization')
    stats={'alpha_below_threshold_pixels_removed':0,'secondary_components_removed':0,'secondary_component_pixels_removed':0,'retained_component_count':None}
    if not norm: return image, [0,0,w,h],stats
    if 'alpha_threshold' in norm:
        image,stats=clean_alpha(image,norm['alpha_threshold'],norm['remove_secondary_components_max_px'])
    canvas_w,canvas_h = norm['canvas_px']
    width = norm['target_width_px']
    height = norm.get('target_height_px',max(1, round(h * width / w)))
    if width>canvas_w or height>canvas_h: raise ValueError('Normalized view exceeds canvas')
    resized = image.resize((width,height), Image.Resampling.NEAREST)
    output = Image.new('RGBA',(canvas_w,canvas_h),(0,0,0,0))
    left,top = (canvas_w-width)//2,(canvas_h-height)//2
    output.paste(resized,(left,top))
    return output, [left,top,width,height],stats

def render(root, recipe):
    validate_connections(recipe)
    size = recipe['cell_size_px']
    width,height = recipe['canvas_px']
    background=recipe['background_rgba']
    if not isinstance(background,list) or len(background)!=4 or any(type(v) is not int or not 0<=v<=255 for v in background): raise ValueError('Background must contain four RGBA bytes')
    if not isinstance(size,int) or size<=0 or min(width,height)<=0: raise ValueError('Invalid map dimensions')
    for p in recipe['placements']:
        x,y=p['cell']
        if 'asset_id' in p and p['asset_id']!=f"drainage-{p['shape']}-top": raise ValueError('Placement asset reference mismatch')
        if not all(isinstance(v,int) for v in (x,y)) or min(x,y)<0 or (x+1)*size>width or (y+1)*size>height: raise ValueError('Placement outside map canvas')
    image = Image.new('RGBA', tuple(recipe['canvas_px']), tuple(background))
    for p in recipe['placements']:
        with Image.open(safe(root, f"tiles/{p['shape']}/top.png")) as src:
            tile = src.convert('RGBA')
            metadata = root / f"tiles/{p['shape']}/top.json"
            if metadata.exists():
                x,y,w,h = read(metadata).get('image',{}).get('content_box_px',[0,0,tile.width,tile.height])
                tile = tile.crop((x,y,x+w,y+h))
            tile = tile.resize((size,size), Image.Resampling.NEAREST).rotate(-p['rotation_deg'])
            image.alpha_composite(tile, (p['cell'][0]*size,p['cell'][1]*size))
    return image

def alignment_report(root, recipe):
    """Bounded dark-teal sampling supports visual review; it cannot prove pixel seams."""
    size=recipe['cell_size_px']; tiles={}; ports={}
    for p in recipe['placements']:
        meta=read(root/f"tiles/{p['shape']}/top.json")
        with Image.open(root/meta['image']['path']) as raw:
            x,y,w,h=meta['image']['content_box_px']
            tile=raw.convert('RGBA').crop((x,y,x+w,y+h)).resize((size,size),Image.Resampling.NEAREST).rotate(-p['rotation_deg'])
        cell=tuple(p['cell']);tiles[cell]=p
        for edge in rotate(EDGES[p['shape']],p['rotation_deg']):
            positions=[]
            inset=max(1,round(size*0.05))
            for i in range(round(size*.15),round(size*.85)):
                point={'N':(i,inset),'S':(i,size-1-inset),'E':(size-1-inset,i),'W':(inset,i)}[edge]
                r,g,b,a=tile.getpixel(point)
                if a>=128 and r<65 and g<120 and b<135:positions.append(i)
            runs=[]
            for i in positions:
                if not runs or i>runs[-1][-1]+1:runs.append([i,i])
                else:runs[-1][1]=i
            span=max(runs,key=lambda v:v[1]-v[0]) if runs else None
            ports[(cell,edge)]=span
    joins=[]
    for (cell,edge),span in sorted(ports.items()):
        if edge not in ('E','S'):continue
        dx,dy=DELTA[edge];other=(cell[0]+dx,cell[1]+dy)
        if other not in tiles:continue
        opposite=DIRECTIONS[(DIRECTIONS.index(edge)+2)%4];b=ports.get((other,opposite))
        overlap=max(0,min(span[1],b[1])-max(span[0],b[0])+1) if span and b else 0
        minimum=min(span[1]-span[0]+1,b[1]-b[0]+1) if span and b else 0
        joins.append({'from_cell':list(cell),'edge':edge,'to_cell':list(other),'from_dark_span_px':span,'to_dark_span_px':b,'overlap_px':overlap,'overlap_fraction_of_narrower':round(overlap/minimum,4) if minimum else 0,'center_offset_px':round(abs(sum(span)/2-sum(b)/2),2) if span and b else None})
    return {'schema_version':1,'status':'measurement-complete','map_sha256':sha(root/'maps/example.png'),'method':'Top tiles rendered at128px; largest dark-teal run within central70percent sampled5percent inward from each edge. RGB r<65 g<120 b<135 alpha>=128. Heuristic does not establish channels at the exact outer pixel or remove dark outlines.','joins':joins,'pixel_seamless':False,'visible_grid_seams':'Dark tile outlines and local width/offset changes remain visible; this is a connection study, not a seamless texture claim.'}

def contact_sheet(root, shape):
    contact=Image.new('RGB',(1536,1152),'white');draw=ImageDraw.Draw(contact)
    for idx,view in enumerate(VIEWS):
        with Image.open(root/f'tiles/{shape}/{view}.png') as raw:
            thumb=raw.convert('RGBA').resize((360,360),Image.Resampling.NEAREST)
        x=(idx%3)*512;y=(idx//3)*384
        bg=Image.new('RGBA',(360,360));checker=ImageDraw.Draw(bg)
        for yy in range(0,360,15):
            for xx in range(0,360,15):
                checker.rectangle((xx,yy,xx+14,yy+14),fill=(210,210,210,255) if (xx//15+yy//15)%2 else (245,245,245,255))
        bg.alpha_composite(thumb);contact.paste(bg.convert('RGB'),(x,y+24));draw.text((x+8,y+5),view,fill='black')
    return contact

def validate_review_evidence(root, decisions):
    expected=decisions.get('map_review',{}).get('alignment_report_sha256')
    if not expected or expected!=sha(root/'maps/alignment-report.json'): raise ValueError('Review alignment report hash mismatch')
    for entry in decisions.get('source_evidence',[]):
        for path_key,hash_key in (('source_path','source_sha256'),('contact_review_path','contact_sha256')):
            if path_key in entry or hash_key in entry:
                if not entry.get(path_key) or not entry.get(hash_key) or sha(safe(root,entry[path_key]))!=entry[hash_key]: raise ValueError(f'Review evidence hash mismatch: {path_key}')

def build_inplace(root):
    recipe = read(root/'source/recipe.json')
    if not (root/'source/prompt.txt').is_file(): raise ValueError('Source prompt must be retained')
    keys = [(e['shape'],e['view']) for e in recipe['exports']]
    if sorted(keys) != sorted((s,v) for s in EDGES for v in VIEWS): raise ValueError('Exactly 21 unique exports required')
    tiles = {t['id']:t for t in read(ROOT/'attachment-rules.json')['tiles']}
    if SUPPORT not in tiles or 'surface:floor' not in tiles[SUPPORT]['tags']: raise ValueError('Missing existing support tile')
    assets=[]
    for entry in recipe['exports']:
        shape,view=entry['shape'],entry['view']; source=safe(root,entry['source'])
        prompt = safe(root,entry.get('prompt','source/prompt.txt'))
        if not prompt.is_file(): raise ValueError('Per-source prompt is missing')
        x,y,w,h=entry['crop']
        image,content_box,cleanup_stats=extract(root,entry)
        path=f'tiles/{shape}/{view}.png'; dest=safe(root,path); dest.parent.mkdir(parents=True,exist_ok=True);image.save(dest)
        asset={'schema_version':1,'id':f'drainage-{shape}-{view}','name':f'Shallow stone drainage channel {shape} {view}', 'kind':'prop','category':'terrain','attachment_namespace':'gameplay','tags':['drainage','stone','dungeon','pocket-dungeon','expansion','view:'+view,'visual_style:pocket-dungeon','art-style:pocket-dungeon'], 'image':{'path':path,'width':image.width,'height':image.height,'content_box_px':content_box,'sha256':sha(dest)},'metadata_path':path[:-4]+'.json','view':view,'object_id':f'drainage-{shape}','provenance':{'method':'imagegen-source-crop','source_image':entry['source'],'source_sha256':sha(source),'crop_px':[x,y,w,h],'recipe':'source/recipe.json','prompt':entry.get('prompt','source/prompt.txt'),'prompt_sha256':sha(prompt),'alpha_cleanup_counts':cleanup_stats,'normalization':entry.get('normalization',{'method':'none'})},'placement':{'footprint_cells':[1,1],'anchor_normalized':[0.5,0.5],'anchor_status':'authored-layout-center; visual-contact-review-pending','support_tile_ids':[SUPPORT],'compatibility_authority':'editorial surface:floor; geometry pending review','connection_edges':EDGES[shape],'connection_coordinate_system':'top view: north up, east right','rotation_degrees_clockwise':[0,90,180,270],'rotation_rule':'logical edges rotate clockwise; raster rotation permitted for top view only','visual_alignment_status':'pending-review'}}
        asset=document(asset);write(root/asset['metadata_path'],asset);assets.append(asset)
    catalog={'schema_version':1,'id':'drainage-channels-v1','title':'Pocket Dungeon drainage channels — expansion candidate','status':'pending-independent-review','frozen_release_library_count':7,'assets':assets,'maps':[{'id':'drainage-example','file':'maps/example.json','preview':'maps/example.png'}], 'review':'review.json','source_recipe':'source/recipe.json','download':'drainage-channels-v1.zip'}
    write(root/'catalog.json',catalog)
    example={'schema_version':1,'id':'drainage-example','kind':'procedural-example','canvas_px':[640,640],'background_rgba':[35,39,43,255],'cell_size_px':128,'seed':0,'generation':'fixed deterministic placement fixture; replay from JSON','claims':{'logical_connectivity':'validated reciprocal adjacent edges','pixel_seams':'pending independent review','runtime_collision':'not defined'},'placements':[{'shape':'corner','cell':[1,1],'rotation_deg':90},{'shape':'straight','cell':[2,1],'rotation_deg':90},{'shape':'corner','cell':[3,1],'rotation_deg':180},{'shape':'straight','cell':[1,2],'rotation_deg':0},{'shape':'tee','cell':[3,2],'rotation_deg':90},{'shape':'corner','cell':[1,3],'rotation_deg':0},{'shape':'straight','cell':[2,3],'rotation_deg':90},{'shape':'corner','cell':[3,3],'rotation_deg':270}], 'open_boundaries':[{'cell':[3,2],'edge':'E'}]}
    for placement in example['placements']:placement['asset_id']=f"drainage-{placement['shape']}-top"
    write(root/'maps/example.json',example);render(root,example).save(root/'maps/example.png')
    write(root/'maps/alignment-report.json',alignment_report(root,example))
    for shape in EDGES:
        preview=root/f'previews/{shape}-contact.png';preview.parent.mkdir(exist_ok=True)
        contact_sheet(root,shape).save(preview)
        write(preview.with_suffix('.json'),{'schema_version':1,'object_id':f'drainage-{shape}','image_path':preview.relative_to(root).as_posix(),'sha256':sha(preview),'derivation':'Deterministic seven exported views resized nearest onto checkerboard; labels follow VIEWS order in tools/drainage_expansion.py','review_status':'pending'})
    write(root/'review.json',{'schema_version':1,'status':'pending','scope':['six orthographic views per object','isometric consistency','logical connections','rendered channel alignment'], 'records':[{'asset_id':a['id'],'sha256':a['image']['sha256'],'status':'pending'} for a in assets], 'map_sha256':sha(root/'maps/example.png'),'approval':None})
    decision_path=root/'source/review-decisions.json'
    if decision_path.exists():
        decisions=read(decision_path)
        if decisions.get('root_approval',{}).get('status')!='approved-qualified': raise ValueError('Review decisions lack explicit root approval')
        records=decisions.get('records',[])
        by_id={r['asset_id']:r for r in records}
        if len(by_id)!=21 or len(records)!=21 or set(by_id)!={a['id'] for a in assets}: raise ValueError('Review decision coverage mismatch')
        for asset in assets:
            record=by_id[asset['id']]
            if record['sha256']!=asset['image']['sha256'] or record.get('status') not in ('qualified-pass','pass'): raise ValueError('Stale or unaccepted review decision hash/status')
        if decisions.get('map_sha256')!=sha(root/'maps/example.png'): raise ValueError('Stale review decision map hash')
        validate_review_evidence(root,decisions)
        for asset in assets:
            asset['review_status']='qualified-reviewed'
            asset['placement']['visual_alignment_status']='qualified-reviewed-with-grid-seams-and-port-offsets'
            asset['placement']['anchor_status']='authored-layout-center; qualified illustrative contact review'
            asset['placement']['compatibility_authority']='editorial surface:floor; qualified illustrative geometry review; no runtime collision claim'
            write(root/asset['metadata_path'],asset)
        example['claims']['pixel_seams']='qualified visual review: visible grid seams and modest port offsets retained'
        write(root/'maps/example.json',example)
        for preview in (root/'previews').glob('*.json'):
            metadata=read(preview);metadata['review_status']='qualified-reviewed';write(preview,metadata)
        catalog['status']='qualified-reviewed'
        catalog['limitations']=['Visible dark grid seams and local channel width differences','Modest channel port offsets: up to7pixels at128pixel tile size','Illustrative orthographic views; not a CAD model','Only top-view raster rotation is supported']
        write(root/'catalog.json',catalog)
        write(root/'review.json',decisions)
    # Ensure source recipe also obeys canonical metadata-document enrichment.
    write(root/'source/recipe.json',recipe)
    result=check(root)
    members={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file() and p.suffix!='.zip'}
    result['archive_bytes']=write_zip(root/'drainage-channels-v1.zip',members,95*1024*1024)
    return result

def build(root):
    # Stage the entire result so stale decisions fail without replacing prior outputs.
    root=Path(root).resolve()
    with tempfile.TemporaryDirectory(prefix='drainage-build-') as temporary:
        staged=Path(temporary)/'expansion'
        shutil.copytree(root,staged,ignore=shutil.ignore_patterns('*.zip'))
        result=build_inplace(staged)
        for path in sorted(staged.rglob('*')):
            relative=path.relative_to(staged)
            if not path.is_file() or relative.parts[0]=='source':continue
            destination=root/relative;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,destination)
        return result

def check(root):
    catalog=read(root/'catalog.json'); assets=catalog['assets']
    if len(assets)!=21: raise ValueError('21 view assets required')
    for path in root.rglob('*.json'):
        doc=read(path)
        if encoded(document(doc))!=path.read_text(): raise ValueError(f'Stale canonical tags: {path}')
    tiles = {t['id'] for t in read(ROOT/'attachment-rules.json')['tiles']}
    review = read(root/'review.json')
    if catalog['status']=='qualified-reviewed':
        if review.get('root_approval',{}).get('status')!='approved-qualified' or read(root/'source/review-decisions.json')!=review: raise ValueError('Approved review differs from immutable decisions')
        validate_review_evidence(root,review)
        if any(a.get('review_status')!='qualified-reviewed' for a in assets): raise ValueError('Inconsistent approved asset status')
    records = {r['asset_id']:r for r in review['records']}
    if set(records) != {a['id'] for a in assets}: raise ValueError('Review coverage mismatch')
    for asset in assets:
        if not set(asset['placement']['support_tile_ids']) <= tiles: raise ValueError('Unknown support tile reference')
        if records[asset['id']]['sha256'] != asset['image']['sha256']: raise ValueError('Stale review hash')
        if read(root/asset['metadata_path'])!=asset: raise ValueError('Sidecar differs from catalog')
        if sha(root/asset['image']['path'])!=asset['image']['sha256']: raise ValueError('PNG hash mismatch')
        p=asset['provenance'];x,y,w,h=p['crop_px']
        if sha(safe(root,p['prompt']))!=p['prompt_sha256']: raise ValueError('Prompt hash mismatch')
        if sha(root/p['source_image'])!=p['source_sha256']: raise ValueError('Source hash mismatch')
        entry={'source':p['source_image'],'crop':p['crop_px']}
        if p['normalization'].get('method')!='none': entry['normalization']=p['normalization']
        replay, box, cleanup_stats = extract(root,entry)
        if cleanup_stats!=p['alpha_cleanup_counts']: raise ValueError('Alpha cleanup count mismatch')
        with Image.open(root/asset['image']['path']) as dst:
            if replay.size!=dst.size or replay.tobytes()!=dst.convert('RGBA').tobytes(): raise ValueError('Crop replay mismatch')
        if box!=asset['image']['content_box_px']: raise ValueError('Normalization bounds mismatch')
    if sha(root/'maps/example.png')!=review['map_sha256']: raise ValueError('Map review hash mismatch')
    recipe=read(root/'maps/example.json')
    with Image.open(root/'maps/example.png') as expected:
        if render(root,recipe).tobytes()!=expected.convert('RGBA').tobytes(): raise ValueError('Map replay mismatch')
    return {'assets':len(assets),'objects':3,'status':catalog['status'],'map_replay':'exact RGBA'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--check',action='store_true');p.add_argument('--render',type=Path);a=p.parse_args()
    if a.render: render(a.root,read(a.root/'maps/example.json')).save(a.render)
    else: print(json.dumps(check(a.root) if a.check else build(a.root),sort_keys=True))
if __name__=='__main__':main()
