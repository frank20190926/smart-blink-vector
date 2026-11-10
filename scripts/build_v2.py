#!/usr/local/bin/python3.11
"""Deterministic V2 source: geometry -> SVG / PDF-compatible AI / EPS / HTML boards."""
from pathlib import Path
import json, math, shutil, hashlib, html
from xml.etree import ElementTree as ET
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from shapely.geometry import LineString

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'exports'; D=ROOT/'deliverables'; R=ROOT/'review'
for p in (E,D,R,ROOT/'docs/exports',ROOT/'docs/deliverables'):p.mkdir(parents=True,exist_ok=True)
BLUE='#087FBD'; NIGHT='#061426'; CYAN='#13C8F4'; WHITE='#FFFFFF'
W,H=4060,600

def num(v):return f'{v:.5f}'.rstrip('0').rstrip('.') if abs(v)>1e-7 else '0'
class CubicPen(BasePen):
 def __init__(self):super().__init__(None);self.ops=[]
 def _moveTo(self,p):self.ops.append(('M',[p]))
 def _lineTo(self,p):self.ops.append(('L',[p]))
 def _curveToOne(self,a,b,c):self.ops.append(('C',[a,b,c]))
 def _closePath(self):self.ops.append(('Z',[]))
 def _endPath(self):pass
 def path(self):return ' '.join(op+' '.join(num(v) for p in pts for v in p) for op,pts in self.ops)
def transform(d,m=(1,0,0,1,0,0)):
 p=CubicPen();parse_path(d,TransformPen(p,m));return p.path()
def circle(cx,cy,r):
 k=.5522847498307936*r
 return f'M{num(cx+r)} {num(cy)} C{num(cx+r)} {num(cy+k)} {num(cx+k)} {num(cy+r)} {num(cx)} {num(cy+r)} C{num(cx-k)} {num(cy+r)} {num(cx-r)} {num(cy+k)} {num(cx-r)} {num(cy)} C{num(cx-r)} {num(cy-k)} {num(cx-k)} {num(cy-r)} {num(cx)} {num(cy-r)} C{num(cx+k)} {num(cy-r)} {num(cx+r)} {num(cy-k)} {num(cx+r)} {num(cy)} Z'
def rect(x,y,w,h):return f'M{x} {y}h{w}v{h}h{-w}Z'
def shape(id,d,fill,stroke=None,sw=None):
 a=dict(id=id,d=transform(d),fill=fill)
 if stroke:a.update(stroke=stroke,**{'stroke-width':str(sw),'stroke-linejoin':'round','stroke-linecap':'round'})
 if id.startswith(('ring','halo')):a['fill-rule']='evenodd'
 return a

def expanded_polyline(points):
 p=LineString(points).buffer(12,cap_style=2,join_style=2)
 return 'M'+' L'.join(f'{num(x)} {num(y)}' for x,y in list(p.exterior.coords)[:-1])+' Z'
# Explicit centerline topology, retained as editable geometry. All non-arc traces expanded.
left=[]
bracket='M -238 -212 L -210 -212 L -146 -148 L -72 -222 L -32 -222 L -32 -126 A130 130 0 0 0 -32 126 L-32 222 L-72 222 L-146 148 L-210 212 L-238 212'
left.append(shape('bracket',bracket,'none',BLUE,24))
traces=[ [(-310,-144),(-238,-144),(-126,-32)], [(-310,144),(-238,144),(-126,32)], [(-375,-82),(-268,-82),(-186,0),(-130,0)], [(-186,0),(-268,82),(-375,82)], [(-296,0),(-286,0),(-236,50)] ]
for i,points in enumerate(traces):left.append(shape(f'trace-{i}',expanded_polyline(points),BLUE))
for i,(x,y) in enumerate([(-238,-212),(-310,-144),(-310,144),(-238,212)]):left.append(shape(f'terminal-{i}',circle(x,y,26),BLUE))
for i,(x,y) in enumerate([(-398,-82),(-318,0),(-398,82)]):left.append(shape(f'ring-{i}',circle(x,y,30)+circle(x,y,16),BLUE))
WORDS=json.loads((ROOT/'source/wordmark_paths.json').read_text())
# 60.1-unit stem and dot; dot's upper bound equals 426.684 cap line exactly.
WORDS['word-BLiNK']=WORDS['word-BLiNK'].replace('3159.65 489.24','3159.65 511.0')
CAP=426.684; DOT_R=30.05

