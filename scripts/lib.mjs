import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export const ROOT = fileURLToPath(new URL('../', import.meta.url));
export const REPO = 'cehinds/AI-Art';
export const GAMES = [
  { id: 'ff2', name: 'Final Fantasy II', branch: 'ff2' },
  { id: 'dungeon-crawler', name: 'Dungeon Crawler', branch: 'dungeon-crawler' },
  { id: 'ashenspire', name: 'AshenSpire', branch: 'ashenspire' },
  { id: 'dovakiin', name: 'Dovakiin', branch: 'Dovakiin' }
];
export const TYPES = [ ['tiles','Tiles'], ['weapons','Weapons'], ['characters','Characters'], ['creatures','Creatures'], ['environments','Environments'], ['props','Props'], ['effects','Effects'], ['animations','Animations'], ['ui','UI & icons'], ['concepts','Concept art'], ['source-sheets','Source sheets'], ['references','References'], ['other','Other assets'] ].map(([id,name]) => ({id,name}));
export const KINDS = [ ['production','Production'], ['concept','Concept'], ['source','Source'], ['reference','Reference'], ['review','Review'], ['archive','Archive'] ].map(([id,name]) => ({id,name}));
const EXTENSIONS = new Set('png jpg jpeg gif webp avif svg bmp tif tiff ico apng heic psd ase aseprite kra xcf ora ai eps pdf zip 7z rar tar gz glb gltf obj fbx blend stl dae mp4 webm mov m4v wav mp3 ogg flac aac ttf otf woff woff2'.split(' '));
export const isAsset = name => EXTENSIONS.has(path.posix.extname(name).slice(1).toLowerCase());
export const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
export const blobHash = bytes => crypto.createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
export function git(args, cwd = ROOT) { return execFileSync('git', args, {cwd, maxBuffer: 64*1024*1024}); }
export function tree(commit, cwd = ROOT) {
  return git(['ls-tree','-r','-z',commit],cwd).toString('utf8').split('\0').filter(Boolean).map(line => {
    const [header, ...parts] = line.split('\t');
    const [mode,type,blob] = header.split(' ');
    return {path:parts.join('\t'), mode, type, blob};
  });
}
export function indexTree(cwd=ROOT) {
  return git(['ls-files','--stage','-z'],cwd).toString('utf8').split('\0').filter(Boolean).map(line=>{
    const [header,...parts]=line.split('\t');const [mode,blob,stage]=header.split(' ');
    return {path:parts.join('\t'),mode,blob,stage};
  });
}
export async function files(dir, base = dir) {
  const result = [];
  for (const entry of await fs.readdir(dir,{withFileTypes:true})) {
    const full = path.join(dir,entry.name);
    if(entry.isDirectory()) result.push(...await files(full,base));
    else if(entry.isFile()) result.push(path.relative(base,full).split(path.sep).join('/'));
    else throw new Error(`Unsupported filesystem entry: ${full}`);
  }
  return result.sort();
}
export function classify(assetPath, hints = {}) {
  const value = `${assetPath} ${hints.category||''} ${hints.group||''} ${hints.label||''}`.toLowerCase();
  const ext = path.posix.extname(assetPath).toLowerCase();
  let kind = 'production';
  if(/^art\//i.test(assetPath) || /(^|\/)(artsource|originals|sources?|authoring)(\/|$)/i.test(assetPath)) kind='source';
  if(/concept|candidate/i.test(hints.status||'') || /(^|\/)(concepts?|conceptart)(\/|$)/i.test(assetPath)) kind='concept';
  if(/(^|\/)(review|reviews|screenshots?|previews?|contact-sheets?)(\/|$)/i.test(assetPath)) kind='review';
  if(/(^|\/)(contact[-_]sheet|preview|comparison|visual[-_]qa)([-_.]|$)/i.test(assetPath)) kind='review';
  if(/(^|\/)(references?)(\/|$)/i.test(assetPath)) kind='reference';
  if(/(^|\/)(archive|archives|revisions)(\/|$)/i.test(assetPath) || /\.(zip|7z|rar|tar|gz)$/.test(ext)) kind='archive';
  if(KINDS.some(x=>x.id===hints.catalogKind)) kind=hints.catalogKind;
  let type='other';
  if(/\.(gif|apng|mp4|webm|mov|m4v)$/.test(ext)) type='animations';
  else if(/(^|\/)(cards|card-components|ui-components)(\/|$)/.test(value) || /(^|\/)(ui|ui-kit)(\/|$)/.test(value)) type='ui';
  else if(/(^|\/)(enemy-poses|enemy-states|enemy-back-motion|enemy-back-proposals|enemies-expansion|enemies-unity)(\/|$)/.test(value)) type='creatures';
  else if(/(^|\/)(combat-effects|pose-effects|effects|special-effects)(\/|$)/.test(value)) type='effects';
  else if(/\/assets\/animations\//.test(value) || /(^|\/)(painted-outfits|poses|defeated-poses|readiness-poses|portraits)(\/|$)/.test(value) || /(^|\/)art\/card-portraits-/.test(value) || /outfits[^/]*\//.test(value) || /^art\/(bow-attack-source|twin-sword-reference[^/]*|unarmed-reference[^/]*|unarmed-magic[^/]*|player-attacks[^/]*|player-counter-sweep[^/]*|painted-combat[^/]*)\//.test(value)) type='characters';
  else if(/(^|[\/ _-])(weapons?|swords?|axes?|daggers?|bows?|spears?|staves|staff|maces?|shields?)([\/ ._-]|$)/.test(value)) type='weapons';
  else if(/(^|[\/ _-])(enemies|enemy|monsters?|creatures?|boss|skeever|wolf|icewraith|draugr|atronach|mirmulnir|bandit)([\/ ._-]|$)/.test(value)) type='creatures';
  else if(/(^|[\/ _-])(party|guest-party|ricard-party|firion|maria|guy|leon|ricard|minwu|leila|josef|gordon|npc|npcs|characters?|dovahkiin|lydia|aela|farkas|jzargo|erandur|balgruuf|farengar|adrianne|arcadia|hulda|guard|alchemist|bard|beastmaster|brawler|cleric|cryomancer|donut|guardian|necromancer|pyromancer|ranger|rogue|stormcaller)([\/ ._-]|$)/.test(value)) type='characters';
  else if(/(^|[\/ _-])(fx|effects?|spells?|attacks?|magic|special-effects)([\/ ._-]|$)/.test(value) || /room-?kit\/overlays\//.test(value)) type='effects';
  else if(/(^|[\/ _-])(ui|icons?|ui-kit|ui-status|hud|status|buttons?|fonts?)([\/ ._-]|$)/.test(value) || /\.(ttf|otf|woff2?)$/.test(ext)) type='ui';
  else if(/tiles?|terrain|biomes|roads|caverns|highlands|settlements|structures|\/(floors|walls|doors)\//.test(value)) type='tiles';
  else if(/(^|[\/ _-])(bg|backgrounds?|environments?|landscapes?|scenes?|maps?|map-detail|events?)([\/ ._-]|$)/.test(value)) type='environments';
  else if(/props?|world-objects|world-vehicles|transport|airship|canoe|sailboat|propeller-plane|equipment|gear|relics|flasks|chest|torch|tree|pine|anvil|shelf|banner|gate|stall|throne|wordwall|claw|sarc|barrow|tower|bed|sign/.test(value)) type='props';
  else if(/animations?|animated|walk|loop|\.(gif|apng|mp4|webm|mov)$/.test(value)) type='animations';
  if(type==='other' && kind==='source') type='source-sheets';
  if(kind==='reference') type='references';
  if(kind==='concept' && type==='other') type='concepts';
  if(TYPES.some(x=>x.id===hints.catalogType)) type=hints.catalogType;
  return {type,kind};
}
export function sourceLinks(commit, assetPath) {
  const encoded=assetPath.split('/').map(encodeURIComponent).join('/');
  return {downloadUrl:`https://raw.githubusercontent.com/${REPO}/${commit}/${encoded}`,sourceUrl:`https://github.com/${REPO}/blob/${commit}/${encoded}`};
}
export async function loadInventory(game, root=ROOT) {
  return JSON.parse(await fs.readFile(path.join(root,'Games',game.id,'_source.json'),'utf8'));
}
