"""Register original animation exports and diagnostic contact sheets without new art.

Contact-card crops are explicitly non-reusable presentation patches. Their actual
semantic objects already exist in the same catalog. Animation frames alias the
corresponding source pose, so normalization never creates new physical identities.
"""
import json
from pathlib import Path


def register_existing_derivatives(builder):
    from build_pocket_reusable import MANAGER, image_bytes
    pack=builder.pack;source_cache={}
    def patch(path,identity,rect,canonical=None):
        if path not in source_cache:
            source_cache.clear();source=builder.open_image(path)
            source_cache[path]=(source,builder.image_info(path,source)['sha256'])
        source,source_hash=source_cache[path];x,y,w,h=rect
        crop=source.crop((x,y,x+w,y+h));raw=image_bytes(crop)
        target=f'reusable/diagnostic-crops/{identity}.png';builder.outputs[target]=raw
        asset={'schema_version':1,'managed_by':MANAGER,'id':identity,'name':identity.replace('--',' '),
            'kind':'reconstruction_patch','category':'diagnostic-presentation','reusable':False,
            'tags':[pack.name,'diagnostic','contact-card','presentation-background'],
            'image':builder.image_info(target,crop,raw),'metadata_path':target[:-4]+'.json',
            'anchor_px':[0,0],'view':'presentation','object_id':canonical or identity,
            'provenance':{'method':'extracted','source_image':path,'source_sha256':source_hash,
                'source_rect':rect,'notes':'Exact presentation-card pixels, including baked background and labels. Reuse the canonical object instead of this diagnostic crop.'},
            'procedural':{'eligible':False,'reason':'Diagnostic presentation card, not an independent game object.'},
            'views':{'applicable':False,'complete':True,'reason':'Diagnostic rendering of an already cataloged object; no separate physical identity.'}}
        if canonical:asset['canonical_asset_id']=canonical
        builder.metadata(asset);return asset

    def contact(path,objects,cell):
        if not (pack/path).exists():return
        source=builder.open_image(path);cw,ch=cell;cols=source.width//cw
        placements=[];stem=path[:-4].replace('/','--')
        for i,obj in enumerate(objects):
            x,y=i%cols*cw,i//cols*ch
            if y>=source.height:raise ValueError('Contact-sheet layout exceeds source: '+path)
            asset=patch(path,'diagnostic--'+stem+f'--card-{i+1:03}',[x,y,min(cw,source.width-x),min(ch,source.height-y)],obj['id'])
            placements.append((asset,x,y))
        builder.map_from_source('diagnostic--'+stem,'Original '+stem+' contact sheet',path,placements,'diagnostic-contact-sheet')

    if pack.parent.name=='style-packs':
        contact('contact-sheet.png',builder.manifest['assets'],(240,250))
        for collection in builder.manifest.get('collections',[]):
            document=json.loads((pack/collection['manifest']).read_text())
            contact(collection['contactSheet'],document['assets'],(240,250))
        for metadata_path in sorted((pack/'animations').glob('*/metadata.json')):
            animation=json.loads(metadata_path.read_text());placements=[]
            for i,(path,parent_id) in enumerate(zip(animation['frames'],animation['componentIds'],strict=True)):
                parent=builder.assets[parent_id];identity='normalized-animation--'+parent_id
                asset={**parent,'id':identity,'name':parent['name']+' normalized animation frame',
                    'image':builder.image_info(path),'metadata_path':str(Path(path).with_suffix('.json')),
                    'object_id':parent_id,'canonical_asset_id':parent_id,'view':'normalized-animation',
                    'pose':parent_id,'anchor_px':[animation['anchor']['x'],animation['anchor']['y']],
                    'provenance':{'method':'existing','source_image':parent['image']['path'],
                        'source_sha256':parent['image']['sha256'],'normalization':animation,
                        'notes':'Original normalized animation PNG reused unchanged. Principal views attach to its original source pose.'},
                    'views':{'applicable':False,'complete':True,'reason':'Normalized alias of the same source pose; see canonical_asset_id.'}}
                builder.metadata(asset);placements.append((asset,i*animation['frameWidth'],0))
            builder.map_from_source('animation--'+animation['id'],animation['label']+' original strip',animation['spriteSheet'],placements,'animation-strip')
    elif pack.parent.name=='book-tiles':
        for manifest in sorted(pack.glob('*/manifest.json')):
            kit=json.loads(manifest.read_text())
            contact(manifest.parent.name+'/contact-sheet.png',kit['assets'],(128,160))
    elif pack.name=='reusable-gameplay':
        path='reusable/sources/contact-sheet.png'
        if path in builder.outputs:
            # Original generator ordering is encoded in the contact sheet pixels;
            # no invented mapping to an arbitrary sorted character list.
            source=builder.open_image(path);placements=[]
            for i in range(source.width//128*(source.height//128)):
                x,y=i%(source.width//128)*128,i//(source.width//128)*128
                asset=patch(path,f'diagnostic--legacy-contact--card-{i+1:03}',[x,y,128,128])
                placements.append((asset,x,y))
            # Replace the earlier residual-only map for this same original file.
            builder.maps=[m for m in builder.maps if m['source']!=path]
            builder.map_from_source('atlas-contact-sheet','Original legacy sprite contact sheet',path,placements,'diagnostic-contact-sheet')
