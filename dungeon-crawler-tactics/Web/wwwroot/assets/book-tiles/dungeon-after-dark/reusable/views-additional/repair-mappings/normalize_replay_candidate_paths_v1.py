"""Normalize frozen candidate paths to the replay module's OUT-relative contract.

Read-only preflight is performed for every row before any write. The original
recipe bytes are retained as a .raw archive and bound by a JSON audit.
"""
from pathlib import Path, PurePosixPath
import hashlib, json, os
HERE=Path(__file__).resolve().parent
OUT=HERE.parent
BOOK=OUT.parent.parent
RECIPE=HERE/'replay-installed-dark-repairs-v2.json'
RAW=HERE/'replay-installed-dark-repairs-v2.pre-candidate-path-normalization-v1.json.raw'
AUDIT=HERE/'replay-candidate-path-normalization-audit-v1.json'
PREFIX='reusable/views-additional/'
def sha(b): return hashlib.sha256(b).hexdigest()
def digest(p): return sha(Path(p).read_bytes())
def safe(root, rel):
 if not isinstance(rel,str) or not rel: raise ValueError(f'invalid empty path {rel!r}')
 p=PurePosixPath(rel)
 if p.is_absolute() or '..' in p.parts: raise ValueError(f'unsafe path {rel!r}')
 q=(root/Path(*p.parts)).resolve(); q.relative_to(root.resolve()); return q
def atomic(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(data);os.replace(tmp,path)
def main():
 original=RECIPE.read_bytes(); original_sha=sha(original); doc=json.loads(original); entries=doc.get('entries'); assert isinstance(entries,list)
 planned=[]; results=[]
 for i,e in enumerate(entries):
  old=e.get('candidate_path'); expected=e.get('candidate_sha256')
  if not isinstance(old,str) or not expected: raise ValueError(f'entry {i}: missing path/hash')
  if old.startswith(PREFIX):
   new=old[len(PREFIX):]; resolution='pack-relative-after-prefix-strip'
  else:
   new=old; resolution='existing-views-additional-relative'
  candidate=safe(OUT,new)
  if not candidate.is_file():
   # An explicit pack-relative path is considered only when it is rooted by a
   # known pack prefix and remains contained in the canonical pack.
   candidate=safe(BOOK,old)
   if not candidate.is_file(): raise FileNotFoundError(f'entry {i} {e.get("asset_id")}: no candidate at OUT-relative or pack-relative path {old!r}')
   book_rel=candidate.relative_to(BOOK).as_posix()
   if not book_rel.startswith(PREFIX): raise ValueError(f'entry {i}: pack candidate outside reusable/views-additional: {book_rel}')
   new=book_rel[len(PREFIX):]; candidate=safe(OUT,new); resolution='validated-pack-relative-prefix-strip'
  actual=digest(candidate)
  if actual!=expected: raise ValueError(f'entry {i} {e.get("asset_id")}: candidate SHA mismatch {actual} != {expected}')
  if new!=old:
   planned.append((i,old,new));results.append({'entry_index':i,'asset_id':e.get('asset_id'),'original_path':old,'normalized_path':new,'path_resolution':resolution,'candidate_sha256':actual})
  e['candidate_path']=new
 # Validate all rows under the exact path semantics consumed by replay_installed_dark_repairs.py.
 for i,e in enumerate(entries):
  q=safe(OUT,e['candidate_path'])
  if not q.is_file() or digest(q)!=e['candidate_sha256']: raise ValueError(f'post-normalization replay path failure: {i}/{e.get("asset_id")}')
 if not planned:
  print(json.dumps({'status':'already-normalized','recipe_sha256':original_sha,'entry_count':len(entries)},indent=2));return
 if RAW.exists():
  if digest(RAW)!=original_sha: raise FileExistsError(f'original raw recipe exists with different bytes: {RAW}')
 else: atomic(RAW,original)
 updated=(json.dumps(doc,indent=2)+'\n').encode()
 # Use a separate immutable audit; do not rewrite it on repeated runs.
 audit={'schema':'replay-candidate-path-normalization-audit-v1','recipe_path':RECIPE.relative_to(BOOK).as_posix(),'recipe_original_sha256':original_sha,'recipe_original_archive_path':RAW.relative_to(BOOK).as_posix(),'recipe_original_archive_sha256':digest(RAW),'recipe_updated_sha256':sha(updated),'normalizer_contract':'candidate_path is relative to reusable/views-additional (OUT); each normalized path is checked for containment and exact candidate_sha256 before use','changed_entry_count':len(results),'changes':results}
 audit_bytes=(json.dumps(audit,indent=2)+'\n').encode()
 if AUDIT.exists() and AUDIT.read_bytes()!=audit_bytes: raise FileExistsError(f'audit already exists but differs: {AUDIT}')
 atomic(RECIPE,updated)
 if not AUDIT.exists(): atomic(AUDIT,audit_bytes)
 print(json.dumps({'status':'normalized','changed_entry_count':len(results),'recipe_sha256_before':original_sha,'recipe_sha256_after':sha(RECIPE.read_bytes()),'archive_path':RAW.relative_to(BOOK).as_posix(),'archive_sha256':digest(RAW),'audit_path':AUDIT.relative_to(BOOK).as_posix(),'audit_sha256':digest(AUDIT)},indent=2))
if __name__=='__main__':main()
