from common import *
import ast,types
from unittest.mock import patch
from types import SimpleNamespace
from student_pilot import carrier_c1_run as C,carrier_c1_data as E,pose_samples as P
from student_pilot.b7_inputs import layout
from student_pilot.r1_handover import compare_configs
import numpy as np
source=(L/'work/build24m4j/p_tree/student_pilot/carrier_c1_run.py').read_text()
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='processor_for_receipt')
code=compile(ast.Module(body=[node],type_ignores=[]),'<P-original-function>','exec')
fn=types.FunctionType(next(c for c in code.co_consts if isinstance(c,types.CodeType)),vars(C))
row=dict(dataset='fixture',scene='room',target='A',student_input=dict(question='Q',frames=[{}]*32,frame_indices=list(range(32)),timestamps=[i/30 for i in range(32)],fps=30,total_num_frames=32))
records=[]
for p in sorted((D/'p_configs').glob('*.json')):
 cfg=J.load(p);r=dict(file=p.name,sha256=J.sha(p),explicit_fields={k:cfg.get(k) for k in ('min_pixels','max_pixels','frame_count','frame_layout','frame_markers')})
 try:layout(cfg)
 except ValueError as e:assert str(e)=='processor_resolution_pin_missing';r['direct_layout_refusal']=str(e)
 else:raise AssertionError('P unexpectedly carries pixel pins')
 desired=dict(cfg,min_pixels=16384,max_pixels=147456,frame_count=32)
 r['explicit_layout']=layout(desired)
 captured=[]
 def capture(proc,q,options,arrays,metadata,target,pixels,limit):captured.append(dict(pixels=pixels,frames=len(arrays),indices=metadata.frames_indices));return {},{}
 with patch.object(C,'processor_for',side_effect=lambda *a:SimpleNamespace(tokenizer=SimpleNamespace())),patch.object(C.rehearsal,'fixture_manifest',return_value={}),patch.object(C.routing,'add_routing_tokens'),patch.object(P,'load_frames',return_value=np.zeros((32,2,2,3),dtype=np.uint8)),patch.object(P,'encode_frames',side_effect=capture):
  processor=fn({'root':'unused'},cfg)
  assert not hasattr(processor,'_b7_layout') and processor.tokenizer._c1_frame_markers
  E.encode_layout_row(processor,row,'duplicate',None)
 assert captured[0]['pixels']==(16384,147456) and captured[0]['frames']==64
 r['synthetic_encode']=captured[0];records.append(r)
J.write(D/'P_CONFIG_TESTS.json',dict(status='PASS',records=records,scope='Four real P configs; original P processor function; synthetic frame input and final processor call stubbed'))
print('P CONFIGS PASS',len(records))
