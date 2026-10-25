'use strict';
// Optional local QA: Browser plugin not available; use installed Chrome with
// Playwright. No server or network is needed for this file:// review flow.
const fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),{pathToFileURL}=require('node:url');
let playwright;try{playwright=require('playwright')}catch{playwright=require(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'))}
const K=require('./core.cjs'),root=path.resolve(__dirname,'../..'),folder=path.join(root,'Review/procedural-tiles');
const evidence=process.env.TILE_REVIEW_QA_DIR||path.join(os.tmpdir(),'ff2-tile-review-qa');
(async()=>{
 const catalog=JSON.parse(await fs.readFile(path.join(root,'Assets/Art/Production/procedural-tiles.json'),'utf8'));
 await fs.mkdir(evidence,{recursive:true});
 const browser=await playwright.chromium.launch({headless:true,channel:process.env.PLAYWRIGHT_CHANNEL||'chrome'});
 const page=await browser.newPage({viewport:{width:1440,height:1100},deviceScaleFactor:1});const errors=[],network=[];
 page.on('pageerror',error=>errors.push(error.message));page.on('console',message=>{if(message.type()==='error')errors.push(message.text())});page.on('request',request=>{if(/^https?:/.test(request.url()))network.push(request.url())});
 try{
  await page.goto(pathToFileURL(path.join(folder,'index.html')).href);await page.waitForSelector('#inspector img');
  assert.equal(await page.title(),'FFII · Tile connection lab');assert.equal(await page.locator('#metrics .metric strong').first().textContent(),String(catalog.tiles.length));
  assert.equal(await page.locator('#inspector .side').count(),4);assert.ok(await page.locator('#inspector img').evaluate(image=>image.complete&&image.naturalWidth>0));
  const id=await page.locator('#inspector .selectedhead code').textContent(),selected=catalog.tiles.find(tile=>tile.id===id);
  const expected=Object.keys(K.opposite).map(direction=>`${catalog.tiles.filter(other=>K.check(selected,direction,other,catalog.policy).match).length} candidates`);
  assert.deepEqual(await page.locator('#neighbors h3 .count').allTextContents(),expected);
  await page.locator('#family').selectOption('stone-building-expansion04');assert.equal(await page.locator('#tiles button').count(),catalog.tiles.filter(tile=>tile.family==='stone-building-expansion04').length);
  await page.locator('#search').fill('outer-nw');assert.equal(await page.locator('#tiles button').count(),1);await page.locator('#reset').click();
  await page.locator('#status').selectOption('blocked');const blocked=catalog.tiles.find(tile=>tile.state==='blocked');await page.locator('#search').fill(blocked.id);await page.locator('#tiles button').first().click();
  assert.deepEqual(await page.locator('#neighbors h3 .count').allTextContents(),['0 candidates','0 candidates','0 candidates','0 candidates']);
  assert.match(await page.locator('#compare-result').textContent(),/Rejected/);
  const superseded=catalog.tiles.filter(tile=>tile.supersededBy&&catalog.tiles.some(other=>other.id===tile.supersededBy));
  for(const previous of superseded){await page.locator('#search').fill(previous.id);await page.locator('#tiles button').first().click();assert.deepEqual(await page.locator('#neighbors h3 .count').allTextContents(),['0 candidates','0 candidates','0 candidates','0 candidates']);await page.getByRole('button',{name:'Inspect corrected tile'}).click();assert.equal(await page.locator('#inspector .selectedhead code').textContent(),previous.supersededBy);assert.match(await page.locator('#inspector .pill').textContent(),/Modeled candidate/);}
  await page.locator('#reset').click();await page.locator('#search').fill(selected.id);await page.locator('#tiles button').first().click();await page.locator('#reset').click();
  await page.locator('#compare-tile').selectOption(blocked.id);assert.match(await page.locator('#compare-result').textContent(),/Rejected/);
  await page.screenshot({path:path.join(evidence,'browser-desktop.png')});
  assert.ok(await page.locator('#building-map img').count()>0);await page.locator('#building-example').screenshot({path:path.join(evidence,'browser-building-map.png')});
  await page.setViewportSize({width:390,height:1000});await page.locator('#inspector').scrollIntoViewIfNeeded();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Mobile page must not overflow horizontally');
  await page.screenshot({path:path.join(evidence,'browser-mobile.png')});
  assert.deepEqual(network,[]);assert.deepEqual(errors,[]);
  const report={browser:'Installed Chrome through Playwright',browserPlugin:'not available',protocol:'file:',tiles:catalog.tiles.length,supersededLinksChecked:superseded.length,evidence,checks:['local PNG rendered','four side profiles','neighbor counts equal shared matcher','family filter','text search','blocked tile yields zero neighbors','rejected pair explanation','seeded building map','desktop and mobile screenshots','no horizontal overflow','no HTTP requests','no page/console errors']};
  console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});
