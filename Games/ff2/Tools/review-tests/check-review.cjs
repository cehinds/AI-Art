/* Run from any directory: node Tools/review-tests/check-review.cjs
 * No packages, network, browser, or production game save writes.
 * --write-svg regenerates the editable review wireframes from review.js.
 */
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
const source=fs.readFileSync(path.join(root,'Review/review.js'),'utf8');
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{id,innerHTML:'',textContent:'',value:'',attrs:{},listeners:{},setAttribute(k,v){this.attrs[k]=v;},addEventListener(k,fn){this.listeners[k]=fn;},getBoundingClientRect(){return {width:512};},focus(){},click(){},classList:{toggle(){}},closest(){return null;}});return elements.get(id);}
const context={console,Blob,URL,setTimeout,document:{getElementById:element,querySelectorAll(){return [];},addEventListener(k,v){this[k]=v;},createElement(){return element('download');}},window:{addEventListener(){}},localStorage:{getItem(){return '{}';},setItem(k,v){assert.equal(k,'ffii-review-notes');JSON.parse(v);}}};
vm.createContext(context);
vm.runInContext(source+'\nglobalThis.reviewApi={screens,state,svgFor,go,action,notes};',context);
const {screens,state,svgFor,go,action}=context.reviewApi;
let checks=0;function check(test){test();checks++;}
check(()=>assert.equal(screens.length,8));
screens.forEach((screen,i)=>check(()=>{go(i);assert.equal(element('screen-title').textContent,screen.name);assert.ok(element('screen').innerHTML.includes('viewBox="0 0 256 240"'));assert.ok(element('screen-controls').innerHTML.includes('data-action'));assert.ok(svgFor(i).includes('<title>'));}));
check(()=>{go(0);action('talk');assert.equal(state.screen,1);action('learn');assert.equal(state.learned,true);action('keyword-mythril');action('ask');assert.match(element('feedback').textContent,/Mythril/);action('back');assert.equal(state.screen,0);});
check(()=>{action('menu');assert.equal(state.screen,2);action('inventory');assert.equal(state.screen,3);action('item-armor');action('character-maria');action('equip');assert.match(element('feedback').textContent,/Maria equips Leather armor/);action('menu');action('progression');action('skill');assert.match(element('feedback').textContent,/use-based growth/);});
check(()=>{go(5);action('target-a');assert.match(element('feedback').textContent,/Choose Fight or Magic/);action('fight');assert.equal(state.battle,'fight');action('target-a');assert.equal(state.battle,'queued');assert.match(element('feedback').textContent,/Attack → Goblin A/);action('battle-back');assert.equal(state.battle,'command');action('magic');action('target-b');assert.match(element('feedback').textContent,/Fire → Goblin B/);action('battle-back');});
check(()=>{go(6);for(let i=0;i<15;i++)action('quantity-up');assert.equal(state.quantity,9);for(let i=0;i<15;i++)action('quantity-down');assert.equal(state.quantity,1);action('item-sword');action('quantity-up');action('purchase');assert.match(element('feedback').textContent,/total 200 G/);assert.equal(state.shop,true);});
check(()=>{go(7);action('slot-2');action('load-preview');assert.match(element('feedback').textContent,/empty/);action('slot-1');action('load-preview');assert.match(element('feedback').textContent,/Altair/);action('save-preview');assert.match(element('feedback').textContent,/No save written/);});
check(()=>{go(0);action('move-up');assert.equal(state.y,112);action('move-down');assert.equal(state.y,120);});
check(()=>{go(0);element('screen').listeners.keydown({key:'ArrowDown',target:element('screen'),preventDefault(){}});assert.equal(state.selection,1);element('screen').listeners.keydown({key:'Enter',target:element('screen'),preventDefault(){}});assert.match(element('feedback').textContent,/marker moved/);});
check(()=>{go(3);context.document.keydown({key:'Escape',target:{tagName:'DIV'},preventDefault(){}});assert.equal(state.screen,2);context.document.keydown({key:'Escape',target:{tagName:'DIV'},preventDefault(){}});assert.equal(state.screen,0);});
check(()=>{go(4);element('notes').value='Review growth language';element('notes').listeners.input();go(0);go(4);assert.equal(element('notes').value,'Review growth language');element('reset-demo').listeners.click();assert.equal(state.screen,0);assert.equal(context.reviewApi.notes.progression,'Review growth language');});
check(()=>{go(0);element('previous').listeners.click();assert.equal(state.screen,7);element('next').listeners.click();assert.equal(state.screen,0);});
// Static exports deliberately use the initial state, independent of tested interactions.
Object.assign(state,{screen:0,selection:0,battle:'command',keyword:'Wild Rose',learned:false,character:'Firion',item:'Broadsword',quantity:1,slot:1,shop:false,x:128,y:119});
const wirePath=path.join(root,'Review/wireframes');
if(process.argv.includes('--write-svg')){
  fs.mkdirSync(wirePath,{recursive:true});
  screens.forEach((s,i)=>fs.writeFileSync(path.join(wirePath,`${String(i+1).padStart(2,'0')}-${s.id}.svg`),svgFor(i)+'\n'));
  const width=1144,height=650;
  const cells=screens.map((s,i)=>{const x=24+(i%4)*280,y=74+Math.floor(i/4)*282;return `<text x="${x}" y="${y-12}" fill="#d2b17a" font-family="monospace" font-size="10">${String(i+1).padStart(2,'0')} / ${s.name.replaceAll('&','&amp;')}</text><svg x="${x}" y="${y}" width="256" height="240" viewBox="0 0 256 240">${svgFor(i).replace(/^<svg[^>]*>/,'').replace(/<\/svg>$/,'')}</svg>`;}).join('');
  fs.writeFileSync(path.join(wirePath,'contact-sheet.svg'),`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="${width}" height="${height}" fill="#0c1420"/><text x="24" y="28" fill="#e9e5d6" font-family="Georgia,serif" font-size="19">Final Fantasy II / Interface studies</text><text x="24" y="46" fill="#91a0ae" font-family="monospace" font-size="9">PROVISIONAL SCHEMATICS · 256 × 240 SQUARE PIXELS · ILLUSTRATIVE DATA</text>${cells}<text x="24" y="636" fill="#91a0ae" font-family="monospace" font-size="9">Editable SVG sources. Review original-layout fidelity against the reference ledger before production.</text></svg>\n`);
}
check(()=>{screens.forEach((s,i)=>{const file=path.join(wirePath,`${String(i+1).padStart(2,'0')}-${s.id}.svg`);assert.ok(fs.existsSync(file),file);assert.equal(fs.readFileSync(file,'utf8').trim(),svgFor(i));});});
const html=fs.readFileSync(path.join(root,'Review/index.html'),'utf8');
check(()=>{for(const match of html.matchAll(/(?:src|href)="([^"]+)"/g)){const link=match[1];if(link.startsWith('#')){assert.ok(html.includes(`id="${link.slice(1)}"`),link);}else if(!/^https?:/.test(link)){assert.ok(fs.existsSync(path.resolve(root,'Review',link)),`Missing local link: ${link}`);}}});
console.log(`PASS: ${checks} review checks, 8 screen renders, interaction flows, keyboard, notes, SVG sources, and local links.`);
console.log('These are source/DOM-model checks. Browser rendering and actual assistive-technology behavior are not covered.');