def logo(mode='light',layout='horizontal',background=False):
 right=WHITE if mode in ('dark','white') else NIGHT
 mono= NIGHT if mode=='mono' else WHITE if mode=='white' else None
 objs=[]
 for side in (-1,1):
  for src in left:
   p=src.copy();p['id']=f"{src['id']}-{'left' if side==-1 else 'right'}"
   p['d']=transform(src['d'],(1 if side==-1 else -1,0,0,1,450,300))
   c=mono or (BLUE if side==-1 else right)
   if p['fill']!='none':p['fill']=c
   if 'stroke' in p:p['stroke']=c
   objs.append(p)
 objs.append(shape('center-disc',circle(450,300,83.5),mono or BLUE))
 # A precise 2.5-unit accent ring outside the solid blue center, with no glow.
 if not mono:objs.append(shape('halo-center',circle(450,300,88.5)+circle(450,300,86),CYAN))
 icon_end=len(objs)
 for id in ('word-SMART','word-BLiNK','word-IT'):
  c=mono or (right if id=='word-BLiNK' else BLUE)
  objs.append(shape(id,transform(WORDS[id],(1,0,0,1,-199.65,-250)),c))
 objs.append(shape('blink-i-dot',circle(3189.7-199.65,CAP+DOT_R-250,DOT_R),mono or right))
 if layout=='icon':objs=objs[:icon_end];w,h=900,600
 elif layout=='stacked':
  for i,p in enumerate(objs):
   p['d']=transform(p['d'],(1.5,0,0,1.5,922.5,-35)) if i<icon_end else transform(p['d'],(1,0,0,1,-930,690))
   if 'stroke-width' in p:p['stroke-width']=str(float(p['stroke-width'])*1.5)
  w,h=3200,1220
 else:w,h=W,H
 if background:objs.insert(0,shape('background',rect(0,0,w,h),NIGHT if mode=='dark' else WHITE))
 return objs,w,h

def svg(objs,w,h,title='Smart Blink IT'):
 return '<?xml version="1.0" encoding="UTF-8"?>\n'+f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><title>{title}</title>'+''.join('<path '+' '.join(f'{k}="{v}"' for k,v in p.items())+'/>' for p in objs)+'</svg>'
NAMES=[ '01_SmartBlinkIT_Primary_Horizontal_Light.svg','02_SmartBlinkIT_Primary_Horizontal_Midnight.svg','03_SmartBlinkIT_Stacked_Vertical_Light.svg','04_SmartBlinkIT_Stacked_Vertical_Midnight.svg','05_SmartBlinkIT_Standalone_Icon.svg','06_SmartBlinkIT_SingleColor_Midnight.svg','07_SmartBlinkIT_SingleColor_White.svg','08_SmartBlinkIT_Transparent_Master.svg']
CONFIG=[('light','horizontal',True),('dark','horizontal',True),('light','stacked',True),('dark','stacked',True),('light','icon',False),('mono','horizontal',False),('white','horizontal',False),('light','horizontal',False)]
versions=[]
for name,cfg in zip(NAMES,CONFIG):
 data=logo(*cfg); versions.append(data);(E/name).write_text(svg(*data,title=name[3:-4].replace('_',' ')))
# Transparent midnight artwork has no midnight background path.
(R/'transparent-midnight.svg').write_text(svg(*logo('dark')))
# Portable EPS Level 3 path master, all curves cubic, no fonts or raster data.
def ops(d):
 p=CubicPen();parse_path(d,p);return p.ops
