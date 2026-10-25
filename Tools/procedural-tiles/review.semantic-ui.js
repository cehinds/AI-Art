// Inlined by review-page.cjs after the unchanged matcher and terrain module.
function semanticText(tile){return JSON.stringify({terrain:tile.terrain,biome:tile.biome,usage:tile.usage,shape:tile.shape,model:tile.topology?.model,connections:tile.topology?.connections,cap:tile.topology?.cap}).toLowerCase();}
function materialNames(tile){return [...new Set([tile.terrain?.primary,...(tile.terrain?.aliases||[]),...(tile.terrain?.materials||[])].filter(Boolean))];}
function semanticRole(tile,role){
 if(tile.shape?.kind===role)return true;
 if(tile.topology?.model!=='route4')return false;
 const connections=tile.topology.connections||[];
 if(role==='end')return connections.length===1;
 if(role==='junction')return connections.length>=3;
 if(role==='straight')return connections.length===2&&connections.includes(TileMatcher.opposite[connections[0]]);
 if(role==='bend')return connections.length===2&&!connections.includes(TileMatcher.opposite[connections[0]]);
 return false;
}
function matchesSemantics(tile){return (!$('terrain').value||materialNames(tile).includes($('terrain').value))&&(!$('biome').value||(tile.biome||[]).includes($('biome').value))&&(!$('role').value||semanticRole(tile,$('role').value));}
function resetSemanticFilters(){for(const id of ['terrain','biome','role'])$(id).value='';}
function emptySemanticResults(){return $('role').value==='end'?'<p class="empty">No authored end tiles match these filters. An end requires a route opening and a sealed cap; an area corner is not a substitute. Check the terrain coverage gaps below.</p>':'<p class="empty">No authored tiles match these filters. This may be a real coverage gap; check terrain coverage below or reset the filters.</p>';}
function semanticInspector(tile){
 const topology=tile.topology||{},chips=[...materialNames(tile),...(tile.biome||[]),...(tile.usage||[]),tile.shape?.kind,tile.shape?.orientation].filter(Boolean);
 const mask=value=>Number.isInteger(value)?`${value} · bit flags ${[0,1,2,3].map(bit=>(value>>bit)&1).join(' ')}`:'Not applicable';
 return `<h3>Terrain semantics</h3><div class="chips">${[...new Set(chips)].map(chip=>`<span class="chip">${esc(chip)}</span>`).join('')}</div><div class="topology"><div><strong>Model</strong>${esc(topology.model||'Not authored')}</div><div><strong>Route openings</strong>${esc(topology.connections?.length?topology.connections.join(', '):'None declared')}</div><div><strong>Sealed end cap</strong>${esc(topology.cap||'None declared')}</div><div><strong>Corner mask · NW NE SE SW</strong>${esc(mask(topology.cornerMask))}<br>Bits: NW=1 · NE=2 · SE=4 · SW=8</div><div><strong>Route mask · N E S W</strong>${esc(mask(topology.routeMask))}<br>Bits: N=1 · E=2 · S=4 · W=8</div><div><strong>Transition</strong>${tile.transition?esc(`${tile.transition.from} → ${tile.transition.to}`):'None declared'}</div></div><p class="meta">${topology.model==='area-corner16'?'Area-corner model: corner orientation does not imply a route bend, end or junction.':topology.model==='route4'?'Route model: openings and caps describe the independent connection graph.':'Use the declared model and shared selector; no route role is inferred from the filename.'}</p>`;
}
const terrainCoverage=TileTerrain.coverage(catalog.tiles);
let generatedTerrainDemo=null;
let generatedTerrainPreset='';
function addOptions(id,values){for(const value of [...new Set(values.filter(Boolean))].sort())$(id).add(new Option(value,value));}
addOptions('terrain',catalog.tiles.flatMap(materialNames));addOptions('biome',catalog.tiles.flatMap(tile=>tile.biome||[]));addOptions('role',[...catalog.tiles.map(tile=>tile.shape?.kind),'end','bend','junction','straight']);
addOptions('coverage-terrain',terrainCoverage.byTerrain.map(item=>item.terrain));addOptions('request-family',catalog.tiles.map(tile=>tile.family));addOptions('request-terrain',terrainCoverage.byTerrain.map(item=>item.terrain));
if(terrainCoverage.byTerrain.some(item=>item.terrain==='path')){$('coverage-terrain').value='path';$('request-terrain').value='path';}
if(catalog.tiles.some(tile=>tile.family==='batch01-path'))$('request-family').value='batch01-path';
$('request-model').value='route4';
for(const id of ['terrain','biome','role'])$(id).addEventListener('change',()=>{visibleLimit=84;renderLibrary();});
function showCoverage(){
 const terrain=$('coverage-terrain').value,entry=terrainCoverage.byTerrain.find(item=>item.terrain===terrain),gaps=terrainCoverage.gaps.filter(gap=>gap.terrain===terrain);
 if(!entry){$('terrain-coverage').textContent='No authored terrain coverage record.';return;}
 const kits=[...(entry.area||[]),...(entry.route||[])];
 $('terrain-coverage').innerHTML=`<p class="meta">${esc(terrain)} · ${entry.fillVariants||0} fill variants · ${gaps.length} reported gap records.</p>${kits.map(kit=>`<div class="gapkit"><strong>${esc(kit.family)} · ${esc(kit.model)}</strong><p>${kit.supportedMasks.length}/16 masks authored. Supported masks: ${esc(kit.supportedMasks.join(', ')||'none')}.</p><p class="${kit.missingMasks.length?'warning':''}">Missing masks: ${esc(kit.missingMasks.join(', ')||'none')}<br>Missing roles: ${esc((kit.missingRoles||[]).join(', ')||'none')}</p></div>`).join('')}${gaps.map(gap=>`<div class="gapkit warning"><strong>${esc(gap.model)} · ${esc(gap.reason)}</strong><p>${gap.family?esc(gap.family)+' · ':''}Missing roles: ${esc((gap.missingRoles||[]).join(', ')||'not specified')}<br>Missing masks: ${esc((gap.missingMasks||[]).join(', ')||'not specified')}</p></div>`).join('')}${!kits.length&&!gaps.length?'<p class="empty">No mask model is authored for this terrain.</p>':''}`;
}
function terrainSeed(){const value=$('terrain-seed').value.trim(),seed=Number(value);return value&&Number.isSafeInteger(seed)?seed:null;}
function generateTerrain(){
 const seed=terrainSeed();if(seed===null){generatedTerrainDemo=null;$('export-terrain').disabled=true;$('terrain-demo-map').replaceChildren();$('terrain-demo-status').className='demostatus reject';$('terrain-demo-status').textContent='Enter a whole-number seed.';return;}
 const intent={kind:'demo',preset:$('demo-preset').value,seed},result=TileTerrain.generate(catalog,intent);generatedTerrainDemo=result;generatedTerrainPreset=intent.preset;
 $('terrain-demo-map').replaceChildren();$('export-terrain').disabled=!result.ok;$('terrain-demo-missing').hidden=!(result.missingRequests?.length);
 $('terrain-missing-list').textContent=JSON.stringify(result.missingRequests||[],null,2);$('terrain-demo-status').className='demostatus '+(result.ok?'match':'reject');
 if(!result.ok){$('terrain-demo-status').textContent=`Generation stopped: ${result.reason}. No fallback tiles were inserted.`;return;}
 $('terrain-demo-status').textContent=`Seed ${seed} · ${result.width} × ${result.height} · ${result.checkedNeighborPairs} neighboring pairs passed the shared matcher. Logical proof only; inspect the pixels.`;
 $('terrain-demo-map').style.gridTemplateColumns=`repeat(${result.width},minmax(0,1fr))`;
 $('terrain-demo-map').innerHTML=result.placements.map(placement=>{const tile=byId.get(placement.id);return `<button data-tile="${esc(tile.id)}" title="${esc(tile.id)}" aria-label="Inspect terrain map tile ${placement.x},${placement.y}: ${esc(tile.id)}"><img src="${image(tile)}" alt=""></button>`;}).join('');
}
function checkMask(){
 const mask=Number($('request-mask').value);if(!Number.isInteger(mask)||mask<0||mask>15){$('mask-result').className='demostatus reject';$('mask-result').textContent='Enter a mask from 0 to 15.';return;}
 const intent={family:$('request-family').value,terrain:$('request-terrain').value,model:$('request-model').value,mask},result=TileTerrain.select(catalog,intent,terrainSeed()??1);
 $('mask-result').className='demostatus '+(result.ok?'match':'reject');$('mask-result').replaceChildren();
 const message=document.createElement('p');message.textContent=result.ok?`Supported shape: ${result.tileId}`:`Unsupported request: ${result.reason}. Available masks: ${(result.availableMasks||[]).join(', ')||'none'}. No fallback selected.`;$('mask-result').append(message);
 if(result.ok){const button=document.createElement('button');button.type='button';button.dataset.tile=result.tileId;button.textContent='Inspect selected tile';$('mask-result').append(button);}
}
$('coverage-terrain').addEventListener('change',showCoverage);$('generate-terrain').addEventListener('click',generateTerrain);$('check-mask').addEventListener('click',checkMask);
$('export-terrain').addEventListener('click',()=>{if(!generatedTerrainDemo?.ok)return;const blob=new Blob([JSON.stringify(generatedTerrainDemo,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=`ff2-${generatedTerrainPreset}-seed-${generatedTerrainDemo.seed}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
$('terrain-hash').textContent='Shared terrain selector SHA-256: __TERRAIN_HASH__';showCoverage();generateTerrain();
