#!/usr/local/bin/python3.11
from pathlib import Path
import json, subprocess, shutil, hashlib, zipfile, importlib.util, io, sys
sys.dont_write_bytecode = True
from xml.etree import ElementTree as ET
from PIL import Image, ImageCms
import fitz
from pypdf import PdfReader, PdfWriter
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'exports';D=ROOT/'deliverables';R=ROOT/'review'
ICC=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
check_js='''() => {
 const board=document.querySelector('.board');const base=board.getBoundingClientRect();
 const els=[...board.querySelectorAll('.label,.art,.line,.surface')];
 const overflow=els.filter(e=>e.scrollWidth>e.clientWidth+1||e.scrollHeight>e.clientHeight+1).map(e=>({text:e.textContent,scroll:[e.scrollWidth,e.scrollHeight],box:[e.clientWidth,e.clientHeight]}));
 const outside=els.filter(e=>{const r=e.getBoundingClientRect();return r.left<base.left-.5||r.top<base.top-.5||r.right>base.right+.5||r.bottom>base.bottom+.5}).map(e=>e.textContent||e.getAttribute('alt'));
 const labels=[...board.querySelectorAll('.label')];const overlaps=[];
 const hit=(a,b)=>a.left<b.right-.5&&a.right>b.left+.5&&a.top<b.bottom-.5&&a.bottom>b.top+.5;
 for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++)if(hit(labels[i].getBoundingClientRect(),labels[j].getBoundingClientRect()))overlaps.push([labels[i].textContent,labels[j].textContent]);
 const artOverlaps=[];for(const t of labels)for(const a of board.querySelectorAll('.art'))if(hit(t.getBoundingClientRect(),a.getBoundingClientRect()))artOverlaps.push([t.textContent,a.alt]);
 const missing=[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src);
 return {overflow,outside:outside.length,outsideDetails:outside,labelOverlaps:overlaps.length,labelOverlapDetails:overlaps,labelArtOverlaps:artOverlaps,missingImages:missing,labelsChecked:labels.length,elementsChecked:els.length};
}'''
reports={}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 page=browser.new_page(viewport={'width':3200,'height':2400},device_scale_factor=1)
 for board in sorted(D.glob('board*.html')):
  page.goto(board.as_uri());page.evaluate('document.fonts.ready');page.wait_for_function('Array.from(document.images).every(i=>i.complete)')
  reports[board.stem]=page.evaluate(check_js)
  page.screenshot(path=str(D/(board.stem+'.jpg')),type='jpeg',quality=98)
  page.pdf(path=str(R/(board.stem+'.pdf')),width='3200px',height='2400px',print_background=True,prefer_css_page_size=True)
 # Responsive page and actual download destinations.
 reports['index']={}
 for width in (1440,390):
  page.set_viewport_size({'width':width,'height':1000});page.goto((ROOT/'index.html').as_uri());page.evaluate('document.fonts.ready')
  reports['index'][str(width)]=page.evaluate('''()=>({overflow:document.documentElement.scrollWidth>innerWidth,missingImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src)})''')
 browser.close()
# Export alpha PNGs via librsvg, with embedded sRGB profile.
for src,out in [('08_SmartBlinkIT_Transparent_Master.svg','01_Primary_Horizontal_3200px_Transparent.png'),('../review/transparent-midnight.svg','02_Primary_Midnight_3200px_Transparent.png'),('05_SmartBlinkIT_Standalone_Icon.svg','05_Standalone_Icon_3000px_Transparent.png')]:
 source=(E/src).resolve();dest=E/out
 subprocess.run(['/opt/homebrew/bin/rsvg-convert','-w','3200','-o',str(dest),str(source)],check=True)
 im=Image.open(dest).convert('RGBA');im.save(dest,icc_profile=ICC)