objs,w,h=logo()
eps=['%!PS-Adobe-3.0 EPSF-3.0',f'%%BoundingBox: 0 0 {w} {h}','%%LanguageLevel: 3','%%Title: Smart Blink IT - V2 editable vector master','%%Pages: 1','%%EndComments',f'0 {h} translate 1 -1 scale','1 setlinejoin 1 setlinecap']
for p in objs:
 eps+=['newpath']
 for op,pts in ops(p['d']):eps.append(' '.join(num(v) for pt in pts for v in pt)+' '+{'M':'moveto','L':'lineto','C':'curveto','Z':'closepath'}[op])
 color=p.get('stroke') if p['fill']=='none' else p['fill']
 eps.append(' '.join(num(int(color[i:i+2],16)/255) for i in (1,3,5))+' setrgbcolor')
 eps.append(f"{p['stroke-width']} setlinewidth stroke" if p['fill']=='none' else 'eofill' if p.get('fill-rule')=='evenodd' else 'fill')
eps+=['showpage','%%EOF'];(E/'SmartBlinkIT_Master_Vector.eps').write_text('\n'.join(eps)+'\n')
# PDF 1.5-compatible Illustrator-editable master: eight artboards, genuine vector paths.
c=canvas.Canvas(str(E/'SmartBlinkIT_Master_Vector.ai'),pagesize=(W,H),pdfVersion=(1,5),pageCompression=1)
c.setTitle('Smart Blink IT - V2 / 8 vector artboards');c.setAuthor('Smart Blink IT')
for objs,w,h in versions:
 c.setPageSize((w,h));c.saveState();c.translate(0,h);c.scale(1,-1)
 for s in objs:
  p=c.beginPath()
  for op,pts in ops(s['d']):
   if op=='M':p.moveTo(*pts[0])
   elif op=='L':p.lineTo(*pts[0])
   elif op=='C':p.curveTo(*(v for pt in pts for v in pt))
   else:p.close()
  fill=s['fill']!='none';stroke='stroke' in s
  if fill:c.setFillColor(HexColor(s['fill']))
  if stroke:c.setStrokeColor(HexColor(s['stroke']));c.setLineWidth(float(s['stroke-width']));c.setLineCap(1);c.setLineJoin(1)
  c.drawPath(p,stroke=int(stroke),fill=int(fill),fillMode=0 if s.get('fill-rule')=='evenodd' else 1)
 c.restoreState();c.showPage()
c.save()
# Lock verified client facts; applications contain role labels, no invented contacts.
facts={'contest':'2801124','name':'SMART BLiNK IT','original_asset':'assets/smart_blink.png','original_px':[462,86],'palette':[NIGHT,BLUE,CYAN,WHITE],'tagline':None,'contacts_provided':False,'asset_sha256':hashlib.sha256((ROOT/'assets/smart_blink.png').read_bytes()).hexdigest()}
(ROOT/'client_facts.json').write_text(json.dumps(facts,indent=2)+'\n')

CSS='''@font-face{font-family:Space;src:url('../assets/fonts/SpaceGrotesk-600.ttf')}@font-face{font-family:Plex;src:url('../assets/fonts/IBMPlexSans-400.ttf')}@font-face{font-family:Plex;src:url('../assets/fonts/IBMPlexSans-600.ttf');font-weight:600}*{box-sizing:border-box}html,body{margin:0;padding:0}body{color:#061426;background:white;font-family:Plex,sans-serif;font-size:28px;font-variant-numeric:tabular-nums}.board{width:3200px;height:2400px;position:relative;background:white;overflow:hidden;break-after:page}.label,.art,.line,.surface{position:absolute}.label{margin:0;line-height:1.25}.heading{font-family:Space;font-size:46px;letter-spacing:-1px}.small{font-size:25px}.note{font-size:25px;color:#40566A}.footer{font-size:24px;letter-spacing:1px}.art{object-fit:contain}.line{background:#D8E0E8}.surface{border:1px solid #D8E0E8}.grid-sample{background-image:linear-gradient(45deg,#eef2f5 25%,transparent 25%),linear-gradient(-45deg,#eef2f5 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#eef2f5 75%),linear-gradient(-45deg,transparent 75%,#eef2f5 75%);background-size:24px 24px;background-position:0 0,0 12px,12px -12px,-12px 0}@page{size:3200px 2400px;margin:0}'''

