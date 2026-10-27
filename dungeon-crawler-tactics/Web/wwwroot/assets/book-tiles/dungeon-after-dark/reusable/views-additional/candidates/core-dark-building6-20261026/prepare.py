import os,json,hashlib,numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D="/workspace/AI-Art/dungeon-crawler-tactics/Web/wwwroot/assets/book-tiles/dungeon-after-dark"; S=D+"/reusable/views-additional"; C=S+"/candidates/core-dark-building6-20261026"
H=json.load(open("/workspace/scratch/dark-future-six-building-plan-handoff-20261026.json")); objs={x["object_id"]:x for x in H["objects"]}; reqs=json.load(open(C+"/requests-imagegen.json")); results=[]; filehash=lambda p:hashlib.sha256(open(p,"rb").read()).hexdigest()
for q in reqs:
 o=objs[q["object_id"]]; raw=Image.open(q["raw_path"]).convert("RGBA"); alpha=np.array(raw.getchannel("A")); lab,n=label(alpha>=16); counts=np.bincount(lab.ravel()); counts[0]=0; k=int(counts.argmax()); yy,xx=np.where(lab==k)
 if not len(xx): raise SystemExit("empty: "+q["object_id"]+":"+q["view"])
 box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]; crop=raw.crop(box); ca=np.array(crop.getchannel("A")); ca[lab[box[1]:box[3],box[0]:box[2]]!=k]=0; crop.putalpha(Image.fromarray(ca))
 base=Image.open(o["views"][q["view"]]["path"]).convert("RGBA"); ba=np.array(base.getchannel("A")); by,bx=np.where(ba>=16); basebox=[int(bx.min()),int(by.min()),int(bx.max()+1),int(by.max()+1)]; targetw=basebox[2]-basebox[0]
 scale=targetw/crop.width; nw=targetw; nh=max(1,round(crop.height*scale))
 if nh>220: scale=min(scale,220/crop.height);nw=round(crop.width*scale);nh=round(crop.height*scale)
 sc=crop.resize((nw,nh),Image.Resampling.NEAREST); out=Image.new("RGBA",(256,256),(0,0,0,0)); x=(256-nw)//2;y=(256-nh)//2;out.alpha_composite(sc,(x,y))
 cand=C+f"/{q['object_id']}.{q['view']}.candidate-v1.png";out.save(cand,optimize=False)
 results.append({"object_id":q["object_id"],"view":q["view"],"request_id":q["request_id"],"prompt":q["prompt"],"prompt_sha256":hashlib.sha256(q["prompt"].encode()).hexdigest(),"raw_response":{"path":os.path.relpath(q["raw_path"],D),"sha256":filehash(q["raw_path"]),"dimensions_px":list(raw.size)},"generator_path":q.get("generator_path"),"references":[{"path":os.path.relpath(p,D),"sha256":filehash(p)} for p in q["reference_paths"]],"canonical_source":{"path":os.path.relpath(o["source"]["path"],D),"sha256":o["source"]["sha256"]},"base_current_view":{"path":os.path.relpath(o["views"][q["view"]]["path"],D),"sha256":o["views"][q["view"]]["sha256"]},"all_six_base_hashes":{v:x["sha256"] for v,x in o["views"].items()},"normalization":{"alpha_threshold":16,"connected_component_connectivity":8,"component_count":int(n),"selected_component_pixels":int(counts[k]),"crop_bounds_xyxy_px":box,"current_view_alpha_bbox_xyxy_px":basebox,"isotropic_scale":scale,"resized_dimensions_px":[nw,nh],"center_offset_px":[x,y],"canvas_px":[256,256],"anchor_px":[128,128],"resampling":"nearest-neighbor","discarded_disconnected_components":True},"candidate":{"path":os.path.relpath(cand,D),"sha256":filehash(cand),"dimensions_px":[256,256],"alpha_bbox_xyxy_px":list(out.getchannel("A").getbbox() or [])},"status":"candidate-only, pending Page review"})
groups={"building6-batch1-shop-ladder":["over-city-damaged-shop-front","over-city-roof-access-ladder"],"building6-batch2-stall-temple-portal":["over-city-venues-mall-shop-stall","over-city-venues-education-temple-entrance","personal-space-personal-space-portal-door"],"building6-batch3-ladder-garage":["over-city-roof-access-ladder","race-circuits-garage-bay-door"]}
for name,ids in groups.items():
 rows=[]
 for oid in ids:
  o=objs[oid]; candidates=[r for r in results if r["object_id"]==oid]; items=[("SOURCE",Image.open(o["source"]["path"]).convert("RGBA"))]+[(v,Image.open(o["views"][v]["path"]).convert("RGBA")) for v in ("front","top","right","left","bottom","rear")]+[("CANDIDATE "+r["view"].upper(),Image.open(D+"/"+r["candidate"]["path"]).convert("RGBA")) for r in candidates]; rows.append((oid,items))
 cols=max(len(z) for _,z in rows); cw,ch=260,280; contact=Image.new("RGB",(cols*cw,len(rows)*ch),(24,24,24))
 for ri,(oid,items) in enumerate(rows):
  for ci,(label,im) in enumerate(items):
   cell=Image.new("RGBA",(cw,ch),(38,38,38,255));dr=ImageDraw.Draw(cell)
   for yy in range(28,ch,16):
    for xx in range(0,cw,16):
     if ((xx//16)+(yy//16))%2: dr.rectangle((xx,yy,xx+15,yy+15),fill=(54,54,54,255))
   if label=="SOURCE" and max(im.size)<220:
    fac=min(200/im.width,200/im.height); im=im.resize((round(im.width*fac),round(im.height*fac)),Image.Resampling.NEAREST)
   im.thumbnail((240,230),Image.Resampling.NEAREST);cell.alpha_composite(im,((cw-im.width)//2,34+(230-im.height)//2));ImageDraw.Draw(cell).text((4,4),label,fill="white");contact.paste(cell.convert("RGB"),(ci*cw,ri*ch))
  ImageDraw.Draw(contact).text((2,ri*ch+264),oid,fill="white")
 p=C+"/contacts/"+name+"-source-six-candidate.png";contact.save(p)
checks=[]
for o in objs.values():
 for e in [o["source"],*o["views"].values()]: checks.append(filehash(e["path"])==e["sha256"])
if not all(checks): raise SystemExit("live source/view hash changed during candidate generation")
report={"schema_version":1,"scope":"candidate-only Dark building-plan6","handoff":"/workspace/scratch/dark-future-six-building-plan-handoff-20261026.json","handoff_status":H["status"],"verified_inputs":{"canonical_and_six_file_count":len(checks),"all_hashes_match_handoff":all(checks)},"contacts":{name:{"path":os.path.relpath(C+"/contacts/"+name+"-source-six-candidate.png",D),"sha256":filehash(C+"/contacts/"+name+"-source-six-candidate.png")} for name in groups},"candidate_views":results,"install_status":"none; waiting for Page visual review and Dark sole installer"}
json.dump(report,open(C+"/building6-candidate-report-v1.json","w"),indent=2)
print(json.dumps({"verified_files":len(checks),"all_match":all(checks),"contacts":report["contacts"],"candidates":[{"id":r["object_id"],"view":r["view"],"sha256":r["candidate"]["sha256"],"bbox":r["candidate"]["alpha_bbox_xyxy_px"]} for r in results]},indent=2))