# Guidelines retain vector content from browser PDF, followed by eight vector artboards.
writer=PdfWriter()
for f in sorted(R.glob('board*.pdf')):writer.append(str(f))
writer.append(str(E/'SmartBlinkIT_Master_Vector.ai'))
writer.add_metadata({'/Title':'Smart Blink IT / V2 Brand Guidelines and Vectors','/Author':'Smart Blink IT'})
with open(E/'SmartBlinkIT_Brand_Guidelines_and_Vectors.pdf','wb') as f:writer.write(f)
# Preview utility requested by the project; custom output directory avoids its /tmp default.
spec=importlib.util.spec_from_file_location('make_preview','/Users/frank/Work/13_money/scripts/make_preview.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
for f in sorted(D.glob('board*.jpg')):
 im=Image.open(f);im.save(f,quality=98,subsampling=0,icc_profile=ICC)
 mod.make_preview(str(f),1200,str(R/'previews'))
# Render real PDF pages for inspection, not screenshots of JPGs.
doc=fitz.open(E/'SmartBlinkIT_Brand_Guidelines_and_Vectors.pdf')
for i in (0,1,2,3,4,5,6):
 page=doc[i];pix=page.get_pixmap(matrix=fitz.Matrix(1200/page.rect.width,1200/page.rect.width),alpha=False)
 pix.save(str(R/'previews'/f'pdf_page_{i+1:02}.png'))
# File inventory / vector structural evidence.
svg_info={}
for f in sorted(E.glob('*.svg')):
 root=ET.parse(f).getroot();tags={n.tag.split('}')[-1] for n in root.iter()}
 svg_info[f.name]={'tags':sorted(tags),'paths':sum(n.tag.endswith('path') for n in root.iter()),'textCount':sum(n.tag.endswith('text') for n in root.iter()),'compoundHoles':sum(n.get('fill-rule')=='evenodd' for n in root.iter())}
 assert tags<= {'svg','title','path'},(f,tags)
 assert not any(n.tag.endswith('text') for n in root.iter())
reports['svg']=svg_info
reports['png']={f.name:{'size':list(Image.open(f).size),'mode':Image.open(f).mode,'alphaExtrema':list(Image.open(f).getchannel('A').getextrema())} for f in E.glob('*.png')}
ai=fitz.open(E/'SmartBlinkIT_Master_Vector.ai')
reports['ai']={'header':(E/'SmartBlinkIT_Master_Vector.ai').read_bytes()[:8].decode(),'artboards':len(ai),'rasterImages':sum(len(p.get_images()) for p in ai),'vectorPaths':sum(len(p.get_drawings()) for p in ai),'nativeIllustratorOpenTest':'not available: Illustrator not installed'}
reports['pdf']={'pages':len(doc),'vectorPaths':sum(len(p.get_drawings()) for p in doc)}
reports['jpg']={f.name:list(Image.open(f).size) for f in D.glob('*.jpg')}
# Pack exactly fourteen production assets (eight SVG + three PNG + AI/EPS/PDF).
files=sorted(f for f in E.iterdir() if f.suffix.lower() in ('.svg','.png','.ai','.eps','.pdf'))
assert len(files)==14,len(files)
with zipfile.ZipFile(E/'Smart_Blink_IT_Vector_Master_Pack.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(f,f.name)
with zipfile.ZipFile(E/'Smart_Blink_IT_Vector_Master_Pack.zip') as z:assert z.testzip() is None
for f in E.iterdir():
 if f.is_file():shutil.copy2(f,ROOT/'docs/exports'/f.name)
for f in D.glob('*.jpg'):shutil.copy2(f,ROOT/'docs/deliverables'/f.name)
shutil.copy2(ROOT/'index.html',ROOT/'docs/index.html')
shutil.copytree(ROOT/'assets',ROOT/'docs/assets',dirs_exist_ok=True)
reports['sync']=all(hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256((ROOT/'docs/exports'/f.name).read_bytes()).digest() for f in E.iterdir() if f.is_file()) and all(f.read_bytes()==(ROOT/'docs/deliverables'/f.name).read_bytes() for f in D.glob('*.jpg'))
reports['zip']={'fileCount':len(files),'crc':'pass','sha256':hashlib.sha256((E/'Smart_Blink_IT_Vector_Master_Pack.zip').read_bytes()).hexdigest()}
(R/'validation.json').write_text(json.dumps(reports,indent=2))
print(json.dumps({k:v for k,v in reports.items() if k not in ('svg','png')},indent=2))
assert all(not v['overflow'] and not v['outside'] and not v['labelOverlaps'] and not v['labelArtOverlaps'] and not v['missingImages'] for k,v in reports.items() if k.startswith('board'))