def box(cls,x,y,w,h,content='',extra=''):
 return f'<div class="{cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{extra}">{content}</div>'
def label(text,x,y,w=1400,h=40,cls='',extra=''):
 return box('label '+cls,x,y,w,h,html.escape(text),extra)
def img(src,x,y,w,h,alt='',extra=''):
 return f'<img class="art" alt="{html.escape(alt)}" src="{src}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{extra}">'
def line(x,y,w,h=1):return box('line',x,y,w,h)
def footer(n,text):
 return line(0,2260,3200,1.333)+label('SMART BLINK IT — '+text,80,2290,2800,38,'footer')+label(f'SHEET 0{n} OF 03',2810,2344,310,32,'footer')+label('PRECISION VECTOR IDENTITY SYSTEM',80,2344,2000,32,'footer')
def write_board(name,body):
 (D/(name+'.html')).write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>'+name+'</title><style>'+CSS+'</style><main class="board">'+body+'</main></html>')

# Sheet 01. Identity artwork spans more than 92% of the width in each field.
b1=box('surface',0,0,3200,1130,extra='background:#FFFFFF;border:0')+box('surface',0,1130,3200,1130,extra=f'background:{NIGHT};border:0')
b1+=img('../exports/'+NAMES[0],80,330,3040,450,'Primary horizontal on white')+img('../exports/'+NAMES[1],80,1460,3040,450,'Primary horizontal on midnight')
b1+=line(0,2260,3200,1.333)+label('SMART BLINK IT — PRECISION VECTOR IDENTITY SYSTEM',80,2285,3040,40,'footer')+label('MANDATORY PALETTE: #061426 / #087FBD / #13C8F4 / #FFFFFF',80,2344,2500,32,'footer')+label('SHEET 01 OF 03',2810,2344,310,32,'footer')
write_board('board1_hero_light_and_midnight_lockups',b1)

# Actual outline visualization of delivered geometry, with real Bezier anchors / handles.
icon,iw,ih=logo(layout='icon'); grid=[]
for x in range(0,901,50):grid.append(f'<path d="M{x} 0V600" stroke="#D8E0E8" stroke-width=".6"/>')
for y in range(0,601,50):grid.append(f'<path d="M0 {y}H900" stroke="#D8E0E8" stroke-width=".6"/>')
grid.append('<path d="M450 0V600" stroke="#087FBD" stroke-width="1.5" stroke-dasharray="6 6"/>')
for p in icon:
 grid.append(f'<path d="{p["d"]}" fill="none" stroke="#061426" stroke-width="1.2"/>')
 prev=None
 for op,pts in ops(p['d']):
  if op=='C':
   a,b,end=pts
   if prev:grid.append(f'<path d="M{prev[0]} {prev[1]}L{a[0]} {a[1]}M{end[0]} {end[1]}L{b[0]} {b[1]}" fill="none" stroke="#087FBD" stroke-width=".65"/>')
   for q in (a,b):grid.append(f'<path d="{circle(*q,1.9)}" fill="white" stroke="#087FBD" stroke-width=".7"/>')
  if pts:
   q=pts[-1];grid.append(f'<path d="{rect(q[0]-2,q[1]-2,4,4)}" fill="white" stroke="#087FBD" stroke-width=".7"/>');prev=q
