const $ = id => document.getElementById(id);
const base = new URL(document.body.dataset.base || './', location.href);
const fixedGame = document.body.dataset.game && document.body.dataset.game !== 'all' ? document.body.dataset.game : null;
const pageSize = 48;
let data, filtered = [], state, previousFocus;
const labels = new Map();
const names = new Map();
const size = bytes => bytes >= 1048576 ? `${(bytes / 1048576).toFixed(1)} MB` : bytes >= 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${bytes} bytes`;
function text(tag, value, cls) { const node = document.createElement(tag); node.textContent = value; if (cls) node.className = cls; return node; }
function option(id, name) { const node = text('option', name); node.value = id; return node; }
function readState() {
  const p = new URLSearchParams(location.search);
  return { q: p.get('q') || '', game: fixedGame || p.get('game') || 'all', type: p.get('type') || 'all', kind: p.get('kind') || 'production', sort: p.get('sort') || 'name', page: Math.max(1, Number(p.get('page')) || 1) };
}
function writeState() {
  const p = new URLSearchParams();
  for (const [key, value] of Object.entries(state)) if (value && value !== ({game:fixedGame || 'all',type:'all',kind:'production',sort:'name',page:1,q:''})[key]) p.set(key, value);
  const query = p.toString();
  history.replaceState(null, '', location.pathname + (query ? '?' + query : '') + location.hash);
}
function normalizeState() {
  if (!data.games.some(g => g.id === state.game)) state.game = fixedGame || 'all';
  if (!data.types.some(t => t.id === state.type)) state.type = 'all';
  if (!data.kinds.some(k => k.id === state.kind)) state.kind = state.kind === 'all' ? 'all' : 'production';
  if (!['name','name-desc','size'].includes(state.sort)) state.sort = 'name';
  if (!Number.isFinite(state.page)) state.page = 1;
}
function preview(asset, detailed = false) {
  const box = text('div', '', detailed ? 'detail-preview-inner' : 'image-well');
  if (detailed && ['video','audio'].includes(asset.mediaType)) {
    const media = document.createElement(asset.mediaType);
    media.controls = true; media.preload = 'metadata'; media.src = asset.downloadUrl;
    box.append(media); return box;
  }
  if (asset.preview) {
    const img = document.createElement('img');
    const animated = ['gif','apng'].includes(asset.format) || (asset.format === 'webp' && asset.frames > 1);
    img.src = detailed && animated ? asset.downloadUrl : new URL(asset.preview, base).href;
    img.alt = detailed ? asset.name : '';
    img.loading = detailed ? 'eager' : 'lazy';
    img.decoding = 'async';
    if ((asset.width || 9999) <= 256 && (asset.height || 9999) <= 256) img.className = 'pixel';
    img.addEventListener('error', () => { box.replaceChildren(fallback(asset, 'Preview unavailable · open original')); }, { once:true });
    box.append(img);
  } else box.append(fallback(asset));
  return box;
}
function fallback(asset, message = 'Original file available') {
  const node = text('div', '', 'file-fallback');
  node.append(text('strong', String(asset.format || asset.path.split('.').pop()).toUpperCase()), text('span', message));
  return node;
}
function openAsset(asset) {
  previousFocus = document.activeElement;
  $('asset-name').textContent = asset.name;
  const node = preview(asset, true);
  $('asset-preview').replaceChildren(...node.childNodes);
  $('asset-context').textContent = `${names.get(asset.game)} · ${labels.get(asset.type) || asset.type} · ${labels.get(asset.kind) || asset.kind}${asset.variant ? ' · '+asset.variant : ''}`;
  const values = [['Format', String(asset.format || '').toUpperCase()], ['Dimensions', asset.width && asset.height ? `${asset.width} × ${asset.height} px` : 'Not applicable'], ['File size',size(asset.bytes)], ['Path',asset.path], ['Commit', asset.sourceCommit || data.games.find(g => g.id === asset.game)?.commit || ''], ['SHA-256',asset.sha256 || '']];
  $('asset-metadata').replaceChildren(...values.filter(([,v])=>v).flatMap(([k,v]) => [text('dt',k),text('dd',v)]));
  $('original-link').href = asset.downloadUrl;
  $('source-link').href = asset.sourceUrl;
  $('asset-dialog').showModal();
  history.replaceState(null, '', location.pathname + location.search + '#asset=' + encodeURIComponent(asset.id));
}
function closeAsset() { $('asset-dialog').close(); }
$('asset-dialog').addEventListener('close', () => { history.replaceState(null, '', location.pathname + location.search); previousFocus?.focus(); });
$('close-dialog').addEventListener('click', closeAsset);
$('asset-dialog').addEventListener('click', event => { if (event.target === $('asset-dialog')) { const r=event.target.getBoundingClientRect(); if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom) closeAsset(); } });
function setType(type) {
  state.type=type;
  const matches=data.assets.filter(a=>(state.game==='all'||a.game===state.game)&&(type==='all'||a.type===type));
  if(state.kind!=='all' && matches.length && !matches.some(a=>a.kind===state.kind)) state.kind='all';
  state.page=1; render();
}
function render() {
  normalizeState();
  const q = state.q.trim().toLocaleLowerCase();
  const scope = data.assets.filter(a => (state.game==='all'||a.game===state.game) && (state.kind==='all'||a.kind===state.kind) && (!q||`${a.name} ${a.path} ${names.get(a.game)} ${labels.get(a.type)}`.toLocaleLowerCase().includes(q)));
  filtered = scope.filter(a => state.type==='all'||a.type===state.type);
  const order = new Map(data.types.map((t,i)=>[t.id,i]));
  filtered.sort((a,b) => (state.type==='all' ? (order.get(a.type)||0)-(order.get(b.type)||0) : 0) || (state.sort==='size' ? b.bytes-a.bytes : (state.sort==='name-desc' ? -1:1)*a.name.localeCompare(b.name,undefined,{numeric:true})) || a.id.localeCompare(b.id));
  const pages = Math.max(1,Math.ceil(filtered.length/pageSize));
  state.page = Math.min(pages,Math.max(1,Math.floor(state.page)));
  for (const key of ['search','game','kind','sort','type-select']) $(key).value = state[{'search':'q','type-select':'type'}[key] || key];
  for (const button of $('types').querySelectorAll('button')) {
    const type = button.dataset.type;
    button.setAttribute('aria-pressed',String(state.type===type));
    button.querySelector('.count').textContent = (type==='all' ? scope.length : scope.filter(a=>a.type===type).length).toLocaleString();
  }
  $('gallery').replaceChildren();
  const shown = filtered.slice((state.page-1)*pageSize,state.page*pageSize);
  const grouped = new Map();
  for (const asset of shown) { if(!grouped.has(asset.type)) grouped.set(asset.type,[]); grouped.get(asset.type).push(asset); }
  for (const [type, assets] of grouped) {
    const section=text('section','','category');
    const heading=text('h3',labels.get(type)||type,'category-title');
    heading.append(text('span',`${filtered.filter(a=>a.type===type).length.toLocaleString()} assets`));
    const grid=text('div','','asset-grid');
    for(const asset of assets) {
      const button=text('button','','asset'); button.type='button'; button.dataset.asset=asset.id;
      button.setAttribute('aria-label',`${asset.name} · ${names.get(asset.game)} · View details`);
      button.append(preview(asset),text('span',asset.name,'asset-name'),text('span',`${names.get(asset.game)} · ${labels.get(asset.type)||asset.type}`,'asset-context'));
      if(asset.variant)button.append(text('span',asset.variant,'asset-variant'));
      button.addEventListener('click',()=>openAsset(asset)); grid.append(button);
    }
    section.append(heading,grid); $('gallery').append(section);
  }
  $('gallery').setAttribute('aria-busy','false');
  $('results-title').textContent=state.type==='all'?'Assets':labels.get(state.type);
  $('result-count').textContent=`${filtered.length.toLocaleString()} results · ${data.assets.length.toLocaleString()} files in the library`;
  $('empty').hidden=filtered.length>0;
  const game=data.games.find(g=>g.id===state.game);
  $('empty-copy').textContent=game && !data.assets.some(a=>a.game===game.id) ? `${game.name}'s gallery is ready. Its source branch does not contain artwork yet; assets will appear when that branch is added to the catalog.` : 'Try a different asset type, collection or search. Choose All collections to include source sheets, review images, references and archives.';
  $('previous').disabled=state.page<=1; $('next').disabled=state.page>=pages;
  $('page-label').textContent=`Page ${state.page} of ${pages}`;
  writeState();
}
async function init() {
  const response=await fetch(new URL('catalog.json',base));
  if(!response.ok) throw Error(`Catalog request failed (${response.status})`);
  data=await response.json();
  for(const x of [...data.types,...data.kinds]) labels.set(x.id,x.name);
  for(const game of data.games) { names.set(game.id,game.name); $('game').append(option(game.id,game.name)); }
  $('kind').replaceChildren(option('all','All collections'),...data.kinds.map(k=>option(k.id,k.name)));
  for(const item of [{id:'all',name:'All types'},...data.types]) {
    const button=text('button'); button.type='button';button.dataset.type=item.id;
    button.append(text('span',item.name),text('span','','count'));button.addEventListener('click',()=>setType(item.id));$('types').append(button);
    if(item.id!=='all')$('type-select').append(option(item.id,item.name));
  }
  const current=fixedGame||'all';document.querySelector(`[data-nav="${current}"]`)?.setAttribute('aria-current','page');
  if(fixedGame){$('title').textContent=names.get(fixedGame)||fixedGame;$('intro').textContent='Browse the complete art collection by asset type.';$('game').disabled=true;}
  $('snapshot').textContent=`Source snapshots: ${data.games.map(g=>`${g.name} ${g.commit.slice(0,7)}`).join(' · ')}`;
  state=readState();render();
  let searchTimer;
  $('search').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{state.q=$('search').value;state.page=1;render();},120);});
  for(const key of ['game','kind','sort'])$(key).addEventListener('change',()=>{state[key]=$(key).value;state.page=1;render();});
  $('type-select').addEventListener('change',()=>setType($('type-select').value));
  $('filters').addEventListener('submit',event=>event.preventDefault());
  $('reset').addEventListener('click',()=>{state={q:'',game:fixedGame||'all',type:'all',kind:'production',sort:'name',page:1};render();});
  for(const [id,step] of [['previous',-1],['next',1]])$(id).addEventListener('click',()=>{state.page+=step;render();$('results-title').scrollIntoView({block:'start'});});
  window.addEventListener('popstate',()=>{state=readState();render();});
  if(location.hash.startsWith('#asset=')){const asset=data.assets.find(a=>a.id===decodeURIComponent(location.hash.slice(7)));if(asset&&(!fixedGame||asset.game===fixedGame))openAsset(asset);}
}
init().catch(error=>{$('result-count').textContent='The library could not be loaded.';$('gallery').setAttribute('aria-busy','false');$('empty').hidden=false;$('empty-copy').textContent='Reload the page, or browse the original collection on GitHub using the link below.';$('reset').hidden=true;console.error(error);});
