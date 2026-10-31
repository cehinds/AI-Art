let sharp;
try { sharp = require('sharp'); }
catch { sharp = require('C:/Users/const/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'); }
const path=require('path');
const root=path.resolve(__dirname,'..');
const W=1140,H=1160,bg='#111820',card='#202e38',ink='#edf3f7',soft='#b8c5ce',accent='#9ed4ff';
function esc(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
(async()=>{
 const layers=[];
 layers.push({input:Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="${bg}"/><text x="28" y="42" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="27" font-weight="700">Shops and temple · FFII PR evidence and V1 proposals</text><text x="28" y="70" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="14">Only the weapon row has a local actual PR interior reference. Other four rooms are clearly marked proposals.</text><text x="28" y="94" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="13">Images are fitted without distortion. The 3× room proofs and gameplay crop are not shown at matching scale.</text></svg>`),left:0,top:0});
 const y=112, topH=374;
 layers.push({input:Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect x="20" y="${y}" width="1100" height="${topH}" rx="8" fill="${card}"/><text x="38" y="${y+28}" fill="${accent}" font-family="Segoe UI,Arial,sans-serif" font-size="19" font-weight="700">Weapon shop · Tobul reference compared with V1 proposal</text><text x="42" y="${y+56}" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600">ORIGINAL FFII PIXEL REMASTER · Tobul smithy screenshot</text><text x="600" y="${y+56}" fill="${ink}" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600">NEW ASSET V1 · proposed weapon room proof</text><text x="42" y="${y+360}" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="12">Observed: red floor, mounted weapons, merchant behind L-counter.</text><text x="600" y="${y+360}" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="12">Motifs retained; room layout and artwork are a new proposal.</text></svg>`),left:0,top:0});
 const ref=path.join(root,'crops/tobul-weapon-shop.png'),weapon=path.join(root,'comparison-inputs/shop-v1/weapon-3x.png');
 for(const [file,x,w,h] of [[ref,40,520,282],[weapon,598,520,282]]){const image=await sharp(file).resize(w,h,{fit:'inside',kernel:'nearest',background:bg}).png().toBuffer();const m=await sharp(image).metadata();layers.push({input:image,left:x+Math.floor((w-m.width)/2),top:y+66+Math.floor((282-m.height)/2)});}
 const items=[['armor','ARMOR','V1 proposal · armor mannequins'],['item','ITEM','V1 proposal · potion and supply shelves'],['magic','MAGIC','V1 proposal · spell books and blue-robed clerk'],['temple','TEMPLE','V1 proposal · sanctuary altar and seating']];
 for(let i=0;i<items.length;i++){
  const [id,label,desc]=items[i],col=i%2,row=Math.floor(i/2),x=20+col*555,yy=500+row*320;
  layers.push({input:Buffer.from(`<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg"><rect x="${x}" y="${yy}" width="540" height="300" rx="8" fill="${card}"/><text x="${x+18}" y="${yy+27}" fill="${accent}" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="700">${esc(label)} · PROPOSED</text><text x="${x+18}" y="${yy+49}" fill="${soft}" font-family="Segoe UI,Arial,sans-serif" font-size="12">${esc(desc)}</text></svg>`),left:0,top:0});
  const file=path.join(root,`comparison-inputs/shop-v1/${id}-3x.png`);const im=await sharp(file).resize(500,230,{fit:'inside',kernel:'nearest',background:bg}).png().toBuffer();const m=await sharp(im).metadata();layers.push({input:im,left:x+20+Math.floor((500-m.width)/2),top:yy+58+Math.floor((230-m.height)/2)});
 }
 const out=path.join(root,'boards/shop-and-temple-reference-vs-v1.png');await sharp({create:{width:W,height:H,channels:3,background:bg}}).composite(layers).png().toFile(out);console.log(out);
})();