(R/'outline.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 600">'+''.join(grid)+'</svg>')
# Wordmark detail includes the actual path bounds of i, L and N, not a software screenshot.
word_detail=[p for p in logo()[0] if p['id'] in ('word-BLiNK','blink-i-dot')]
(R/'cap-detail.svg').write_text(svg(word_detail,W,H).replace('viewBox="0 0 4060 600"','viewBox="2725 120 610 380"').replace('width="4060" height="600"','width="610" height="380"'))
b2=label('01 / SOURCE & REFINEMENT',80,65,1400,65,'heading')+label('02 / PATH GEOMETRY',1690,65,1400,65,'heading')+line(80,156,3040)
b2+=label('Original low-resolution raster · 462 × 86 px',80,200,1450,40,'small')+img('../assets/smart_blink.png',80,280,1400,261,'Original client image',extra='image-rendering:pixelated')
b2+=label('Refined symmetric vector',80,580,1450,40,'small')+img('../exports/'+NAMES[0],80,657,1400,207,'Refined vector')
b2+=label('24-unit traces / 45° & 135° diagonals / 4 solid + 3 open terminals per side',80,900,1500,50,'note')
b2+=label('i dot aligned to cap height',80,1040,590,50,'small')+img('../review/cap-detail.svg',760,960,410,255,'Cap height detail')+line(760,998,410,1)
b2+=img('../review/outline.svg',1690,200,1430,953,'Delivered vector paths, anchors and Bezier handles')
b2+=label('Outline / Ctrl+Y reference · generated from the delivered SVG paths',1690,1170,1430,40,'note')
b2+=label('03 / EIGHT REQUIRED LOGO VERSIONS',80,1250,2800,70,'heading')
TITLES=['Primary / light','Primary / midnight','Stacked / light','Stacked / midnight','Standalone icon','Single color / midnight','Single color / white','Transparent master']
for i,(name,data,title) in enumerate(zip(NAMES,versions,TITLES)):
 col,row=i%4,i//4;x=80+col*760;y=1355+row*430;dark=i in (1,3,6)
 b2+=box('surface'+(' grid-sample' if i==7 else ''),x,y,760,430,extra=f'background-color:{NIGHT if dark else WHITE}')
 b2+=label(f'{i+1:02d}  {title}',x+24,y+24,712,36,'small',extra=f'color:{WHITE if dark else NIGHT}')
 if i in (2,3):b2+=img('../exports/'+name,x+55,y+100,650,250,title)
 elif i==4:b2+=img('../exports/'+name,x+185,y+95,390,260,title)
 else:b2+=img('../exports/'+name,x+24,y+155,712,106,title)
 b2+=label(f'{data[1]} × {data[2]} units  /  SVG',x+24,y+370,712,34,'small',extra=f'color:{WHITE if dark else NIGHT}')
b2+=footer(2,'SOURCE, GEOMETRY & STANDARD VARIANTS')
write_board('board2_8_versions_and_bezier_geometry',b2)

# Sheet 03: practical specifications. Pantone is explicitly unassigned without a physical match.
b3=label('01 / MANDATORY BRAND COLORS',80,65,1490,65,'heading')+label('02 / SPACE & SCALE',1690,65,1430,65,'heading')+line(80,156,3040)
colors=[('Midnight',NIGHT,'6 / 20 / 38','84 / 47 / 0 / 85'),('Blue',BLUE,'8 / 127 / 189','96 / 33 / 0 / 26'),('Cyan',CYAN,'19 / 200 / 244','92 / 18 / 0 / 4'),('Pure White',WHITE,'255 / 255 / 255','0 / 0 / 0 / 0')]
for i,(name,color,rgb,cmyk) in enumerate(colors):
 x=80+i*378
 b3+=box('surface',x,220,345,285,extra=f'background:{color}')+label(name,x,538,345,46,'',extra='font-weight:600;font-size:34px')+label(color,x,600,345,38,'small')+label('RGB  '+rgb,x,650,345,66,'small')+label('CMYK  '+cmyk,x,725,345,70,'small')+label('Pantone: unassigned',x,807,345,70,'small')
