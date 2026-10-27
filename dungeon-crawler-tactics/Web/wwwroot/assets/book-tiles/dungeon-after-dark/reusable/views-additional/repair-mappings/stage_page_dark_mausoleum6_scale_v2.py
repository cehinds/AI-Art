"""Stage Root-requested uniform-scale/mask cleanup for six mausoleum directions only."""
import json,hashlib,pathlib,copy
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
OUT=pathlib.Path(__file__).resolve().parents[1];PACK=OUT.parent.parent;CDIR=OUT/'candidates/page-dark-next-six-mausoleum-v1'
M1=CDIR/'mausoleum6-candidate-manifest.json';HAND=pathlib.Path('/workspace/scratch/page-dark-future-six-mausoleum-handoff-20261026.json')
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def safe(rel):
 p=(PACK/rel).resolve();p.relative_to(PACK.resolve());return p
def rgba(p):return Image.open(p).convert('RGBA')
def nearest_fit(crop,w,h):return crop.resize((w,h),Image.Resampling.NEAREST)
def main():
 m1=json.loads(M1.read_text()); hand=json.loads(HAND.read_text()); objmap={x['object_id']:x for x in m1['objects']}; candmap={(x['object_id'],x['view']):x for x in m1['candidates']}
 # Verify every current source and six remains bound to the handoff before producing v2.
 for o in hand['objects']:
  source=o['source']; assert sha(pathlib.Path(source['path']))==source['sha256']
  for view,x in o['views'].items():assert sha(pathlib.Path(x['path']))==x['sha256'],(o['object_id'],view)
 updates=[]
 # Filter each generated view to its main connected alpha component while retaining a 3px soft-alpha halo.
 for oid in ['ghost-cemetery-white-mausoleum-masonry-open-doorway','ghost-cemetery-white-mausoleum-masonry-closed-doorway']:
  c=candmap[(oid,'top')];raw=safe(c['raw_path']);im=rgba(raw);arr=np.asarray(im);alpha=arr[:,:,3]
  labels,n=ndimage.label(alpha>=16);counts=np.bincount(labels.ravel());idx=1+int(counts[1:].argmax());main=labels==idx;ys,xs=np.where(main);bbox=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
  keep=ndimage.binary_dilation(main,iterations=3)&(alpha>0);ys2,xs2=np.where(keep);cropbox=(int(xs2.min()),int(ys2.min()),int(xs2.max()+1),int(ys2.max()+1))
  masked=arr.copy();masked[:,:,3]=np.where(keep,alpha,0).astype(np.uint8);filtered=Image.fromarray(masked,'RGBA').crop(cropbox)
  scale=204/filtered.width; nw=204;nh=max(1,round(filtered.height*scale));scaled=nearest_fit(filtered,nw,nh);frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(scaled,((256-nw)//2,(256-nh)//2))
  v2path=CDIR/'images'/f'{oid}.top.candidate-v2.png';frame.save(v2path,format='PNG',optimize=False)
  norm={'foreground_component_threshold_alpha':16,'selected_component_index':idx,'component_count_threshold16':n,'selected_component_bbox_xyxy':list(bbox),'soft_alpha_halo_px':3,'retained_crop_bbox_xyxy':list(cropbox),'visible_alpha_bbox_before_scale':list(bbox),'target_visible_width_px':204,'uniform_scale_from_filtered_crop':scale,'resized_dimensions_px':[nw,nh],'offset_px':[(256-nw)//2,(256-nh)//2],'resampling':'nearest','anchor_px':[128,128]}
  c2=copy.deepcopy(c);c2['candidate_path']=v2path.relative_to(PACK).as_posix();c2['candidate_sha256']=sha(v2path);c2['normalization']=norm;c2['notes']+=' Faint detached components are discarded; selected soft-alpha silhouette is uniformly fitted to 204px visible width.'
  c2['review_status']='resubmitted; corrected uniform normalization per Root direction'
  updates.append(c2)
  # Exact symmetric opposite plan from the corrected top candidate.
  b=candmap[(oid,'bottom')];bp=CDIR/'images'/f'{oid}.bottom.candidate-v2.png';frame.transpose(Image.Transpose.ROTATE_180).save(bp,format='PNG',optimize=False)
  b2=copy.deepcopy(b);b2['candidate_path']=bp.relative_to(PACK).as_posix();b2['candidate_sha256']=sha(bp);b2['derived_from']={'view':'top','candidate_sha256':c2['candidate_sha256']};b2['normalization']={'operation':'rotate180','uniform_scale':1.0,'anchor_px':[128,128]};b2['notes']='Opposite plan from corrected selected TOP footprint; exact 180-degree rotation, open/closed state retained.';b2['review_status']='resubmitted; updated alias derives from corrected TOP'
  updates.append(b2)
 # Scale source-native transparent Havana front/rear to common side width/Z while preserving opening alpha.
 oid='ghost-havana-weathered-stucco-open-doorway'; src=objmap[oid]['source'];p=safe(src['path']);im=rgba(p);box=im.getchannel('A').getbbox();crop=im.crop(box);width,height=crop.size
 for view,op in [('front','copy'),('rear','mirror_x')]:
  targetw,targeth=201,151;scaled=nearest_fit(crop,targetw,targeth)
  if op=='mirror_x':scaled=scaled.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  frame=Image.new('RGBA',(256,256),(0,0,0,0));frame.alpha_composite(scaled,((256-targetw)//2,(256-targeth)//2))
  path=CDIR/'images'/f'{oid}.{view}.candidate-v2.png';frame.save(path,format='PNG',optimize=False)
  base=copy.deepcopy(candmap[(oid,view)]);base['candidate_path']=path.relative_to(PACK).as_posix();base['candidate_sha256']=sha(path);base['normalization']={'source_alpha_bbox_xyxy':list(box),'native_foreground_dimensions_px':[width,height],'target_visible_dimensions_px':[targetw,targeth],'uniform_scale':targetw/width,'resampling':'nearest','operation':op,'anchor_px':[128,128],'open_passage_alpha_preserved':True};base['notes']='Canonical source pixels uniformly scaled to the common side width/height; alpha-zero passage retained.';base['review_status']='resubmitted; common-scale source-alpha restoration'
  updates.append(base)
 m2=copy.deepcopy(m1);m2['supersedes_manifest']='reusable/views-additional/candidates/page-dark-next-six-mausoleum-v1/mausoleum6-candidate-manifest.json';m2['supersedes_manifest_sha256']=sha(M1);m2['scope']='six mausoleum/doorway objects; 14 scoped directions; v2 revises only six Root-held directions'
 for c in m2['candidates']:
  newer=next((x for x in updates if x['asset_id']==c['asset_id']),None)
  if newer:m2['candidates'][m2['candidates'].index(c)]=newer
  else:c['review_status']='previous candidate accepted; preserve exact candidate bytes'
 mp=CDIR/'mausoleum6-candidate-manifest-v2.json';mp.write_text(json.dumps(m2,indent=2)+'\n')
 # source+six+six corrected direction contact rows for three objects
 ids=['ghost-cemetery-white-mausoleum-masonry-open-doorway','ghost-cemetery-white-mausoleum-masonry-closed-doorway',oid]; rows=[];cards=[]
 for object_id in ids:
  ob=objmap[object_id]; row=[]
  cells=[('SOURCE',ob['source'])]+[(v,ob['base_six'][v]) for v in ['front','top','right','left','bottom','rear']]+[(c['view'].upper()+' V2',{'path':c['candidate_path'],'sha256':c['candidate_sha256']}) for c in updates if c['object_id']==object_id]
  proofs=[]
  for label,rec in cells:
   q=safe(rec['path']);assert sha(q)==rec['sha256'],(object_id,label)
   im=rgba(q);im.thumbnail((180,180),Image.Resampling.NEAREST);tile=Image.new('RGBA',(200,220),(31,34,39,255));tile.alpha_composite(im,((200-im.width)//2,8+(180-im.height)//2));ImageDraw.Draw(tile).text((4,195),label,fill='white');row.append(tile);proofs.append({'label':label,**rec})
  cards.append(row);rows.append({'object_id':object_id,'cells':proofs})
 cols=max(len(r) for r in cards);contact=Image.new('RGBA',(200*cols,220*len(cards)),(14,17,22,255))
 for r,row in enumerate(cards):
  for c,t in enumerate(row):contact.alpha_composite(t,(c*200,r*220))
 cp=CDIR/'mausoleum-six-corrections-source-six.png';contact.save(cp)
 proof={'manifest_path':mp.relative_to(PACK).as_posix(),'manifest_sha256':sha(mp),'contact_path':cp.relative_to(PACK).as_posix(),'contact_sha256':sha(cp),'supersedes_manifest_sha256':sha(M1),'handoff_sha256':sha(HAND),'rows':rows};pf=CDIR/'mausoleum6-candidate-contact-proof-v2.json';pf.write_text(json.dumps(proof,indent=2)+'\n')
 print(json.dumps({'manifest':proof['manifest_path'],'manifest_sha256':proof['manifest_sha256'],'contact':proof['contact_path'],'contact_sha256':proof['contact_sha256'],'corrected_directions':[x['asset_id'] for x in updates]},indent=2))
if __name__=='__main__':main()
