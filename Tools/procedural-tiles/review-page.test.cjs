'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {render,buildingDemo,scriptJSON}=require('./review-page.cjs'),K=require('./core.cjs');
const catalog=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../Assets/Art/Production/procedural-tiles.json')));
test('offline page embeds the exact shared matcher and safe complete data',async()=>{
 const demo={seed:20261025,width:1,height:1,placements:[],checkedNeighborPairs:0};
 const html=await render(catalog,demo),matcher=fs.readFileSync(path.join(__dirname,'core.cjs'),'utf8');
 assert.ok(html.includes(matcher));assert.equal((html.match(/<script/g)||[]).length,3);
 assert.ok(!/fetch\s*\(|<script[^>]+src=/.test(html));
 const embedded=JSON.parse(html.match(/<script id="catalog-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
 assert.equal(embedded.tiles.length,catalog.tiles.length);
 const script=html.match(/<script>\n([\s\S]*?)<\/script>/)[1];assert.doesNotThrow(()=>new vm.Script(script));
 assert.equal(JSON.parse(scriptJSON({text:'</script><script>bad</script>'})).text,'</script><script>bad</script>');
 assert.ok(!scriptJSON({text:'</script>'}).includes('<'));
});
test('seeded building assembly only uses pairs accepted by the shared matcher',()=>{
 const demo=buildingDemo(catalog);assert.ok(demo);assert.equal(demo.pixelSeamGuarantee,false);
 assert.deepEqual(buildingDemo(catalog),demo);const byId=new Map(catalog.tiles.map(tile=>[tile.id,tile]));let pairs=0;
 for(const p of demo.placements)for(const [direction,dx,dy]of [['east',1,0],['south',0,1]]){
  if(p.x+dx>=demo.width||p.y+dy>=demo.height)continue;
  const neighbor=demo.placements[(p.y+dy)*demo.width+p.x+dx];assert.ok(K.check(byId.get(p.id),direction,byId.get(neighbor.id),catalog.policy).match);pairs++;
 }
 assert.equal(pairs,demo.checkedNeighborPairs);assert.equal(buildingDemo({...catalog,tiles:[]}),null);
});
