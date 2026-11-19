"""Source-backed inventories for review; does not infer passing acceptance."""
import ast,collections,hashlib,json,re
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';B=L/'work/build8'
P=B/'proofs/audit';P.mkdir(parents=True,exist_ok=True)
scope=(L/'work/design/eat1_b03/work/nextleg/static/SCOPE_READ.txt').read_text().splitlines()
names=[]
for line in scope:
 for prefix in ('student_pilot/','trace_format/','evalpath/','ofs/','verifykit/'):
  if prefix in line:names.append(prefix+line.split(prefix,1)[1]);break
inventory=[]
for name in names:
 p=T/name
 if not p.is_file():continue
 source=p.read_text();parsed=ast.parse(source)
 for node in parsed.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
   inventory.append(dict(file=name,line=node.lineno,component=node.name,
      classification='module-level function; outside registered model weights'))
  elif isinstance(node,ast.ClassDef):
   for method in node.body:
    if isinstance(method,(ast.FunctionDef,ast.AsyncFunctionDef)):
     inventory.append(dict(file=name,line=method.lineno,component=node.name+'.'+method.name,
       classification='reader/backend class; model registration and forward scope must be judged by EAT-1'))
(P/'INFERENCE_COMPONENTS.json').write_text(json.dumps(dict(scope=names,components=inventory,
 limitation='Conservative source inventory. Dynamic reachability is reported separately by the two tiny EAT-1 adapters; no real RGB read was available.'),indent=2)+'\n')
resizes=[];units=[];empty=[]
for p in T.rglob('*.py'):
 name=str(p.relative_to(T))
 if name.startswith(('tests/','generator/')):continue
 for n,line in enumerate(p.read_text().splitlines(),1):
  if re.search(r'ndimage\.zoom|\.resize\(|F\.interpolate\(|functional\.interpolate\(',line):
   resizes.append(dict(file=name,line=n,text=line.strip(),portrait_aspect_distorted=(True if 'ndimage.zoom' in line else 'requires transform-context review')))
  if name in names and re.search(r'degrees\(|radians\(|\.2f|\.4f|\bround\(',line):
   units.append(dict(file=name,line=n,text=line.strip(),classification='Tool/geometry formatting candidate; not proof of final-answer rewriting'))
  if 'remove_files' in line:
   empty.append(dict(file=name,line=n,text=line.strip()))
(P/'RESIZE_AUDIT.json').write_text(json.dumps(resizes,indent=2)+'\n')
(P/'NUMBER_PATHS.json').write_text(json.dumps(units,indent=2)+'\n')
(P/'EMPTY_EXCLUSION_LISTS.json').write_text(json.dumps(empty,indent=2)+'\n')
old=json.loads((L/'work/build6/SUITE_COMPARISON.json').read_text())
regressions=[r for r in old['failures'] if not r['preexisting']]
(P/'BUILD6_REGRESSIONS.json').write_text(json.dumps(regressions,indent=2)+'\n')
pins={str(p.relative_to(L)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
      (L/'work/design/R0_SCENES.json',L/'work/design/R0_ROOMS.txt',L/'work/design/R0_DEV_ROOMS.txt',T/'student_pilot/trace_grammar.py')}
(P/'AUTHORITY_HASHES.json').write_text(json.dumps(pins,indent=2)+'\n')
frame_sites=[]
for name in ('student_pilot/carrier_c1_routing.py','student_pilot/ground_v3.py',
             'student_pilot/s1_grounding.py','student_pilot/ground_sources.py',
             'student_pilot/stageb_mdg.py','student_pilot/carrier_c1_data.py',
             'generator/derivgen_v7/derivgen/camera_rows.py'):
 p=T/name
 if not p.exists():continue
 for n,line in enumerate(p.read_text().splitlines(),1):
  if re.search(r'\b32\b|range\(1,\s*33\)',line):
   frame_sites.append(dict(file=name,line=n,text=line.strip(),status='Requires frame-count propagation or compatibility proof; not a qualified 64-frame path'))
(P/'FRAME64_REMAINING_SITES.json').write_text(json.dumps(frame_sites,indent=2)+'\n')
print(json.dumps(dict(scope_files=len(names),components=len(inventory),resize_sites=len(resizes),format_sites=len(units),prior_regressions=len(regressions))))