b3+=label('CMYK values are nominal conversions, not press-profile targets.',80,915,1490,55,'note')+label('Pantone spot matching requires a physical coated / uncoated swatch approval.',80,982,1490,80,'note')+label('Cyan is reserved for the 2.5-unit precision ring. No gradients or glow.',80,1090,1490,70,'note')
# clearspace uses actual full icon width: x=857? full x21.5..878.5 = 857? terminals rings x22..878 =>856.
# Center icon at 2098,420, rendered width 428, protection = one full icon span each side.
b3+=label('Clearspace protection zone · x = full icon diameter',1690,200,1430,45,'small')
(R/'clearspace-icon.svg').write_text(svg(*logo(layout='icon')).replace('viewBox="0 0 900 600"','viewBox="22 62 856 476"').replace('width="900" height="600"','width="856" height="476"'))
b3+=box('surface',2000,280,750,639,extra='border:1px dashed #40566A')
b3+=img('../review/clearspace-icon.svg',2250,530,250,139,'Full icon with one diameter clearspace')
b3+=line(2000,470,250,1)+label('1.0x',2070,420,150,40,'small')+line(2500,470,250,1)+label('1.0x',2570,420,150,40,'small')
b3+=label('1.0x',2300,340,180,40,'small')+label('1.0x',2300,790,180,40,'small')+label('Minimum edge clearance: one full icon width on all four sides.',1730,940,1300,50,'note')
b3+=label('Small-scale legibility · actual pixels / unmodified master',1690,1010,1430,45,'small')
for i,size in enumerate((64,32,24,16)):
 x=1740+i*330
 b3+=img('../exports/'+NAMES[4],x,1100,size,round(size*600/900),f'{size}px icon')+label(f'{size}px'+(' / favicon' if size==16 else ''),x,1195,300,40,'small')
b3+=label('At 16–24px the open terminals soften; use ≥64px for full circuit detail.',1690,1255,1430,65,'note')
b3+=line(80,1360,3040)+label('03 / CORPORATE IT APPLICATIONS',80,1410,1900,65,'heading')+label('04 / DELIVERY INDEX',2130,1410,990,65,'heading')
# Flat physical layouts, no fake personal data or contact information.
b3+=box('surface',80,1540,840,465)+img('../exports/'+NAMES[0],125,1620,750,111,'Business card front')+label('IT OPERATIONS',125,1880,750,50,'small')
b3+=box('surface',960,1540,840,465,extra=f'background:{NIGHT}')+img('../exports/'+NAMES[1],1005,1705,750,111,'Business card reverse')
b3+=label('Business card · front / reverse · 85 × 47 mm',80,2040,1720,55,'small')
b3+=box('surface',1840,1540,240,465)+img('../exports/'+NAMES[4],1880,1590,160,107,'IT operations badge')+label('IT',1880,1760,160,65,'heading')+label('OPERATIONS',1860,1845,200,35,'small',extra='font-size:22px')+label('ACCESS PASS',1860,1900,200,35,'small',extra='font-size:22px')+label('ID / 54 × 105 mm',1840,2040,240,60,'small')
entries=['01–08   Eight path-only SVG variants','09         Light horizontal / 3200px RGBA','10         Midnight horizontal / 3200px RGBA','11         Standalone icon / 3200px RGBA','12         AI / PDF 1.5 / eight artboards','13         EPS / PostScript Level 3','14         Guidelines + vector artwork / PDF','15         ZIP / fourteen production files']
for i,t in enumerate(entries):b3+=label(t,2130,1540+i*66,990,45,'small')
b3+=label('Light ground → midnight right half. Dark ground → white right half.',80,2145,1960,70,'note')+label('Original identity / flat artwork / no tagline',2130,2145,990,70,'note')+footer(3,'COLOR, REPRODUCTION & APPLICATION')
write_board('board3_guidelines_and_it_identity',b3)

