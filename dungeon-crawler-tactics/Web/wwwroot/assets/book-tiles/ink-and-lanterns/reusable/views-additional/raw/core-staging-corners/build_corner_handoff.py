from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,os
BASE=Path(__file__).resolve().parents[4]
IDX=BASE/'reusable/index.json'; MERGED=Path('/workspace/scratch/view-review-merged.json'); PAGE=Path('/workspace/scratch/view-qa-report.json'); ROOT=Path('/workspace/scratch/view-qa-root.json'); HANDOFF=Path(__file__).resolve().parent/'current-corner-handoff.json'; VIEWS=('front','top','right','left','bottom','rear')
PREFIXES=['bubble-desert-adobe-desert-plaster','bubble-glass-sand-coloured-glass','bubble-sea-submarine-metal-hull','great-race-transition-glass-maze','hunting-shrines-village-stone','hunting-zockau-painted-town-brick','industry-menagerie-soot-stained-brick','over-city-venues-painted-civic-stone','safe-services-cream-service-tile','surface-entry-urban-brick']
OIDS=[f'{p}-{kind}-corner' for p in PREFIXES for kind in ('inner','outer') if not (p=='industry-menagerie-soot-stained-brick' and kind=='outer')]
sha=lambda b:hashlib.sha256(b).hexdigest(); load=lambda p:json.loads(p.read_text())
idx=load(IDX); assets={a['id']:a for a in idx['assets']}; merged=load(MERGED); lib=next(x for x in merged['libraries'] if x['scope']=='book-tiles/ink-and-lanterns'); sets={s['object_id']:s for s in lib['sets']}; page=load(PAGE); root=load(ROOT); page_rec=page['reviewed']; root_rec=root['reviewed']; items=[]; skipped=[]; errors=[]
for oid in OIDS:
 if oid not in assets or oid not in sets: errors.append(f'missing canonical source or merged view set: {oid}');continue
 src=assets[oid]; ms=sets[oid]; source_path=BASE/src['image']['path']; source_sha=sha(source_path.read_bytes())
 if source_sha!=src['image']['sha256']:errors.append(f'live source hash differs from index: {oid}')
 if ms.get('source',{}).get('path')!=src['image']['path']:errors.append(f'merged source path differs: {oid}')
 views={}
 for v in VIEWS:
  ref=ms.get('views',{}).get(v)
  if not ref:errors.append(f'missing merged view ref {oid}.{v}');continue
  p=BASE/ref['path']; actual=sha(p.read_bytes())
  if actual!=ref['sha256']:errors.append(f'live image hash differs from merged for {oid}.{v}')
  with Image.open(p) as im:size=list(im.size); alpha=list(im.convert('RGBA').getchannel('A').getbbox() or (0,0,0,0))
  views[v]={'asset_id':ref.get('asset_id'),'path':ref['path'],'sha256':actual,'size_wh':size,'alpha_bbox_xyxy':alpha}
 evidence=[]; key='book-tiles/ink-and-lanterns::'+oid
 for reviewer,records in [('page_inventory',page_rec),('root',root_rec)]:
  rec=records.get(key)
  if not rec:continue
  source_match=(rec.get('source_sha256')==source_sha if 'source_sha256' in rec else rec.get('source')==str(source_path))
  image_match=all(rec.get('image_hashes',{}).get(v)==views[v]['sha256'] for v in VIEWS)
  if source_match and image_match:evidence.append({'reviewer':reviewer,'status':rec.get('status'),'reviewed_at':rec.get('reviewed_at'),'affected_views':rec.get('affected_views'),'notes':rec.get('notes',[]),'source_hash_matched':True,'all_six_hashes_matched':True})
 review=ms.get('review') or {}
 if review:evidence.append({'reviewer':review.get('reviewer'),'status':review.get('status'),'reviewed_at':review.get('reviewed_at'),'affected_views':review.get('affected_views'),'notes':review.get('notes',[]),'source_hash_matched':True,'all_six_hashes_matched':True,'evidence_source':'view-review-merged.json'})
 passes=[e for e in evidence if e.get('status') in ('pass','passed','whole-pass','whole-pass-current')]
 if passes:skipped.append({'object_id':oid,'reason':'source and all six live image hashes match whole-set PASS','pass_reviews':passes});continue
 nonpending=[e for e in evidence if e.get('status') not in (None,'pending')]; freshest=sorted(nonpending,key=lambda e:e.get('reviewed_at') or '',reverse=True)
 items.append({'object_id':oid,'source':{'path':src['image']['path'],'sha256':source_sha,'rgba_sha256':src['image'].get('rgba_sha256')},'current_views':views,'review_evidence':evidence,'freshest_nonpending_review':freshest[0] if freshest else None,'catalog_name':src.get('name'),'kind':src.get('kind'),'category':src.get('category'),'tags':src.get('tags',[]),'status':ms.get('status')})
if errors:raise SystemExit('\n'.join(errors))
OUT=HANDOFF.parent
for start in range(0,len(items),3):
 group=items[start:start+3];cw=164;ch=190;contact=Image.new('RGBA',(7*cw,len(group)*ch),(42,42,46,255));draw=ImageDraw.Draw(contact)
 for row,item in enumerate(group):
  draw.text((2,row*ch+2),item['object_id'],fill='white'); paths=[('SOURCE',BASE/item['source']['path'])]+[(v.upper(),BASE/item['current_views'][v]['path']) for v in VIEWS]
  for col,(label,p) in enumerate(paths):
   im=Image.open(p).convert('RGBA');im.thumbnail((128,128),Image.Resampling.NEAREST);x=col*cw+18+(128-im.width)//2;y=row*ch+32+(128-im.height)//2;contact.alpha_composite(im,(x,y));draw.text((col*cw+3,row*ch+17),label,fill='white')
 cp=OUT/f'corner-source-six-{start+1:02d}-{start+len(group):02d}.png';contact.save(cp,optimize=False)
 for item in group:item['source_six_contact']={'path':cp.name,'sha256':sha(cp.read_bytes())}
record={'schema_version':1,'status':'candidate-only staging handoff','scope':'book-tiles/ink-and-lanterns/reusable/views-additional/raw/core-staging-corners','installer':'views_ink_books','reviewer':'root','write_scope':'raw/core-staging-corners only','live_writes_permitted':False,'source_index':{'path':str(IDX),'sha256':sha(IDX.read_bytes())},'merged_review':{'path':str(MERGED),'sha256':sha(MERGED.read_bytes())},'page_ledger':{'path':str(PAGE),'sha256':sha(PAGE.read_bytes())},'root_ledger':{'path':str(ROOT),'sha256':sha(ROOT.read_bytes())},'wall_axes':'L belongs in XY; four cardinal elevations are rectangular joined-wall silhouettes at a shared Z, with L plans only top/bottom. All inferred geometry/material mappings must preserve target source identity.','canvas_contract':{'size_wh':[256,256],'anchor_px':[128,128]},'skipped_passed':skipped,'sets':items}
tmp=HANDOFF.with_suffix('.json.tmp');tmp.write_text(json.dumps(record,indent=2)+'\n');os.replace(tmp,HANDOFF)
print(json.dumps({'requested':len(OIDS),'active_unresolved':len(items),'skipped_whole_pass':len(skipped),'handoff':str(HANDOFF),'sets':[{'id':x['object_id'],'status':x['status'],'affected':(x.get('freshest_nonpending_review') or {}).get('affected_views'),'reviewer':(x.get('freshest_nonpending_review') or {}).get('reviewer')} for x in items]},indent=2))
