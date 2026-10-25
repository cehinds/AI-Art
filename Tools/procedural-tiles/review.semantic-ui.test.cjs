'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const K=require('./core.cjs'),T=require('./terrain.cjs'),catalog=require('../../Assets/Art/Production/procedural-tiles.json');
// Minimal DOM doubles exercise handlers in Node. This is functional integration
// coverage, not browser rendering or screenshot evidence.
class Element{
 constructor(id){this.id=id;this.value='';this.options=[];this.handlers={};this.style={};this.dataset={};this.children=[];this.innerHTML='';this.textContent='';this.disabled=false;this.hidden=false;}
 add(option){this.options.push(option);if(this.options.length===1)this.value=option.value;}
 addEventListener(name,handler){this.handlers[name]=handler;}
 replaceChildren(...children){this.children=children;this.innerHTML='';this.textContent='';}
 append(...children){this.children.push(...children);}
 click(){this.clicked=true;this.handlers.click?.();}
}
function setup(){
 const nodes=new Map(),get=id=>{if(!nodes.has(id))nodes.set(id,new Element(id));return nodes.get(id);};
 for(const id of ['terrain','biome','role'])get(id).add({value:''});
 get('terrain-seed').value='20261025';get('demo-preset').value='path';get('request-model').value='area-corner16';get('request-mask').value='1';
 let exportedBlob,download;
 const context=vm.createContext({catalog,TileTerrain:T,TileMatcher:K,$:get,byId:new Map(catalog.tiles.map(tile=>[tile.id,tile])),esc:value=>String(value??''),image:tile=>tile.path,visibleLimit:84,renderLibrary(){},Option:function(text,value){return {text,value};},Blob,URL:{createObjectURL(blob){exportedBlob=blob;return 'blob:test';},revokeObjectURL(){}},setTimeout:handler=>handler(),document:{createElement(tag){const element=new Element(tag);if(tag==='a')download=element;return element;}}});
 vm.runInContext(fs.readFileSync(path.join(__dirname,'review.semantic-ui.js'),'utf8').replaceAll('__TERRAIN_HASH__','unit-test-hash'),context);
 return {get,context,exported:()=>({blob:exportedBlob,download})};
}
test('semantic filters distinguish area corners from route ends and search aliases',()=>{
 const {get,context}=setup(),corner=catalog.tiles.find(tile=>tile.id==='batch01:terrain.path-nw');
 assert.ok(get('role').options.some(option=>option.value==='end'));
 get('terrain').value='soil-path';assert.ok(context.matchesSemantics(corner));
 get('biome').value='temperate';assert.ok(context.matchesSemantics(corner));get('biome').value='snow';assert.ok(!context.matchesSemantics(corner));get('biome').value='';
 get('role').value='end';assert.ok(!context.matchesSemantics(corner));assert.equal(catalog.tiles.filter(tile=>context.matchesSemantics(tile)).length,0);
 assert.match(context.emptySemanticResults(),/No authored end tiles/);assert.match(context.emptySemanticResults(),/not a substitute/);
 context.resetSemanticFilters();assert.ok(context.matchesSemantics(corner));assert.match(context.semanticText(corner),/soil-path/);
 const inspector=context.semanticInspector(corner);assert.match(inspector,/area-corner16/);assert.match(inspector,/bit flags 0 0 1 0/);assert.match(inspector,/does not imply a route bend/);
});
test('demo handlers use the shared generator and export its exact placements',async()=>{
 const {get,exported}=setup();
 for(const preset of ['path','grass','snow']){
  get('demo-preset').value=preset;get('generate-terrain').click();const expected=T.generate(catalog,{kind:'demo',preset,seed:20261025});
  assert.ok(expected.ok);assert.match(get('terrain-demo-status').textContent,new RegExp(`${expected.checkedNeighborPairs} neighboring pairs`));
  assert.equal((get('terrain-demo-map').innerHTML.match(/data-tile=/g)||[]).length,expected.placements.length);assert.equal(get('export-terrain').disabled,false);
  get('export-terrain').click();const {blob,download}=exported();assert.deepEqual(JSON.parse(await blob.text()),expected);assert.match(download.download,new RegExp(`ff2-${preset}-seed-20261025`));
 }
 get('demo-preset').value='unsupported-preset';get('generate-terrain').click();assert.match(get('terrain-demo-status').textContent,/Generation stopped: unsupported-demo/);assert.equal(get('export-terrain').disabled,true);assert.equal(get('terrain-demo-map').innerHTML,'');
 get('terrain-seed').value='';get('generate-terrain').click();assert.match(get('terrain-demo-status').textContent,/whole-number seed/);assert.equal(get('export-terrain').disabled,true);
});
test('shape requests surface missing route masks and terrain coverage gaps without fallback',()=>{
 const {get}=setup();get('request-family').value='batch01-path';get('request-terrain').value='path';get('request-model').value='route4';get('request-mask').value='1';get('check-mask').click();
 assert.equal(get('mask-result').className,'demostatus reject');assert.match(get('mask-result').children[0].textContent,/unsupported-mask/);assert.match(get('mask-result').children[0].textContent,/No fallback/);
 get('request-model').value='area-corner16';get('request-mask').value='4';get('check-mask').click();assert.equal(get('mask-result').className,'demostatus match');assert.equal(get('mask-result').children[1].dataset.tile,'batch01:terrain.path-nw');
 get('coverage-terrain').value='path';get('coverage-terrain').handlers.change();assert.match(get('terrain-coverage').innerHTML,/9\/16 masks authored/);assert.match(get('terrain-coverage').innerHTML,/inner-ne/);assert.match(get('terrain-coverage').innerHTML,/route4/);
});
