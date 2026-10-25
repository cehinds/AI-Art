import fs from 'node:fs/promises';
import { constants } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { ROOT,REPO,GAMES,git,tree,indexTree,files,hash,blobHash } from './lib.mjs';

// Default imports are append-only. --update is an explicitly reviewed migration
// allowed only after the exact previous source snapshot is preserved in HEAD.
export async function importGame(game, root=ROOT, {update=false}={}) {
  const commit=git(['rev-parse',`origin/${game.branch}^{commit}`],root).toString().trim();
  const entries=tree(commit,root);
  if(entries.some(e=>e.path==='_source.json')) throw new Error('Source already owns reserved _source.json path');
  if(entries.some(e=>e.type!=='blob'||!['100644','100755'].includes(e.mode))) throw new Error('Symlinks/submodules require an explicit import policy');
  const target=path.join(root,'Games',game.id);
  let previous=null,previousManifestBytes=null,previousCatalogCommit=null;
  try {
    await fs.access(target);
    previousManifestBytes=await fs.readFile(path.join(target,'_source.json'));
    const existing=JSON.parse(previousManifestBytes);
    if(existing.commit!==commit && !update) throw new Error(`Upstream changed for ${game.id}; review a migration instead of overwriting ${target}`);
    const oldEntries=tree(existing.commit,root);
    if(existing.files.length!==oldEntries.length) throw new Error(`Incomplete source manifest: ${game.id}`);
    const expected=new Map(oldEntries.map(entry=>[entry.path,entry]));
    const actual=await files(target);
    if(JSON.stringify(actual)!==JSON.stringify(oldEntries.map(e=>e.path).concat('_source.json').sort())) throw new Error(`Snapshot contains added or missing files: ${game.id}`);
    if(new Set(existing.files.map(e=>e.path)).size!==oldEntries.length) throw new Error(`Duplicate source inventory paths: ${game.id}`);
    for(const entry of existing.files) {
      if(entry.blob!==expected.get(entry.path)?.blob || entry.mode!==expected.get(entry.path)?.mode) throw new Error(`Source inventory changed: ${game.id}/${entry.path}`);
      const bytes=await fs.readFile(path.join(target,entry.path));
      if(hash(bytes)!==entry.sha256 || blobHash(bytes)!==entry.blob) throw new Error(`Local snapshot changed: ${game.id}/${entry.path}`);
    }
    if(existing.commit===commit) {
      console.log(`${game.id}: verified existing ${existing.files.length} files at ${commit}`);
      return existing;
    }
    previousCatalogCommit=git(['rev-parse','HEAD'],root).toString().trim();
    const committed=new Map(tree(previousCatalogCommit,root).map(entry=>[entry.path,entry]));
    const indexedEntries=indexTree(root).filter(entry=>entry.path.startsWith(`Games/${game.id}/`));
    const indexed=new Map(indexedEntries.map(entry=>[entry.path,entry]));
    if(committed.get(`Games/${game.id}/_source.json`)?.blob!==blobHash(previousManifestBytes)) throw new Error(`Previous snapshot manifest must be committed before update: ${game.id}`);
    for(const entry of existing.files) if(committed.get(`Games/${game.id}/${entry.path}`)?.blob!==entry.blob||committed.get(`Games/${game.id}/${entry.path}`)?.mode!==entry.mode) throw new Error(`Previous snapshot file must be committed exactly before update: ${game.id}/${entry.path}`);
    if(indexedEntries.length!==existing.files.length+1 || indexedEntries.some(entry=>entry.stage!=='0'||entry.blob!==committed.get(entry.path)?.blob||entry.mode!==committed.get(entry.path)?.mode)) throw new Error(`Snapshot index differs from preserved HEAD: ${game.id}`);
    previous=existing;
  } catch(error) { if(error.code!=='ENOENT') throw error; }
  // An existing unmanifested directory must never be adopted or overwritten.
  if(!previous) try { await fs.access(target); throw new Error(`Existing unmanifested directory: ${target}`); } catch(e) { if(e.code!=='ENOENT') throw e; }
  const staging=await fs.mkdtemp(path.join(os.tmpdir(),'ai-art-import-'));
  const extracted=path.join(staging,'snapshot');
  await fs.mkdir(extracted);
  const previousByPath=new Map(previous?.files.map(entry=>[entry.path,entry])||[]);
  const payloadEntries=previous?entries.filter(entry=>previousByPath.get(entry.path)?.blob!==entry.blob):entries;
  // Windows core.autocrlf can affect archive text conversion. Pin conversion
  // off for this command, then prove every extracted byte against its blob.
  // Updates transfer only changed/new blobs. Unchanged multi-gigabyte originals
  // stay in place; their byte-verified inventory is reused, never copied.
  const batches=[];
  if(!previous) batches.push([]);
  else for(const entry of payloadEntries) {
    let batch=batches.at(-1);
    if(!batch || batch.join(' ').length+entry.path.length>6000) {batch=[];batches.push(batch);}
    batch.push(entry.path);
  }
  for(let index=0;index<batches.length;index++) {
    const archive=path.join(staging,`source-${index}.tar`);
    git(['-c','core.autocrlf=false','archive','--format=tar',`--output=${archive}`,commit,...(previous?['--',...batches[index]]:[])],root);
    execFileSync('tar',['-xf',archive,'-C',extracted]);
  }
  const extractedPaths=await files(extracted);
  if(JSON.stringify(extractedPaths)!==JSON.stringify(payloadEntries.map(entry=>entry.path).sort())) throw new Error(`Archive omitted files; refusing partial import of ${game.id}`);
  const inventory=[];
  for(const entry of entries) {
    if(previousByPath.get(entry.path)?.blob===entry.blob) {
      inventory.push({...previousByPath.get(entry.path),mode:entry.mode});
      continue;
    }
    const bytes=await fs.readFile(path.join(extracted,entry.path));
    if(blobHash(bytes)!==entry.blob) throw new Error(`Archive changed original bytes: ${game.id}/${entry.path}`);
    inventory.push({path:entry.path,blob:entry.blob,mode:entry.mode,bytes:bytes.length,sha256:hash(bytes)});
  }
  const manifest={schemaVersion:1,repository:REPO,game:game.id,branch:game.branch,commit,files:inventory};
  if(previous) {
    const old=new Map(previous.files.map(entry=>[entry.path,entry]));
    const next=new Map(inventory.map(entry=>[entry.path,entry]));
    const added=inventory.filter(entry=>!old.has(entry.path)).map(entry=>entry.path);
    const changed=inventory.filter(entry=>old.has(entry.path)&&old.get(entry.path).blob!==entry.blob).map(entry=>entry.path);
    const deleted=previous.files.filter(entry=>!next.has(entry.path)).map(entry=>entry.path);
    manifest.update={previousSourceCommit:previous.commit,previousCatalogCommit,added,changed,deleted};
    // Revalidate each changed/deleted file immediately before applying its
    // reviewed update, and never overwrite an unexpected newly created file.
    for(const relative of [...changed,...deleted]) if(hash(await fs.readFile(path.join(target,relative)))!==old.get(relative).sha256) throw new Error(`Concurrent local change: ${game.id}/${relative}`);
    if(!previousManifestBytes.equals(await fs.readFile(path.join(target,'_source.json')))) throw new Error(`Concurrent manifest change: ${game.id}`);
    for(const relative of [...added,...changed]) {
      const destination=path.resolve(target,relative);
      if(!destination.startsWith(path.resolve(target)+path.sep)) throw new Error('Unsafe import destination');
      await fs.mkdir(path.dirname(destination),{recursive:true});
      await fs.copyFile(path.join(extracted,relative),destination,old.has(relative)?0:constants.COPYFILE_EXCL);
    }
    for(const relative of deleted) await fs.unlink(path.join(target,relative));
    await fs.writeFile(path.join(target,'_source.json'),JSON.stringify(manifest,null,2)+'\n');
    console.log(`${game.id}: reviewed update ${previous.commit} -> ${commit}: ${added.length} added, ${changed.length} changed, ${deleted.length} removed (preserved in ${previousCatalogCommit})`);
  } else {
    await fs.writeFile(path.join(extracted,'_source.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
    await fs.mkdir(path.dirname(target),{recursive:true});
    await fs.rename(extracted,target);
  }
  // Keep archive staging on disk: no destructive cleanup of imported sources.
  console.log(`${game.id}: imported ${inventory.length} exact files at ${commit}`);
  return manifest;
}
if(process.argv[1] && import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href) {
  for(const game of GAMES) await importGame(game,ROOT,{update:process.argv.includes('--update')});
}
