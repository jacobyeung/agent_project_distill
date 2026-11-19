import sys,json
T='/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf12/pkg/work/tree_r1';sys.path.insert(0,T)
from tests.test_batched_routed_decode import fixture,varied,Script
from student_pilot import carrier_c1_decode as D
out={}
model,p,batch=fixture();rows=varied(batch)
model.config.text_config.max_position_embeddings=rows[-1]['input_ids'].shape[1]+3
for name,sc in (('old_input_6x42',[[40,41],[32],[42]*6,[40,41]]),('new_input_10x42',[[40,41],[32],[42]*10,[40,41]])):
    try:
        o=D.generate(model,p,rows,logits_processor=[Script(s) for s in sc]);out[name]=[(r['finish'],r.get('refusal','')[:60]) for r in o]
    except Exception as e: out[name]='RAISE '+type(e).__name__+': '+str(e)[:150]
    for i in range(4):
        try: r=D.generate(model,p,rows[i],logits_processor=Script(sc[i])); out[f'{name}_single{i}']=r['finish']
        except Exception as e: out[f'{name}_single{i}']='RAISE '+type(e).__name__+': '+str(e)[:80]
print(json.dumps(out,indent=1))
