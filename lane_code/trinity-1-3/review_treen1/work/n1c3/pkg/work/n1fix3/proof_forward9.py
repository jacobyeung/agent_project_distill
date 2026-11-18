"""Real producer/reader/forward with the bound final recipe and supervised gradients."""
import copy,json,os,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';T=L/'work/tree_r1';O=B/'proofs/forward'
O.mkdir(exist_ok=True);sys.path[:0]=[str(T),str(B)]
os.environ['R2_FIXTURES']=str(L/'fixtures');os.environ['R2_PROOFS']=str(O)
from monitor9 import Monitor
monitor=Monitor(T)
import torch
from student_pilot.r2_materialize import materialize
from student_pilot.carrier_c1_run import Rows
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.carrier_c1 import CarrierC1
from student_pilot.p3_provenance import load
from tests import test_r2_data_path as D
from tests.test_r2_families import ground
from tests.test_carrier_c1 import fixture
from transformers import Qwen3_5ForConditionalGeneration
torch.manual_seed(7)
root=O/'input';root.mkdir(exist_ok=True)
row=ground(root,'recovery');manifest=D.manifest(root/'manifest',[row],'routing','recovery')
os.environ['STUDENT_FRAME_ROOT_MAP']=json.dumps({'/logical/r2':str(root/'frames')})
produced=materialize([manifest],O/'store');assert produced['status']=='ready'
receipt=load(produced['receipt']['path']);receipt['b7_inputs']={'fixture_binding':True}
reader=Rows(receipt,D.TinyProcessor())
try:batch,_,audit=reader.get('routing',0)
finally:reader.close()
native,_,_=fixture(depth_enabled=False)
cfg=copy.deepcopy(native.config);cfg.text_config.vocab_size=512
recipe=recipe_for(load(B/'inputs/config.json'))
model=CarrierC1(Qwen3_5ForConditionalGeneration(cfg).float(),dict(embed_dim=64,num_heads=4,
    trunk_depth=4,refine_iterations=4,weight_gravity=1.,weight_scale=1.,
    supervision={'path':'/fixture','sha256':'a'*64}),{},5,training_mode='final',depth_enabled=False,
    frame_layout='duplicate',frame_count=32,recipe=recipe)
result=model(batch,stream='routing')
assert torch.isfinite(result['loss']) and result['loss'].item()>0
assert int((batch['labels']!=-100).sum())>0 and audit['tool_spans']>0
result['loss'].backward()
gradients=sum(p.grad is not None and bool(torch.isfinite(p.grad).all()) and bool(p.grad.abs().sum()>0)
              for p in model.parameters())
assert gradients>0
record=dict(status='PASS',loss=float(result['loss'].detach()),supervised_tokens=int((batch['labels']!=-100).sum()),
    nonzero_finite_gradient_tensors=gradients,recipe_source=str(B/'inputs/config.json'),routing_weight=recipe['weights']['routing'],
    real_functions=['r2_materialize.materialize','r2_intake.intake','carrier_c1_run.Rows.get','carrier_c1_routing.encode','CarrierC1.forward'],
    standins='Tiny native Qwen and pose-head weights and lossless tokenizer/processor at the pretrained/GPU boundary; synthetic RGB and recorded response fixture. Real producer, store, reader, RGB loader, response masking, final recipe, forward and backward.',
    limitations='No real pretrained weights, deployed frozen towers, real-scene RGB, or product inference acceptance.')
(O/'RESULT.json').write_text(json.dumps(record,indent=2)+'\n');monitor.save(O);print(json.dumps(record))