# Compact responsive download page, with real local download links.
boards=['board1_hero_light_and_midnight_lockups','board2_8_versions_and_bezier_geometry','board3_guidelines_and_it_identity']
web='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Smart Blink IT — Precision vector identity</title><style>@font-face{font-family:Plex;src:url('assets/fonts/IBMPlexSans-400.ttf')}@font-face{font-family:Space;src:url('assets/fonts/SpaceGrotesk-600.ttf')}*{box-sizing:border-box}body{margin:0;background:#fff;color:#061426;font-family:Plex,sans-serif}main{max-width:1600px;margin:auto;padding:40px 24px}header{display:flex;justify-content:space-between;gap:24px;align-items:baseline;border-bottom:1px solid #d8e0e8;padding-bottom:24px}h1,h2{font-family:Space;letter-spacing:-.03em}h1{font-size:32px;margin:0}a{color:#061426;text-underline-offset:5px}a:hover{color:#087FBD}a:focus-visible{outline:2px solid #087FBD;outline-offset:5px}a:active{color:#40566a}.boards{margin:32px 0}.boards img{display:block;width:100%;height:auto;margin:0 0 24px;border:1px solid #d8e0e8}.variants{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}figure{margin:0;min-width:0}figure img{width:100%;height:210px;object-fit:contain;border:1px solid #d8e0e8;padding:20px}figcaption{padding:12px 0;font-size:15px}.white-art{background:#061426}.files{display:flex;flex-wrap:wrap;gap:24px;margin:32px 0}footer{border-top:1px solid #d8e0e8;padding:24px 0;color:#40566a}@media(max-width:650px){header{display:block}header a{display:inline-block;margin-top:20px}.variants{grid-template-columns:1fr}main{padding:24px 16px}h1{font-size:26px}figure img{height:160px}}</style><main><header><h1>Smart Blink IT / Vector identity</h1><a href="exports/Smart_Blink_IT_Vector_Master_Pack.zip" download>Download complete vector pack ↗</a></header><section class="boards" aria-label="Brand presentation">'''
for name in boards:web+=f'<a href="deliverables/{name}.jpg"><img src="deliverables/{name}.jpg" alt="{name.replace("_"," ")}" width="3200" height="2400"></a>'
web+='</section><h2>Eight production variants</h2><section class="variants">'
for i,(name,title) in enumerate(zip(NAMES,TITLES)):web+=f'<figure><img class="{"white-art" if i==6 else ""}" src="exports/{name}" alt="{title}"><figcaption><a href="exports/{name}" download>{i+1:02d} / {title} — SVG</a></figcaption></figure>'
web+='</section><nav class="files" aria-label="Production files">'
for name,caption in [('SmartBlinkIT_Master_Vector.ai','Editable AI / PDF 1.5'),('SmartBlinkIT_Master_Vector.eps','EPS / Level 3'),('SmartBlinkIT_Brand_Guidelines_and_Vectors.pdf','Brand guidelines / PDF')]:web+=f'<a href="exports/{name}" download>{caption}</a>'
web+='</nav><footer>V2 · Eight outlined variants · Three presentation sheets · No tagline</footer></main></html>'
(ROOT/'index.html').write_text(web)
geometry={'trace_width_units':24,'center_radius':83.5,'halo_width':2.5,'cap_height_y':CAP-250,'dot_top_y':CAP-250,'dot_radius':DOT_R,'axis_x':450,'solid_terminals_per_side':4,'compound_ring_terminals_per_side':3,'hero_art_width_fraction':3040/W*(4037.728-22)/3200,'original_size':[462,86]}
(R/'geometry.json').write_text(json.dumps(geometry,indent=2))
print('Built eight SVGs, eight-artboard PDF 1.5 AI, Level 3 EPS, three HTML boards and index.')
