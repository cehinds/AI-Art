from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import hashlib,json,shutil
OUT=Path(__file__).resolve().parent
GAME=Path('C:/repos/AI-Remake-FF2');ART=Path('C:/repos/AI-Art-FF2')
SOURCES={
'pr-hq-layout':('Logs/interior-reference-20261029/hq.jpg','https://www.soloplayguide.com/games/final-fantasy-ii-pixel-remaster/walkthrough/01-altair','Annotated sepia hideout map; layout only, not color gameplay.'),
'pr-smithy':('Logs/interior-reference-20261029/tobul.webp','https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/walkthrough/salamand-and-semitt-falls/tobul-960w.webp','Direct PR Tobul interior capture, platform/build unknown.'),
'pr-refuge':('Logs/interior-reference-20261029/scott.webp','https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn/scott-gives-you-ring-960w.webp','Direct PR Scott room capture, platform/build unknown.'),
'pr-hilda':('References/Parity20261025/rpgfan-ffii-pr-005.jpg','https://www.rpgfan.com/wp-content/uploads/2021/06/Final-Fantasy-II-Pixel-Remaster-Screenshot-005.jpg','Direct FFII PR Hilda scene; publication gallery identifies version.'),
'pr-status':('References/Parity20261025/vorxu-ffii-character-stats.webp','https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/leveling/character-stats-960w.webp','Direct English PR status capture; platform/build unknown.'),
'pr-status-jp':('References/Parity20261025/gcgx-ffii-status.jpg','https://gcgx.games/ff2/re/img/slv.webp','Direct Japanese PR status capture; GCGX PR status page.'),
'pr-items':('References/Parity20261025/note-ffii-item-menu.jpg','https://assets.st-note.com/production/uploads/images/104758775/rectangle_large_type_2_f61987c156b420f34c0e6367b50445b4.jpeg?fit=bounds&quality=85&width=1280','Direct PR battle item list; battle surface only, not field inventory.'),
'pr-altair-map':('Logs/altair-reference-20261030/altair-pr.png','https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/towns/altair-start-game.png','Actual Altair sepia map; topology/silhouette only.'),
'pr-town-materials':('Logs/altair-reference-20261030/pr-town-materials.jpg','https://klardendum.com/wp-content/uploads/2021/11/ff2pr1.jpg','Other PR town, identity unconfirmed; materials only, never Altair geometry.'),
'local-hq':('Logs/interiors-hq-fixed-20261030.png',None,'Historical native remake capture, 2026-10-30 09:09; before this UI change.'),
'local-smithy':('Logs/interiors-smithy-fixed-20261030.png',None,'Historical native remake capture, 2026-10-30 09:05; before this comparison change.'),
'local-refuge':('Logs/interiors-scott-fixed-20261030.png',None,'Historical native remake capture, 2026-10-30 09:06; before this comparison change.'),
'local-tavern':('Logs/interiors-tavern-fixed-20261030.png',None,'Historical native remake capture, 2026-10-30 09:05; no matched retail tavern still accepted.'),
'local-status':('Review/ff2-shot-comparison-20261027/status.png',None,'Historical native prototype capture, 2026-10-27; old debug spell provisioning.'),
'local-field-menu':('Review/ff2-shot-comparison-20261027/field-menu.png',None,'Historical native prototype menu capture, 2026-10-27; does not establish current stock/menu choices.'),
'local-altair-old':('Logs/layout-altair-native.png',None,'Historical native town capture, 2026-10-29; predates the new AltairKitV1 renderer.'),
'local-fynn':('Logs/layout-fynn-final-native.png',None,'Historical native Fynn capture, 2026-10-29; runtime city-map adaptation.'),
}
ASSETS={'kit-hq':'Assets/Art/Production/AltairKitV1/buildings/headquarters.png','kit-inn':'Assets/Art/Production/AltairKitV1/buildings/inn.png','kit-sanctuary':'Assets/Art/Production/AltairKitV1/buildings/sanctuary.png','local-wall-asset':'Assets/Art/Production/RemasterExpansion/tiles/town/wall-cream-a.png','local-rug-asset':'Assets/Art/Production/RemasterExpansion/tiles/interior/carpet-center.png','local-bed-asset':'Assets/Art/Production/Campaign/prop/bed/idle.png'}
for k,p in ASSETS.items():SOURCES[k]=(str(ART/p),None,'Generated production asset; asset preview, not runtime proof.')
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',15);title=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',28)
manifest={'scope':'Independent component/layer comparison of FFII PR reference captures and dated local evidence. No new native runtime capture made by this task.','sources':{},'crops':[]}
def sha(data):return hashlib.sha256(data).hexdigest()
def keep(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and path.read_bytes()!=data:raise RuntimeError('Preserve differing file '+str(path))
 if not path.exists():path.write_bytes(data)
def png(path,im):
 import io
 b=io.BytesIO();im.save(b,format='PNG');keep(path,b.getvalue())
images={}
for k,(p,url,note) in SOURCES.items():
 source=Path(p) if Path(p).is_absolute() else GAME/p;data=source.read_bytes();target=OUT/'sources'/(k+source.suffix);keep(target,data)
 images[k]=Image.open(source).convert('RGBA');manifest['sources'][k]={'original':str(source),'url':url,'scope':note,'file':target.relative_to(OUT).as_posix(),'sha256':sha(data),'size':list(images[k].size)}
def crop(k,rect):
 im=images[k];return im.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3])) if rect else im.copy()
