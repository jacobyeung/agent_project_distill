"""Conservative local inference import closure for the independent acceptance lane."""
import ast,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';P=L/'work/merge11/proofs/n1/audit'
initial=json.loads((P/'INFERENCE_COMPONENTS.json').read_text());seeds=initial.get('seed_scope',initial['scope'])
def resolve(name):
 parts=name.split('.')
 if parts[0]=='derivgen':parts=['generator','derivgen_v7',*parts]
 if parts[0]=='vggt':parts=['student_pilot','g3t_vendor',*parts]
 path=T.joinpath(*parts)
 for candidate in (path.with_suffix('.py'),path/'__init__.py'):
  if candidate.is_file():return str(candidate.relative_to(T))
 return None
pending=list(seeds);seen=set();components=[];files={};edges=[]
while pending:
 name=pending.pop()
 if name in seen:continue
 seen.add(name);path=T/name
 if not path.is_file():continue
 raw=path.read_bytes();parsed=ast.parse(raw);files[name]=hashlib.sha256(raw).hexdigest()
 package=list(path.relative_to(T).parts[:-1])
 for node in ast.walk(parsed):
  targets=[]
  if isinstance(node,ast.Import):targets=[a.name for a in node.names]
  elif isinstance(node,ast.ImportFrom):
   prefix=package[:len(package)-node.level+1] if node.level else []
   if node.module:prefix+=node.module.split('.')
   targets=['.'.join(prefix)]+['.'.join([*prefix,a.name]) for a in node.names if a.name!='*']
  elif isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='import_module' and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):
   targets=[node.args[0].value]
  for target in targets:
   source=resolve(target)
   if source:
    pending.append(source);edges.append(dict(caller=name,line=node.lineno,source=source))
 for node in parsed.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
   components.append(dict(file=name,line=node.lineno,component=node.name,
    classification='Local function in conservative inference import closure; dynamic forward scope unproved'))
  elif isinstance(node,ast.ClassDef):
   for method in node.body:
    if isinstance(method,(ast.FunctionDef,ast.AsyncFunctionDef)):
     components.append(dict(file=name,line=method.lineno,component=node.name+'.'+method.name,
      classification='Class method in inference import closure; registration and forward execution require acceptance evidence'))
  elif isinstance(node,(ast.Assign,ast.AnnAssign)):
   value=node.value
   if isinstance(value,(ast.Dict,ast.List,ast.Tuple,ast.Set,ast.Constant)):
    targets=node.targets if isinstance(node,ast.Assign) else [node.target]
    names=[x.id for target in targets for x in ast.walk(target) if isinstance(x,ast.Name)]
    if names:components.append(dict(file=name,line=node.lineno,component=', '.join(names),classification='Module-level literal or table outside registered weights'))
components.sort(key=lambda r:(r['file'],r['line']))
focus={
 ('student_pilot/carrier_c1_routing.py','query_tensor'):'Builds the depth stencil and query coordinates outside the model forward pass.',
 ('student_pilot/carrier_c1_routing.py','OwnGeometry.pose'):'Converts pose outputs to public geometry and degrees.',
 ('student_pilot/carrier_c1_routing.py','render_full'):'Serializes responses and reasoning into text tokens.',
 ('student_pilot/carrier_c1_batch_decode.py','Row.step'):'Controls token emission and reserved-token masking outside forward.',
 ('student_pilot/carrier_c1_batch_decode.py','Row._call'):'Dispatches decoded calls and injects rendered response tokens.',
 ('student_pilot/carrier_c1_decode.py','parse_head'):'Parses generated calls and checks frame arguments.',
 ('student_pilot/carrier_c1_decode.py','respond_state'):'Dispatches responses and converts reader exceptions to typed output.',
 ('student_pilot/geometry_profiles.py','ProfileGeometry.lift'):'Computes geometry from coordinates and depth outside registered weights.',
 ('trace_format/box_v313.py','public_fields'):'Computes public box fields and degree values.',
 ('trace_format/box_v313.py','ground'):'Computes grounding statuses and serialized responses.',
 ('trace_format/box_v313.py','provider_for'):'Chooses the existing box provider according to the configured geometry mode.',
 ('trace_format/box_v313.py','PolicyBoxProvider.__call__'):'Applies the existing fitted-box policy outside weights.',
 ('student_pilot/mdg_decode.py','threshold'):'Reads and validates the artifact threshold outside the model forward pass.',
 ('student_pilot/mdg_decode.py','predict'):'Invokes the head and postprocesses its outputs in a decoder helper.',
}
confirmed=[dict(r,operation=focus[(r['file'],r['component'])]) for r in components if (r['file'],r['component']) in focus]
assert len(confirmed)==len(focus)
value=dict(seed_scope=seeds,scope=sorted(files),source_hashes=files,import_edges=edges,components=components,
 known_outside_forward=confirmed,
 limitation='Conservative local static import closure includes support/training functions imported by inference modules. Dynamic dispatch and external dependencies are not proven complete. EAT traces establish only exercised tiny-reader paths; no production acceptance is claimed.')
(P/'INFERENCE_COMPONENTS.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(dict(files=len(files),components=len(components),source='work/merge11/proofs/n1/audit/INFERENCE_COMPONENTS.json')))
