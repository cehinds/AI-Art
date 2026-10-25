import fs from 'node:fs/promises';
import path from 'node:path';
import { ROOT,GAMES,files,loadInventory,hash,blobHash,tree,indexTree } from './lib.mjs';
import { GitBlobReader } from './git-blobs.mjs';
export async function verifySnapshots(root=ROOT,{committed=false,gitMode=false}={}) {
  const reader=gitMode?new GitBlobReader(root):null;
  try {
  let count=0, bytes=0;
  const head=(committed||gitMode)?new Map(tree('HEAD',root).map(entry=>[entry.path,entry])):null;
  const indexed=(committed&&!gitMode)?new Map(indexTree(root).map(entry=>[entry.path,entry])):null;
  for(const game of GAMES) {
    const manifest=await loadInventory(game,root);
    const folder=path.join(root,'Games',game.id);
    const prefix=`Games/${game.id}/`;
    const actual=gitMode?[...head.keys()].filter(name=>name.startsWith(prefix)).map(name=>name.slice(prefix.length)).sort():await files(folder);
    const expected=manifest.files.map(x=>x.path).concat('_source.json').sort();
    if(JSON.stringify(actual)!==JSON.stringify(expected)) throw new Error(`Added or missing files in ${game.id}`);
    const original=gitMode?[...head.values()].filter(entry=>entry.path.startsWith(prefix)&&entry.path!==`${prefix}_source.json`).map(entry=>({...entry,path:entry.path.slice(prefix.length)})):tree(manifest.commit,root);
    if(original.length!==manifest.files.length) throw new Error(`Incomplete source inventory: ${game.id}`);
    const byPath=new Map(original.map(x=>[x.path,x]));
    if(head && head.get(`Games/${game.id}/_source.json`)?.blob!==blobHash(await fs.readFile(path.join(folder,'_source.json')))) throw new Error(`HEAD inventory mismatch: ${game.id}`);
    if(indexed && indexed.get(`Games/${game.id}/_source.json`)?.blob!==head.get(`Games/${game.id}/_source.json`)?.blob) throw new Error(`Index inventory mismatch: ${game.id}`);
    for(const entry of manifest.files) {
      const data=reader?await reader.read(entry.blob):await fs.readFile(path.join(folder,entry.path));
      if(entry.blob!==byPath.get(entry.path)?.blob || entry.mode!==byPath.get(entry.path)?.mode || data.length!==entry.bytes || hash(data)!==entry.sha256 || blobHash(data)!==entry.blob) throw new Error(`Source mismatch: ${game.id}/${entry.path}`);
      if(head && (head.get(`Games/${game.id}/${entry.path}`)?.blob!==entry.blob||head.get(`Games/${game.id}/${entry.path}`)?.mode!==entry.mode)) throw new Error(`HEAD source blob/mode mismatch: ${game.id}/${entry.path}`);
      if(indexed && (indexed.get(`Games/${game.id}/${entry.path}`)?.blob!==entry.blob||indexed.get(`Games/${game.id}/${entry.path}`)?.mode!==entry.mode||indexed.get(`Games/${game.id}/${entry.path}`)?.stage!=='0')) throw new Error(`Index source blob/mode mismatch: ${game.id}/${entry.path}`);
      count++;bytes+=data.length;
    }
    console.log(`${game.id}: ${manifest.files.length} source files verified against ${gitMode?'HEAD blobs':manifest.commit}`);
  }
  console.log(`${count} byte-exact files (${bytes.toLocaleString()} bytes) verified.`);
  return {count,bytes};
  } finally {await reader?.close();}
}
if(process.argv[1]?.endsWith('verify-snapshots.mjs')) await verifySnapshots(ROOT,{committed:process.argv.includes('--committed'),gitMode:process.argv.includes('--git')});
