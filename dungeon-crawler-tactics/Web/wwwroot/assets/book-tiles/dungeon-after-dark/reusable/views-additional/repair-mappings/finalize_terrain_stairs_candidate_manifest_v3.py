"""Correct transport provenance metadata without touching any candidate pixels."""
from pathlib import Path
import json,hashlib,copy
OUT=Path(__file__).resolve().parents[1];PACK=OUT.parent.parent;CDIR=OUT/'candidates/page-dark-next-six-terrain-stairs-v1'
M2=CDIR/'terrain-stairs-candidate-manifest-v2.json';HAND=Path('/workspace/scratch/page-dark-future-six-terrain-stairs-handoff-v2-20261026.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 m=copy.deepcopy(json.loads(M2.read_text()));m['supersedes_manifest']='reusable/views-additional/candidates/page-dark-next-six-terrain-stairs-v1/terrain-stairs-candidate-manifest-v2.json';m['supersedes_manifest_sha256']=sha(M2)
 group_files={'battlefield-earth-up-down':'exec-53d18104-6a7f-4218-8a05-bb8501ad1529.png','larracos-cobble-up-down':'exec-2058fcfd-a29c-49cf-bde3-7f31bf786623.png','cemetery-flagstone-up-down':'exec-d9a26cd6-69ae-41da-9b30-c7202513474c.png','battlefield-earth-rear':'exec-cf888908-9ef7-4e90-b390-ac91702f40b5.png','larracos-cobble-rear':'exec-bb2e08dd-dac8-409b-93d0-4b1b3c5384ce.png','cemetery-flagstone-rear':'exec-8da0a943-83e6-4ab9-9a0f-ede1a3406b5c.png'}
 for r in m['raw_requests']:
  g=r['group_id'];file=group_files[g];raw=Path('/workspace/generated_images')/file
  # Portable record uses retained in-pack raw and the actual tool result filename/hash; no runtime absolute ref.
  retained=OUT/r['raw_path'].replace('reusable/views-additional/','',1)
  assert sha(raw)==sha(retained)==r['raw_sha256']
  r['tool_request_id']=None;r['local_request_label']=r.pop('request_id');r['tool_response_name']=file;r['tool_response_sha256']=sha(raw)
 for c in m['candidates']:
  if c.get('raw_path'):
   g=Path(c['raw_path']).stem;file=group_files[g];r=next(x for x in m['raw_requests'] if x['group_id']==g)
   c['tool_request_id']=None;c['request_id']=None;c['local_request_label']=r['local_request_label'];c['tool_response_name']=file;c['tool_response_sha256']=r['tool_response_sha256']
 script=OUT/'repair-mappings/stage_page_dark_terrain_stairs_rekey_v2.py'
 m['extraction_recipe_path']='reusable/views-additional/repair-mappings/stage_page_dark_terrain_stairs_rekey_v2.py';m['extraction_recipe_sha256']=sha(script)
 m['handoff_id']='page-dark-future-six-terrain-stairs-handoff-v2-20261026.json';m['handoff_sha256']=sha(HAND)
 p=CDIR/'terrain-stairs-candidate-manifest-v3.json';p.write_text(json.dumps(m,indent=2)+'\n')
 # Reuse identical v2 contact pixels; bind proof to new manifest.
 cp=CDIR/'terrain-stairs-source-six-candidates-v2.png';contact_sha=sha(cp)
 proof=json.loads((CDIR/'terrain-stairs-candidate-contact-proof-v2.json').read_text());proof['manifest_path']=p.relative_to(PACK).as_posix();proof['manifest_sha256']=sha(p);proof['contact_sha256']=contact_sha;proof['supersedes_manifest_v2_sha256']=sha(M2)
 pf=CDIR/'terrain-stairs-candidate-contact-proof-v3.json';pf.write_text(json.dumps(proof,indent=2)+'\n')
 # Assert no absolute file references in the candidate manifest.
 def scan(x,path=''):
  if isinstance(x,dict):
   for k,v in x.items():scan(v,path+'.'+k)
  elif isinstance(x,list):
   for i,v in enumerate(x):scan(v,path+f'[{i}]')
  elif isinstance(x,str) and x.startswith('/'):raise AssertionError(('absolute reference',path,x))
 scan(m)
 print(json.dumps({'manifest':p.relative_to(PACK).as_posix(),'manifest_sha256':sha(p),'contact':cp.relative_to(PACK).as_posix(),'contact_sha256':contact_sha,'proof':pf.relative_to(PACK).as_posix(),'proof_sha256':sha(pf),'candidate_pixels_unchanged':True,'request_id_fields_null':all(c.get('tool_request_id') is None and c.get('request_id') is None for c in m['candidates'] if c.get('raw_path'))},indent=2))
if __name__=='__main__':main()
