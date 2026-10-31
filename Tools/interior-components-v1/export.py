"""Normalize approved generated component masters; never source retail pixels."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import argparse,hashlib,json,math,tempfile

ROOT=Path(__file__).resolve().parents[2]
CFG=Path(__file__).with_name('components.json')
RAW=ROOT/'ArtSource/InteriorComponentsV1'
PROD=ROOT/'Assets/Art/Production/InteriorComponentsV1'
REVIEW=ROOT/'Review/interior-components-v1'
MANIFEST=PROD/'manifest.json'
ALLOW_DERIVED_REFRESH=False

def sha(data):return hashlib.sha256(data).hexdigest()
def read_json(path,default=None):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def save_new(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=data:raise ValueError('Preserving existing differing file; use a versioned source/output ID: '+str(path))
    if not path.exists():path.write_bytes(data)

def save_derived(path,data):
    if ALLOW_DERIVED_REFRESH:
        if not path.resolve().is_relative_to(PROD.resolve()):raise ValueError('Derived output escapes production root')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    else:save_new(path,data)

def save_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def safe_path(root,relative):
    target=(root/relative).resolve()
    if not target.is_relative_to(root.resolve()):raise ValueError('Path escapes intended folder: '+str(relative))
    return target

def png_bytes(im):
    import io
    stream=io.BytesIO();im.save(stream,format='PNG');return stream.getvalue()

def cell_rect(im,component):
    if 'crop' in component:
        x,y,w,h=component['crop']
    elif 'grid' in component:
        cols,rows=component['grid'];col,row=component['cell']
        if im.width%cols or im.height%rows:raise ValueError('Master dimensions must divide exactly into the declared regular grid')
        if not(0<=col<cols and 0<=row<rows):raise ValueError('Cell outside grid')
        w,h=im.width//cols,im.height//rows;x,y=col*w,row*h
    else:x,y,w,h=0,0,im.width,im.height
    if min(x,y)<0 or min(w,h)<=0 or x+w>im.width or y+h>im.height:raise ValueError('Invalid master crop')
    return x,y,w,h

def normalize(im,component):
    x,y,w,h=cell_rect(im,component);source=im.convert('RGBA').crop((x,y,x+w,y+h));size=tuple(component['size'])
    if len(size)!=2 or min(size)<=0:raise ValueError('Invalid output dimensions')
    mode=component['alpha'];trim=(0,0,w,h);padding=(0,0);scale=None
    if mode=='cutout':
        if source.getchannel('A').getextrema()[0]>=128:raise ValueError('Cutout source lacks transparent gutters/background')
        alpha=source.getchannel('A').point(lambda value:255 if value>=128 else 0)
        trim=alpha.getbbox()
        if trim is None:raise ValueError('Cutout has no alpha>=128 pixels')
        source.putalpha(alpha);source=source.crop(trim)
        scale=min(size[0]/source.width,size[1]/source.height)
        target_size=size if component.get('fit')=='stretch' else (max(1,min(size[0],round(source.width*scale))),max(1,min(size[1],round(source.height*scale))))
        source=source.resize(target_size,Image.Resampling.NEAREST)
        padding=((size[0]-source.width)//2,size[1]-source.height)
        output=Image.new('RGBA',size,(0,0,0,0));output.alpha_composite(source,padding)
    elif mode=='opaque':
        if source.getchannel('A').getextrema()!=(255,255):raise ValueError('Opaque component contains transparency; declare a tighter crop or a cutout')
        output=source.resize(size,Image.Resampling.NEAREST)
    else:raise ValueError('Unsupported alpha mode '+str(mode))
    return output,{'fit':component.get('fit','contain' if mode=='cutout' else 'stretch'),'cellRect':[x,y,w,h],'trimRect':list(trim),'padding':list(padding),'scale':scale,'anchor':component.get('anchor',[size[0]//2,size[1]]),'alpha':mode,'size':list(size),'repeat':component.get('repeat','none'),'nineSlice':component.get('nineSlice')}

def import_master(source_id,path):
    if not source_id or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in source_id):raise ValueError('Use a lowercase versioned source ID')
    source=Path(path);data=source.read_bytes();im=Image.open(source)
    if im.format!='PNG':raise ValueError('Preserve generated PNG master bytes; supplied file is not PNG')
    target=RAW/'sources'/(source_id+'.png');save_new(target,data)
    sources=read_json(RAW/'source-manifest.json',{'sources':{}})
    record={'path':target.relative_to(ROOT).as_posix(),'sha256':sha(data),'size':list(im.size),'originPath':str(source.resolve()),'kind':'AI-generated master; generation details supplied by parent agent'}
    prior=sources['sources'].get(source_id)
    if prior and prior['sha256']!=record['sha256']:raise ValueError('Source ID is frozen; select a new versioned source ID')
    sources['sources'][source_id]=prior or record;save_json(RAW/'source-manifest.json',sources)
    print('Preserved source',source_id,record['size'],record['sha256'])

def export(source_filter=None):
    cfg=read_json(CFG);sources=read_json(RAW/'source-manifest.json',{'sources':{}})['sources']
    selected=[c for c in cfg['components'] if source_filter is None or c['source']==source_filter]
    if not selected:raise ValueError('No configured components for requested source')
    existing=read_json(MANIFEST,{'version':1,'status':'asset-only; not integrated','components':{},'references':[]})
    for component in selected:
        source_id=component['source']
        if source_id not in sources:raise ValueError('Master not imported: '+source_id)
        info=sources[source_id];path=safe_path(ROOT,info['path']);data=path.read_bytes()
        if sha(data)!=info['sha256']:raise ValueError('Source hash drift: '+source_id)
        output,meta=normalize(Image.open(path),component);dest=safe_path(PROD,component['output']);result=png_bytes(output);save_new(dest,result)
        meta.update({'id':component['id'],'file':dest.relative_to(ROOT).as_posix(),'sha256':sha(result),'source':info,'referenceScope':component.get('referenceScope','Reference-informed generated art, not screenshot extraction'),'collision':'none; integration deferred','kind':component.get('kind','component')})
        if meta['repeat'] in ('horizontal','both'):
            cols,rows=(6,1) if meta['repeat']=='horizontal' else (6,6)
            proof=Image.new('RGBA',(output.width*cols,output.height*rows))
            for row in range(rows):
                for col in range(cols):proof.alpha_composite(output,(col*output.width,row*output.height))
            proof_path=REVIEW/'repeats'/(component['id']+'-native.png');proof_path.parent.mkdir(parents=True,exist_ok=True);proof_path.write_bytes(png_bytes(proof))
            (REVIEW/'repeats'/(component['id']+'-4x.png')).write_bytes(png_bytes(proof.resize((proof.width*4,proof.height*4),Image.Resampling.NEAREST)))
            meta['repeatProof']=proof_path.relative_to(ROOT).as_posix()
        if component.get('nineSlice'):export_ui_layers(output,component,meta)
        existing['components'][component['id']]=meta
        print('Exported',component['id'],meta['size'],meta['alpha'])
    existing['references']=[]
    for ref in cfg.get('references',[]):
        path=safe_path(ROOT,ref['path']);data=path.read_bytes()
        if sha(data)!=ref['sha256']:raise ValueError('Approved cursor reference changed: '+ref['path'])
        existing['references'].append(ref)
    existing['configuredCount']=len(cfg['components']);existing['exportedCount']=len(existing['components'])
    existing['pending']=[c['id'] for c in cfg['components'] if c['id'] not in existing['components']]
    save_json(MANIFEST,existing);make_review(existing)
    print('Manifest:',existing['exportedCount'],'exported;',len(existing['pending']),'pending. No game integration.')

def make_review(manifest):
    components=list(manifest['components'].values());cols=4;cw=220;ch=202;rows=max(1,math.ceil(len(components)/cols))
    sheet=Image.new('RGB',(cols*cw,72+rows*ch),(20,26,34));d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13);title=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',21)
    d.text((14,12),'InteriorComponentsV1 / generated assets only',font=title,fill='#f1dfad');d.text((14,42),'No Unity binding, runtime proof, or retail sprite extraction.',font=font,fill='#cbd5e1')
    for i,item in enumerate(components):
        im=Image.open(ROOT/item['file']).convert('RGBA');x=(i%cols)*cw;y=72+(i//cols)*ch
        for cy in range(8,152,8):
            for cx in range(8,cw-8,8):d.rectangle((x+cx,y+cy,x+cx+7,y+cy+7),fill=(54,60,72) if (cx+cy)//8%2 else (38,44,55))
        factor=max(1,min(3,144//im.height,200//im.width));preview=im.resize((im.width*factor,im.height*factor),Image.Resampling.NEAREST);sheet.paste(preview,(x+(cw-preview.width)//2,y+8+144-preview.height),preview)
        d.text((x+10,y+159),item['id'],font=font,fill='#f1dfad');d.text((x+10,y+180),str(item['size'])+' '+item['alpha'],font=font,fill='#cbd5e1')
    REVIEW.mkdir(parents=True,exist_ok=True);(REVIEW/'contact-sheet.png').write_bytes(png_bytes(sheet))
    cards=''.join(f'<article><h2>{item["id"]}</h2><img src="../../{item["file"]}"><p>{item["size"]} / anchor {item["anchor"]} / {item["alpha"]}</p><code>{item["sha256"]}</code></article>' for item in components)
    (REVIEW/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>InteriorComponentsV1</title><style>body{background:#141a22;color:#e2e8f0;font:16px system-ui;margin:32px}main{display:grid;grid-template-columns:repeat(4,minmax(180px,1fr));gap:16px}article{padding:16px;border:1px solid #526174}img{image-rendering:pixelated;max-width:100%;min-height:128px;object-fit:contain}code{font-size:10px;overflow-wrap:anywhere}</style><h1>InteriorComponentsV1</h1><p>Generated component assets; integration deferred. Existing cursor option 10 is referenced only.</p><p>Exported '+str(len(components))+' / configured '+str(manifest['configuredCount'])+'</p><main>'+cards+'</main>',encoding='utf-8')

    gallery=REVIEW/'index.html';html=gallery.read_text(encoding='utf-8')
    extra='<section><h2>Layer construction and proofs</h2><p><a href="panel-nine-slice-proofs.png">Three-size UI proof</a> | <a href="rug-nine-slice-proof.png">Rug border proof</a> | <a href="../../Docs/InteriorComponentsV1/README.md">Contracts and caveats</a></p>'
    for item in components:
        if 'layers' not in item:continue
        links=' | '.join(f'<a href="../../{part["file"]}">{name}</a>' for name,part in item['layers'].items())
        extra+=f'<h3>{item["id"]}</h3><p>{links} | margins {item["nineSlice"]}; mode {item["sliceMode"]}</p>'
    gallery.write_text(html+extra+'</section>',encoding='utf-8')


def sliced_panel(im,size,margins,mode="stretch"):
    left,top,right,bottom=margins;w,h=im.size;tw,th=size
    if tw<left+right or th<top+bottom:raise ValueError('Panel too small for fixed border')
    sx=[0,left,w-right,w];sy=[0,top,h-bottom,h]
    dx=[0,left,tw-right,tw];dy=[0,top,th-bottom,th]
    result=Image.new('RGBA',size,(0,0,0,0))
    for row in range(3):
        for col in range(3):
            part=im.crop((sx[col],sy[row],sx[col+1],sy[row+1]))
            target=(dx[col+1]-dx[col],dy[row+1]-dy[row])
            if mode=='tile' and (row==1 or col==1):
                repeated=Image.new('RGBA',target,(0,0,0,0))
                for py in range(0,target[1],part.height):
                    for px in range(0,target[0],part.width):
                        clipped=part.crop((0,0,min(part.width,target[0]-px),min(part.height,target[1]-py)));repeated.alpha_composite(clipped,(px,py))
                part=repeated
            else:part=part.resize(target,Image.Resampling.NEAREST)
            result.alpha_composite(part,(dx[col],dy[row]))
    return result

def export_ui_layers(im,component,meta):
    margins=component['nineSlice'];left,top,right,bottom=margins;w,h=im.size
    if min(margins)<=0 or left+right>=w or top+bottom>=h:raise ValueError('Invalid nine-slice borders')
    mask=Image.new('L',im.size,0);ImageDraw.Draw(mask).rectangle((left,top,w-right-1,h-bottom-1),fill=255)
    fill=im.copy();fill.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
    frame=im.copy();frame.putalpha(ImageChops.multiply(im.getchannel('A'),ImageChops.invert(mask)))
    stem=Path(component['output']).with_suffix('');meta['layers']={};meta['sliceMode']='tile' if component.get('kind')=='rug' else 'stretch'
    layer_names=('border','field') if component.get('kind')=='rug' else ('frame','fill')
    for name,layer in zip(layer_names,[frame,fill]):
        path=PROD/str(stem.parent)/(stem.name+'-'+name+'.png');data=png_bytes(layer);save_derived(path,data)
        meta['layers'][name]={'file':path.relative_to(ROOT).as_posix(),'sha256':sha(data),'size':list(layer.size)}
    if Image.alpha_composite(frame,fill).tobytes()!=im.tobytes():raise ValueError('UI layers fail exact reconstruction')
    xs=[0,left,w-right,w];ys=[0,top,h-bottom,h];meta['slices']={}
    for row,names in enumerate([['nw','n','ne'],['w','center','e'],['sw','s','se']]):
        for col,name in enumerate(names):
            part=im.crop((xs[col],ys[row],xs[col+1],ys[row+1]));path=PROD/str(stem.parent)/(stem.name+'-'+name+'.png');data=png_bytes(part);save_derived(path,data)
            meta['slices'][name]={'file':path.relative_to(ROOT).as_posix(),'sha256':sha(data),'size':list(part.size)}
    if component['id']=='dialogue-panel':
        sizes=[(192,96),(320,128),(480,200)];proof=Image.new('RGBA',(512,600),(25,31,43,255));draw=ImageDraw.Draw(proof);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14);y=12
        for size in sizes:
            draw.text((12,y),str(size)+' / corners fixed at '+str(margins),font=font,fill='#f2e0b0');y+=24;proof.alpha_composite(sliced_panel(im,size,margins),(12,y));y+=size[1]+18
        path=REVIEW/'panel-nine-slice-proofs.png';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(png_bytes(proof))

def verify():
    manifest=read_json(MANIFEST)
    if not manifest:raise ValueError('No exported manifest')
    for item in manifest['components'].values():
        data=(ROOT/item['file']).read_bytes();assert sha(data)==item['sha256'],'Output hash drift'
        source=(ROOT/item['source']['path']).read_bytes();assert sha(source)==item['source']['sha256'],'Source hash drift'
        im=Image.open(ROOT/item['file']).convert('RGBA');assert list(im.size)==item['size'],'Wrong size'
        if item['alpha']=='opaque':assert im.getchannel('A').getextrema()==(255,255),'Unexpected alpha'
        else:
            assert {im.getpixel((x,y))[3] for y in range(im.height) for x in range(im.width)}<={0,255},'Nonbinary alpha'
            bounds=im.getchannel('A').getbbox();assert bounds and bounds[3]==im.height,'Wrong base anchor'
        for group in ['layers','slices']:
            for part in item.get(group,{}).values():
                assert sha((ROOT/part['file']).read_bytes())==part['sha256'],'UI derivative drift'
        if 'layers' in item:
            frame_key,fill_key=('border','field') if item['kind']=='rug' else ('frame','fill')
            frame=Image.open(ROOT/item['layers'][frame_key]['file']).convert('RGBA');fill=Image.open(ROOT/item['layers'][fill_key]['file']).convert('RGBA')
            assert Image.alpha_composite(frame,fill).tobytes()==im.tobytes(),'UI layers do not reconstruct source'
    expected=set()
    for item in manifest['components'].values():
        expected.add(item['file'])
        for group in ['layers','slices']:
            expected.update(part['file'] for part in item.get(group,{}).values())
    actual={p.relative_to(ROOT).as_posix() for p in PROD.rglob('*.png')}
    assert actual==expected,'Missing or unlisted production PNGs: '+str(actual^expected)
    for ref in manifest['references']:assert sha((ROOT/ref['path']).read_bytes())==ref['sha256'],'Cursor reference drift'
    print('Production PNGs:',len(actual),'(primary components plus border/fill/slice layers).')
    print('Verified',len(manifest['components']),'components, source/output hashes, dimensions, alpha, anchors and approved cursor hashes. Pending:',len(manifest['pending']))
    pending={c['id'] for c in read_json(CFG)['components']}-set(manifest['components'])
    if pending:raise ValueError('Configured outputs remain pending: '+', '.join(sorted(pending)))

def self_test():
    im=Image.new('RGBA',(96,32),(0,0,0,0));d=ImageDraw.Draw(im);d.rectangle((4,4,11,19),fill=(255,0,0,255));d.rectangle((36,3,55,23),fill=(0,0,255,255));im.putpixel((3,3),(0,255,0,127));im.putpixel((4,4),(255,0,0,128))
    output,meta=normalize(im,{'grid':[3,1],'cell':[0,0],'size':[64,64],'alpha':'cutout'})
    assert meta['cellRect']==[0,0,32,32] and meta['trimRect']==[4,4,12,20]
    assert output.getchannel('A').getbbox()==(16,0,48,64)
    assert {output.getpixel((x,y))[:3] for y in range(output.height) for x in range(output.width) if output.getpixel((x,y))[3]}=={(255,0,0)},'Neighbor cell leaked into cutout'
    try:normalize(Image.new('RGBA',(31,32)),{'grid':[3,1],'cell':[0,0],'size':[64,64],'alpha':'cutout'});raise AssertionError('Accepted partial cells')
    except ValueError:pass
    print('PASS regular-cell isolation, threshold127/128, aspect fit, bottom-center anchor and invalid-grid rejection.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    imp=sub.add_parser('import-master');imp.add_argument('source_id');imp.add_argument('path')
    exp=sub.add_parser('export');exp.add_argument('--source');exp.add_argument('--refresh-derived',action='store_true',help='Explicitly refresh only derived layer/slice PNGs; preserved masters and full components remain frozen');sub.add_parser('verify');sub.add_parser('self-test')
    args=parser.parse_args()
    if args.command=='import-master':import_master(args.source_id,args.path)
    elif args.command=='export':
        ALLOW_DERIVED_REFRESH=args.refresh_derived;export(args.source)
    elif args.command=='verify':verify()
    else:self_test()
