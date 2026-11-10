#!/usr/local/bin/python3.11
"""Targeted output checks for the three reported logo defects."""
from pathlib import Path
import json,math
from xml.etree import ElementTree as ET
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'exports';R=ROOT/'review'
def paths(f):return {p.attrib['id']:p.attrib for p in ET.parse(f).getroot() if p.tag.endswith('path')}
def bounds(p):
 pen=BoundsPen(None);parse_path(p['d'],pen);return pen.bounds
light=paths(E/'01_SmartBlinkIT_Primary_Horizontal_Light.svg');dark=paths(E/'02_SmartBlinkIT_Primary_Horizontal_Midnight.svg')
error=0
for key,a in light.items():
 if not key.endswith('-left'):continue
 b=light[key[:-5]+'-right'];pa=RecordingPen();pb=RecordingPen();parse_path(a['d'],pa);parse_path(b['d'],pb)
 assert len(pa.value)==len(pb.value)
 for (opa,ap),(opb,bp) in zip(pa.value,pb.value):
  assert opa==opb
  for (ax,ay),(bx,by) in zip(ap,bp):error=max(error,abs(ax+bx-900),abs(ay-by))
assert error<.00002,error
assert float(light['bracket-left']['stroke-width'])==24
cap=bounds(light['word-BLiNK'])[1];dot=bounds(light['blink-i-dot'])[1]
assert abs(cap-dot)<1e-6,(cap,dot)
assert light['center-disc']['fill']=='#087FBD'
assert dark['word-BLiNK']['fill']=='#FFFFFF'
assert all(p.get('fill')=='#FFFFFF' or p.get('stroke')=='#FFFFFF' for k,p in dark.items() if k.endswith('-right'))
# Ring centers must remain transparent in the final PNG, including under crossing traces.
im=Image.open(E/'05_Standalone_Icon_3000px_Transparent.png').convert('RGBA');sx=im.width/900;sy=im.height/600
holes=[]
for x,y in ((52,218),(132,300),(52,382),(848,218),(768,300),(848,382)):
 alpha=im.getpixel((round(x*sx),round(y*sy)))[3];assert alpha==0,(x,y,alpha);holes.append(alpha)
assert sum(k.startswith('terminal-') for k in light)==8
assert sum(k.startswith('ring-') for k in light)==6
for k,p in light.items():
 if k.startswith('ring-'):assert p.get('fill-rule')=='evenodd'
# Reject unsupported drawing primitives and quadratic / arc commands in final production files.
import re
for f in E.glob('*.svg'):
 for p in paths(f).values():assert set(re.findall('[A-Za-z]',p['d']))<={'M','L','C','Z'}
# Check local links resolve, including the docs mirror.
from html.parser import HTMLParser
class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,tag,attrs):
  self.refs.extend(v for k,v in attrs if k in ('src','href'))
for page in (ROOT/'index.html',ROOT/'docs/index.html'):
 parser=Links();parser.feed(page.read_text())
 for ref in parser.refs:assert (page.parent/ref).exists(),ref
# EPS uses actual editable paths, not an embedded bitmap or outlined font dependency.
eps=(E/'SmartBlinkIT_Master_Vector.eps').read_text()
assert '%%LanguageLevel: 3' in eps and 'curveto' in eps and 'eofill' in eps
assert not any(t in eps for t in ('colorimage','findfont','imagemask'))
result={'mirror_max_error_units':error,'i_cap_height_error_units':abs(cap-dot),'stroke_width_units':24,'center_fill':light['center-disc']['fill'],'right_side_dark_fill':'#FFFFFF','ring_center_alpha':holes,'solid_terminal_count':8,'hollow_terminal_count':6,'path_commands':'M L C Z only','local_download_links':'pass','eps_level3_path_structure':'pass; no native PostScript interpreter available'}
(R/'geometry-checks.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