def box_sheet(name,heading,rows):
 cw=800;rh=460;sheet=Image.new('RGB',(1600,105+len(rows)*rh),(20,26,34));d=ImageDraw.Draw(sheet);d.text((24,16),heading,font=title,fill='#f5e2ac');d.text((24,57),'Reference left / dated local evidence right. Different cameras and progress; compare components, not pixel scores.',font=small,fill='#c8d0dc')
 for r,row in enumerate(rows):
  for c,(key,rect,label,note) in enumerate(row):
   x=c*cw;y=105+r*rh;im=crop(key,rect).convert('RGB');scale=min(752/im.width,338/im.height);im=im.resize((int(im.width*scale),int(im.height*scale)),Image.Resampling.NEAREST)
   d.rectangle((x+10,y+10,x+790,y+450),outline='#4e6073',width=1);sheet.paste(im,(x+(cw-im.width)//2,y+20+(338-im.height)//2));d.text((x+24,y+370),label,font=font,fill='#f5e2ac');d.text((x+24,y+401),note,font=small,fill='#c8d0dc')
 png(OUT/(name+'.png'),sheet)
box_sheet('01-interiors','INTERIOR LAYERS / structure, materials, furniture',[
 [('pr-smithy',(168,0,623,488),'PR Tobul: red ground + pale rug + L counter','Observed: tall wall face, weapon display, east forge.'),('local-smithy',(194,180,434,338),'Local smithy / native 30 Oct 09:05','Wood ground, red rug, split counters; forge asset absent.')],
 [('pr-refuge',(25,0,622,443),'PR Scott: wall face + bed niche + blue rug','Observed: timber/cream north wall, warm flagstone, crates.'),('local-refuge',(194,180,434,338),'Local refuge / native 30 Oct 09:06','Cool stone, extra partitions and beds; rug missing.')],
 [('pr-hilda',(430,340,1440,480),'PR Hilda: wide audience carpet and thrones','Observed cropped room; whole hideout layout is separate.'),('local-hq',(194,180,434,338),'Local headquarters / native 30 Oct 09:09','Compact one-room adaptation; central runner and side bays.')]
])
box_sheet('02-ui-v2','UI LAYERS / panel, speaker, fields, gauges',[
 [('pr-hilda',(388,57,1143,295),'PR Hilda: speaker chip above a top dialogue panel','World remains visible; keyword choices use lower panels.'),('local-field-menu',None,'Historical local modal style / 27 Oct','Used only for frame/dimming evidence; not a dialogue still.')],
 [('pr-status',None,'PR status: sidebar + portrait + two content columns','Blue gradient, cyan labels, warm framed proficiency gauges.'),('local-status',None,'Historical local status / 27 Oct','Gauge changes held in local code; column layout retained.')],
 [('pr-items',(60,409,1162,248),'PR battle items: description, list, actor pane','This state does not prove field inventory layout.'),('local-field-menu',None,'Local party menu / historical 27 Oct','No same-state inventory screenshot: comparison limited.')]
])
box_sheet('03-city','CITY LAYERS / topology versus generated structures',[
 [('pr-altair-map',(400,460,650,800),'Verified Altair: L-shaped HQ and western civic plaza','Sepia map confirms topology; no color inference.'),('kit-hq',None,'Current generated HQ source layers / asset preview','224x288 L canvas; runtime placement still needs fresh capture.')],
 [('pr-town-materials',(1440,80,600,592),'Other PR town: roof, facade, door and sign','Material vocabulary only; this is not an Altair screenshot.'),('kit-sanctuary',None,'Current generated sanctuary / asset preview','Distinct wide silhouette; style inspired, not a retail sprite.')],
 [('pr-altair-map',(390,190,670,1000),'Altair reference: varied frontages and paved districts','Nine generated role IDs share four approved source families.'),('local-altair-old',None,'Historical local Altair / 29 Oct / pre-kit','Superseded renderer; shown as baseline only, not current state.')]
])
CROPS=[
 ('wall-timber-cream','pr-refuge',(68,0,100,152),'wall face'),('floor-warm-stone','pr-refuge',(76,155,270,140),'floor'),('bed-and-blue-rug','pr-refuge',(409,158,195,240),'furniture/rug'),('shop-counter','pr-smithy',(215,98,340,126),'counter'),('shop-cream-rug','pr-smithy',(263,249,335,190),'rug'),('shop-red-floor','pr-smithy',(604,251,90,180),'floor'),('hilda-throne','pr-hilda',(898,407,134,206),'furniture'),('dialogue-speaker','pr-hilda',(407,57,122,42),'speaker tab'),('dialogue-panel','pr-hilda',(392,69,1136,282),'dialogue frame'),('status-gauge','pr-status',(682,191,81,14),'progress gauge'),('status-sidebar','pr-status',(49,28,196,292),'menu sidebar'),('item-description','pr-items',(68,413,1141,88),'description panel'),('current-wall','local-wall-asset',None,'current wall asset'),('current-rug','local-rug-asset',None,'current carpet asset'),('current-bed','local-bed-asset',None,'current bed asset'),('current-inn','kit-inn',None,'current facade+roof asset')]
cols=4;cw=400;ch=340;sheet=Image.new('RGB',(cols*cw,95+4*ch),(20,26,34));d=ImageDraw.Draw(sheet);d.text((20,16),'COMPONENT ATLAS / exact source pixels, reference-only crops',font=title,fill='#f5e2ac');d.text((20,57),'Original imagery stays outside runtime assets. Crops are not production sprites.',font=small,fill='#c8d0dc')
for i,(name,k,rect,kind) in enumerate(CROPS):
 im=crop(k,rect);png(OUT/'crops'/(name+'.png'),im);manifest['crops'].append({'id':name,'source':k,'rect':list(rect) if rect else [0,0,*im.size],'kind':kind,'file':'crops/'+name+'.png'})
 x=(i%cols)*cw;y=95+(i//cols)*ch;rgb=im.convert('RGB');scale=min(368/rgb.width,244/rgb.height);rgb=rgb.resize((int(rgb.width*scale),int(rgb.height*scale)),Image.Resampling.NEAREST);sheet.paste(rgb,(x+(cw-rgb.width)//2,y+12+(244-rgb.height)//2));d.text((x+15,y+269),name,font=font,fill='#f5e2ac');d.text((x+15,y+299),kind,font=small,fill='#c8d0dc')
png(OUT/'04-components.png',sheet)
ANNOTATIONS={
 'pr-smithy':[(1,(213,0,534,101),'Tall wall: face/trim/display'),(2,(214,99,342,128),'L-shaped service counter'),(3,(264,249,334,189),'Pale patterned rug'),(4,(601,253,94,182),'Red base floor'),(5,(648,173,86,89),'Forge / work bay')],
 'pr-refuge':[(1,(68,0,537,153),'Tall cream/timber north wall'),(2,(74,154,331,239),'Warm large flagstone'),(3,(409,157,194,238),'Blue rug bed niche'),(4,(70,296,124,99),'Stacked storage crates')],
 'pr-hilda':[(1,(388,69,1141,282),'Top dialogue panel'),(2,(407,57,120,42),'Speaker tab'),(3,(625,408,1056,410),'Wide red/gold carpet'),(4,(899,406,522,209),'Throne pair'),(5,(97,819,1723,229),'Lower keyword panes')],
 'pr-status':[(1,(49,28,196,292),'Main menu sidebar'),(2,(444,80,286,70),'Portrait and HP/MP'),(3,(263,166,307,259),'Attribute and derived values'),(4,(591,165,173,192),'Framed weapon gauges'),(5,(49,464,862,46),'Bottom input strip')],
 'local-smithy':[(1,(196,180,430,34),'Repeated square wall blocks'),(2,(224,214,370,279),'Wood floor differs'),(3,(258,337,244,88),'Red rug differs'),(4,(257,303,304,30),'Split counter silhouette')],
 'local-status':[(1,(88,88,851,459),'Single central panel'),(2,(109,185,248,286),'Stats and combat values'),(3,(364,172,207,285),'Thin blue gauges: corrected in code'),(4,(629,174,244,151),'Additional magic column')]
}
for k,boxes in ANNOTATIONS.items():
 im=images[k].convert('RGB');legend=Image.new('RGB',(im.width,im.height+46+len(boxes)*28),(20,26,34));legend.paste(im,(0,0));d=ImageDraw.Draw(legend)
 for number,rect,note in boxes:
  x,y,w,h=rect;d.rectangle((x,y,x+w,y+h),outline='#ffcf69',width=3);d.rectangle((x,y,x+26,y+25),fill='#172331');d.text((x+4,y+1),str(number),font=font,fill='#ffcf69');d.text((18,im.height+20+(number-1)*28),f'{number}. {note}',font=small,fill='#e0e5ed')
 png(OUT/'annotated'/(k+'.png'),legend)
keep(OUT/'evidence-manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())
print('Created4comparisonPNG sheets,6annotatedcaptures,16nativecrops,sourcecopies+hashmanifest.')
