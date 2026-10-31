from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, json, shutil

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parents[2]/'AI-Remake-FF2'/'Logs'/'altair-reference-20261030'
SOURCES={
 'altair': {'file':'altair-pr.png','url':'https://cdn.vorxu.com/images/final-fantasy-2-pixel-remaster/towns/altair-start-game.png','page':'https://vorxu.com/final-fantasy-2-pixel-remaster/walkthrough/altair-and-fynn','scope':'Actual Altair PR in-game sepia map: topology and architectural silhouette only.'},
 'materials': {'file':'pr-town-materials.jpg','url':'https://klardendum.com/wp-content/uploads/2021/11/ff2pr1.jpg','page':'https://klardendum.com/review/o-tempora-final-fantasy-ii-pixel-remaster/','scope':'Different PR town, identity unconfirmed: palette/material vocabulary only; never Altair geography.'}
}
# x,y,width,height in original source pixels; right and bottom excluded.
CROPS=[
 ('altair-item-shop','altair',(442,286,115,157),'Northwest item shop','object'),
 ('altair-inn','altair',(442,496,187,167),'Inn, west of headquarters','object'),
 ('altair-headquarters','altair',(664,496,262,317),'L-shaped headquarters','object'),
 ('altair-sanctuary','altair',(1102,188,264,184),'Northeast sanctuary','object'),
 ('altair-armor-shop','altair',(442,1018,187,169),'Southwest armor shop','object'),
 ('altair-weapons-smithy','altair',(962,866,264,241),'Southeast weapons / smithy','object'),
 ('altair-roof-main','altair',(667,499,251,94),'Headquarters roof strip','roof'),
 ('altair-facade-main','altair',(668,591,148,73),'Headquarters front facade','facade'),
 ('altair-plaza-ground','altair',(449,882,355,123),'Broad civic cobble plaza','ground'),
 ('altair-item-symbol','altair',(462,317,79,65),'Item-shop map symbol','shop-sign'),
 ('altair-inn-symbol','altair',(539,543,73,54),'Inn map symbol','shop-sign'),
 ('altair-armor-symbol','altair',(471,1051,66,66),'Armor-shop map symbol','shop-sign'),
 ('altair-weapon-symbol','altair',(984,905,80,79),'Weapon-shop map symbol','shop-sign'),
 ('altair-magic-symbol','altair',(1279,682,75,75),'Magic-shop map symbol','shop-sign'),
 ('altair-fountain','altair',(632,791,79,88),'Central civic fountain','prop'),
 ('altair-courtyard-wall','altair',(364,214,264,76),'Item-shop pale U-wall top','terrain'),
 ('altair-cliff-steps','altair',(955,297,89,146),'Upper terrace and steps','terrain'),
 ('altair-cliff-rim','altair',(741,359,221,58),'Horizontal natural cliff rim','terrain'),
 ('material-blue-roof','materials',(1472,112,368,256),'Other town: blue slate roof','roof'),
 ('material-masonry','materials',(1456,400,384,256),'Other town: pale masonry','facade'),
 ('material-door','materials',(1864,504,136,168),'Other town: arched timber door','facade'),
 ('material-cobble','materials',(1360,720,384,128),'Other town: paving pattern','ground'),
 ('material-gold-sign','materials',(1856,272,128,128),'Other town: roof-mounted sign','shop-sign'),
 ('material-fountain','materials',(2048,840,392,400),'Other town: fountain palette','prop'),
 ('material-quay-edge','materials',(960,128,248,160),'Other town: quay, not Altair cliff','terrain'),
 ('material-grass-edge','materials',(1440,624,376,80),'Other town: grass / masonry edge','terrain')
]

def digest(data):return hashlib.sha256(data).hexdigest()
def preserve(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and path.read_bytes()!=data:raise RuntimeError('Preserve existing differing file: '+str(path))
 if not path.exists():path.write_bytes(data)
def png(path,img):
 import io
 b=io.BytesIO();img.save(b,format='PNG');preserve(path,b.getvalue())
font_path=Path('C:/Windows/Fonts/consola.ttf')
font=ImageFont.truetype(str(font_path),18);small=ImageFont.truetype(str(font_path),15);title=ImageFont.truetype(str(font_path),25)
images={};manifest={'referenceOnly':True,'runtimeUse':False,'license':'Original-game copyright and source attribution retained; no new license granted. Crops are unaltered rectangular research samples, not generated production art.','rectangleConvention':'x,y,width,height in original source pixels; right/bottom excluded. No upscaling or painting in crop files.','sources':{},'crops':[]}
for key,source in SOURCES.items():
 data=(SOURCE/source['file']).read_bytes();preserve(OUT/'sources'/source['file'],data)
 images[key]=Image.open(SOURCE/source['file']).convert('RGB')
 manifest['sources'][key]={**source,'sha256':digest(data),'dimensions':images[key].size,'local':'sources/'+source['file']}
for name,key,rect,label,kind in CROPS:
 x,y,w,h=rect;crop=images[key].crop((x,y,x+w,y+h));path=OUT/'crops'/(name+'.png');png(path,crop)
 manifest['crops'].append({'id':name,'source':key,'rect':rect,'kind':kind,'label':label,'file':'crops/'+name+'.png','sha256':digest(path.read_bytes())})
for key,heading in [('altair','ALTAIR / verified sepia map topology'),('materials','OTHER PR TOWN / material samples only')]:
 rows=[row for row in manifest['crops'] if row['source']==key];cols=4;cellw=360;cellh=354
 sheet=Image.new('RGB',(cols*cellw,104+((len(rows)+cols-1)//cols)*cellh),(22,27,33));d=ImageDraw.Draw(sheet)
 d.text((20,15),heading,font=title,fill=(244,224,170))
 d.text((20,52),'REFERENCE ONLY / source pixels retained / exact rectangles listed below each sample',font=small,fill=(200,208,217))
 for i,row in enumerate(rows):
  x=(i%cols)*cellw;y=104+(i//cols)*cellh
  d.rectangle((x+8,y+8,x+cellw-8,y+cellh-8),outline=(72,83,96),width=1)
  im=Image.open(OUT/row['file']).convert('RGB');scale=min((cellw-32)/im.width,258/im.height);im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.Resampling.NEAREST)
  sheet.paste(im,(x+(cellw-im.width)//2,y+16+(258-im.height)//2))
  d.text((x+16,y+282),row['id'],font=small,fill=(246,224,172));d.text((x+16,y+306),str(tuple(row['rect']))+' px',font=small,fill=(204,213,220));d.text((x+16,y+327),row['kind'],font=small,fill=(164,184,195))
 png(OUT/(key+'-contact-sheet.png'),sheet)
 annotated=images[key].copy();d=ImageDraw.Draw(annotated)
 for row in rows:
  x,y,w,h=row['rect'];color={'roof':(48,167,255),'facade':(255,188,87),'ground':(85,224,151),'shop-sign':(242,103,218),'terrain':(245,231,106)}.get(row['kind'],(242,242,242))
  d.rectangle((x,y,x+w-1,y+h-1),outline=color,width=3)
  text=row['id'];box=d.textbbox((x,y-23),text,font=small);d.rectangle(box,fill=(15,20,25));d.text((x,y-23),text,font=small,fill=color)
 png(OUT/(key+'-annotated-crops.png'),annotated)
preserve(OUT/'crop-manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())
print(f'Created {len(CROPS)} exact PNG crops, two contact sheets, two annotated sources, source copies and SHA-256 manifest under {OUT}')
