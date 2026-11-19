import sys,json
T='/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/pkg/work/tree_r1';sys.path.insert(0,T)
from unittest.mock import patch
from tests.test_batched_routed_decode import fixture,varied,Script
from student_pilot import carrier_c1_decode as D, carrier_c1_batch_decode as BD
out={}
model,p,batch=fixture();rows=varied(batch)
model.config.text_config.max_position_embeddings=rows[-1]['input_ids'].shape[1]+3
sc=[[40,41],[32],[42]*6,[40,41]]
for name,exc in (('integrity_ValueError',ValueError('ARTIFACT_FIXED_READOUT_CONSTANT_MISMATCH')),('CallError',D.CallError('bad call')),('RowRefusal',BD.RowRefusal('declared'))):
    with patch.object(BD.Row,'step',side_effect=exc):
        try: o=D.generate(model,p,rows,logits_processor=[Script(s) for s in sc]); out[name+'_batch']=[(r['finish'],r.get('refusal','')[:50]) for r in o]
        except Exception as e: out[name+'_batch']='RAISE '+type(e).__name__+': '+str(e)[:80]
print(json.dumps(out,indent=1))
