from common import *
import ast,copy,difflib,traceback
from unittest.mock import patch
from types import SimpleNamespace
from student_pilot import r1_handover as H,carrier_c1_run as C,carrier_c1_data as E,pose_samples as P
from student_pilot.b7_inputs import layout
from student_pilot.p3_provenance import digest
import numpy as np

# Use authenticated member replicas recovered from the supplied resolver archive.
records=[]
replicas={p.name:str(p) for p in (D/'inputs').iterdir() if p.is_file() and len(p.name)==64}
source=J.load(input_file('b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad'))
for name in NAMES:
 for fname in ('c','n'):
  cfg=J.load(D/'configs'/name/(fname+'.json'));candidate=J.load(D/'candidate'/name/(fname+'.json'))
  for tag,v in (('current',cfg),('candidate',candidate)):
   r=dict(kit=name,config=fname,variant=tag,scope='Real configurations and authenticated metadata; no comparison stubs')
   try:H.compare_configs(source,v,replicas=replicas);r['compare']='PASS'
   except ValueError as e:r['compare_refusal']=str(e)
   if tag=='candidate':assert r.get('compare_refusal')=='P_EXPORT_CONFIG_DIFFERENCE:max_pixels',r
   else:assert r.get('compare')=='PASS',r
   records.append(r)
J.write(D/'COMPARE_TESTS.json',records)

# The proposed patch is never written into tree C or any kit.
changes={}
p=T/'student_pilot/carrier_c1_run.py';old=p.read_text()
new=old.replace("    if receipt.get('b7_inputs') or receipt.get('r1_training'):\n        from .b7_inputs import layout\n        processor._b7_layout = layout(receipt.get('b7_inputs') or receipt)","    if receipt.get('b7_inputs'):\n        from .b7_inputs import layout\n        processor._b7_layout = layout(receipt['b7_inputs'])")
assert new!=old;changes[str(p.relative_to(T))]=(old,new)
p=T/'launch_r1/entry.py';old=p.read_text()
new=old.replace('    layout(cfg)\n', '''    if cfg.get('b7_inputs'):
        layout(cfg)
    else:
        # The legacy processor uses DEFAULT_PIXELS and does not set _b7_layout.
        from student_pilot.pose_samples import DEFAULT_PIXELS
        if any(cfg.get(key) is not None for key in ('min_pixels', 'max_pixels')):
            raise ValueError('R1_LEGACY_PROCESSOR_PIXELS_MUST_USE_DEFAULTS')
        layout(dict(cfg, min_pixels=DEFAULT_PIXELS[0], max_pixels=DEFAULT_PIXELS[1],
                    frame_count=cfg.get('frame_count', 32)))
''')
assert new!=old;changes[str(p.relative_to(T))]=(old,new)
raw=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n,(a,b) in changes.items())
replace(L/'out/TREE_CHANGE_24M4K.patch',raw)

def function(raw,name,namespace):
 node=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name==name)
 ns=dict(namespace);exec(compile(ast.Module(body=[node],type_ignores=[]),'<proposal-test>','exec'),ns);return ns[name]
proposed=function(changes['student_pilot/carrier_c1_run.py'][1],'processor_for_receipt',vars(C))
p_original=function((L/'work/build24m4j/p_tree/student_pilot/carrier_c1_run.py').read_text(),'processor_for_receipt',vars(C))
def fake():return SimpleNamespace(tokenizer=SimpleNamespace())
out=[]
for name in NAMES:
 cfg=J.load(D/'configs'/name/'c.json');candidate=J.load(D/'candidate'/name/'c.json')
 with patch.object(C,'processor_for',side_effect=lambda *a:fake()),patch.object(C.rehearsal,'fixture_manifest',return_value={}),patch.object(C.routing,'add_routing_tokens'):
  # Functions have copied globals; bind the isolated processor constructor explicitly.
  for fn in (proposed,p_original):fn.__globals__['processor_for']=lambda *a:fake()
  p=p_original({'root':'unused'},source);n=proposed({'root':'unused'},cfg)
  fixed=C.processor_for_receipt({'root':'unused'},candidate)
  try:C.processor_for_receipt({'root':'unused'},cfg)
  except ValueError as e:assert str(e)=='processor_resolution_pin_missing'
  else:raise AssertionError('Current processor unexpectedly passed')
 assert not hasattr(p,'_b7_layout') and not hasattr(n,'_b7_layout')
 assert n.tokenizer._c1_frame_count==32 and n.tokenizer._c1_frame_markers
 row=dict(dataset='fixture',scene='fixture',student_input=dict(question='Q',options=[],frames=[{} for _ in range(32)],frame_indices=list(range(32)),timestamps=[i/30 for i in range(32)],fps=30,total_num_frames=32),target='A')
 captured=[]
 def capture(proc,q,options,arrays,metadata,target,pixels,limit):
  captured.append(dict(pixels=pixels,shape=arrays.shape,indices=metadata.frames_indices,markers=proc.tokenizer._c1_frame_markers));return {},{}
 with patch.object(P,'load_frames',return_value=np.zeros((32,2,2,3),dtype=np.uint8)),patch.object(P,'encode_frames',side_effect=capture):
  for proc in (p,n,fixed):E.encode_layout_row(proc,row,'duplicate',None)
 assert captured[0]==captured[1]==captured[2] and captured[0]['pixels']==(16384,147456)
 out.append(dict(kit=name,synthetic=captured[0],current_refusal='processor_resolution_pin_missing',proposal_matches_P=True,candidate_matches_P_for_this_row=True))
# Execute exactly the changed admission layout block, without granting admission.
node=next(n for n in ast.parse(changes['launch_r1/entry.py'][1]).body if isinstance(n,ast.FunctionDef) and n.name=='admit')
check=next(n for n in node.body if isinstance(n,ast.If) and ast.unparse(n.test)=="cfg.get('b7_inputs')")
checks=[]
for name in NAMES:
 cfg=J.load(D/'configs'/name/'c.json')
 exec(compile(ast.Module(body=[check],type_ignores=[]),'<admission-layout-test>','exec'),dict(cfg=cfg,layout=layout))
 checks.append(dict(kit=name,layout_clause='PASS',full_admission='NOT_RUN'))
J.write(D/'PATCH_TESTS.json',dict(status='PASS',encoding=out,admission_layout=checks,production_rows_tested=False,tree_modified=False))
print('CASE b: P_EXPORT_CONFIG_DIFFERENCE:max_pixels; 8 real config comparisons; proposal processor/admission-layout and synthetic encode PASS')
