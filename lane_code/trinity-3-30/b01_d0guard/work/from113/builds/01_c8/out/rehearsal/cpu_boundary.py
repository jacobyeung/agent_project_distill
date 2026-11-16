"""CPU fixtures confined to loading, forward/prefill, and token generation.

No request, mask, geometry, parity, scoring, or admission validator is replaced.
The harness is unexecuted until the specified runtime and streamed inputs exist.
"""
import ast
from copy import deepcopy
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace as NS

B=Path(__file__).resolve().parents[2]
W=B.parents[1]/'work'

def install(root,dest):
    import numpy as np
    import torch
    import common
    import nomdg as N
    import geometry as G
    import perception as P
    import read_runtime
    import kernels
    from evalpath import runtime
    from student_pilot import carrier_c1_run as trainer
    from student_pilot import carrier_c1_decode as decoder
    from trace_format.program_errors import ProgramRefusal
    for name in ('synchronize','reset_peak_memory_stats'):
        setattr(torch.cuda,name,lambda *a,**k:None)
    for name in ('max_memory_allocated','max_memory_reserved'):
        setattr(torch.cuda,name,lambda *a,**k:0)
    original_move=common.move_batch
    def cpu_move(batch,device):return original_move(batch,'cpu')
    common.move_batch=N.move_batch=G.move_batch=cpu_move

    manifest=json.loads((W/'p9/native/geometry/GEOMETRY_MANIFEST.json').read_text())
    captures={r['clip']:r for r in manifest['records']}
    journal=[json.loads(s) for s in (W/'p9/native/probe/items.jsonl').read_text().splitlines() if s]
    recorded={r['key']:r['decode'] for r in journal if r['arm']=='unflagged' and 'decode' in r}
    probe=json.loads((W/'p9/native/probe/PARITY_DECODE.json').read_text())
    family=json.loads((B/'out/c8/FAMILY_C8.json').read_text())
    tasks,frames=N.tasks_and_captures(family['worker_contract']['inputs'])
    tasks=[t for t in tasks if N.family(t['question_type']) in N.FAMILIES]
    references=N.load(N.checked(family['worker_contract']['inputs']['references']))
    raw=N.load(N.checked(family['worker_contract']['raw_tower']))
    checks=[]
    generation_count=0

    def task_for(processor,batch):
        text=processor.tokenizer.decode(batch['input_ids'][0].tolist(),skip_special_tokens=False)
        hits=[t for t in tasks if t['question'] in text]
        if len(hits)>1:
            clip=batch['video_sha256']
            hits=[t for t in hits if t['native']==captures[clip]['native']]
        if len(hits)!=1:raise ValueError('Fixture cannot identify the real prompt question')
        return hits[0]

    class Model:
        trace_program_version='3.14'
        def __init__(self,processor):
            self.processor=processor
            from student_pilot.camera_targets import carrier_id
            self.carrier_id=carrier_id(processor.tokenizer)
            self.query_index=0
        def named_modules(self):return []
        def hidden(self,batch,carriers=True):
            ids=batch['input_ids']
            next_ids=torch.cat((ids[:,1:],torch.full_like(ids[:,:1],self.processor.tokenizer.eos_token_id)),1)
            return next_ids.unsqueeze(-1).float()
        def lm_head(self,hidden):
            ids=hidden[...,0].long()
            logits=torch.full((len(ids),len(self.processor.tokenizer)),-100.)
            logits[:,0]=-10.
            logits[torch.arange(len(ids)),ids]=10.
            return logits
        def readout_heads(self,hidden,batch,uv):
            heads=probe['heads']
            result=dict(pose=torch.tensor(heads['pose9'],dtype=torch.float64)[None],
                        gravity=torch.tensor(heads['gravity'],dtype=torch.float64)[None])
            if uv is not None:
                q=heads['depth_queries'][self.query_index]
                self.query_index+=1
                depth=torch.full((32,uv.shape[1]),2.,dtype=torch.float64)
                depth[q['frame']-1]=torch.tensor(q['depth'],dtype=torch.float64)
                result['depth']=depth
            else:self.query_index=0
            return result

    def load_model(config_pin,artifact_pin,data_pin,*,device,selected_trainer):
        cfg,receipt,model_manifest=read_runtime.prepared(config_pin,artifact_pin,data_pin)
        trainer_pin=runtime.verify_trainer(selected_trainer,cfg.get('code'))
        init_spec=runtime.check_init_spec(receipt,artifact_pin)
        processor=trainer.processor_for_receipt(model_manifest,receipt)
        model=Model(processor)
        info=dict(fixture=True,kind='routed',artifact=artifact_pin,step=N.load(artifact_pin['path'])['step'],
                  init_spec=init_spec,trainer=trainer_pin,config=config_pin,data_receipt=data_pin,
                  preparation=cfg['preparation'],read_runtime_sha256=N.sha(read_runtime.__file__),
                  boundary='No model weights loaded; real preparation/source/processor authentication executed')
        checks.append(info)
        return model,processor,info
    read_runtime.load_model=load_model

    def prefill(model,processor,batch,**kwargs):
        capture=captures[batch['video_sha256']]
        p=N.checked(raw['captures'][capture['native']])
        with np.load(p,allow_pickle=False) as z:depth=np.asarray(z['depth_grid'],float)
        with np.load(W/'p9/native/geometry'/(capture['clip']+'.npz'),allow_pickle=False) as z:
            scale=float(z['scale'])
        own=np.maximum(depth*scale,.0001)
        class DepthHead:
            def query(self,state,uv):
                if tuple(uv.shape)!=(32,51*51,2):raise ValueError('Unexpected prefill depth query')
                return torch.tensor(own.reshape(32,-1),dtype=torch.float64)
        heads=NS(depth_map=torch.zeros((32,1)),gravity=np.asarray(capture['diagnostics']['head_gravity']),
                 depth_head=DepthHead())
        return NS(heads=heads)
    decoder._prepare_decode=prefill

    def budgeted(processor,text,calls,heads,fire=False):
        Q=N.Q;tokenizer=processor.tokenizer
        guard=Q.ThinkingBudget(tokenizer,Q.DECODE_BUDGET,openers=processor._routing_tokens['ids'].values())
        ids=[]
        candidates=tokenizer.encode(text,add_special_tokens=False)+[tokenizer.eos_token_id]
        if fire:
            filler=tokenizer.encode('thinking ',add_special_tokens=False)[0]
            candidates=[filler]*(Q.DECODE_BUDGET['thinking_tokens']+200)
        logits=torch.zeros((1,len(tokenizer)))
        for candidate in candidates:
            logits.fill_(-100.);logits[0,candidate]=10.
            result=guard(ids,logits)
            token=int(result.argmax(-1)[0]);ids.append(token)
            if token==tokenizer.eos_token_id:break
        decoded=dict(text=tokenizer.decode(ids,skip_special_tokens=False),calls=calls,heads=heads,
                     tokens=ids,generated_tokens=len(ids),errors=sum(c['kind']=='error' for c in calls),finish='eos')
        return Q.apply_budget(decoded,guard)

    def generate(model,processor,batch,geometry,ground_backend=None,tap=None,budget=None):
        nonlocal generation_count
        if geometry is None:
            decoded=deepcopy(probe)
            if tap is not None:
                from evalpath.parity import injected_positions
                injected=injected_positions(decoded)
                for index,token in enumerate(decoded['tokens']):
                    if index not in injected:
                        tap.positions[index]=dict(token=token,top2=[token,0],logits=[10.,-10.],margin=20.)
            return decoded
        task=task_for(processor,batch);key='devrows:'+task['id']
        generation_count+=1
        if generation_count==3:
            raise ProgramRefusal('fixture_program_refusal')
        if key in recorded and generation_count not in (1,2,4):
            return deepcopy(recorded[key])
        calls=P.script_calls(task,references)
        if generation_count==4:calls=['<move from=0 to=33>']
        script=P.execute_calls(geometry,ground_backend,calls)
        # Actual dispatch computes responses. Only model-authored token output is scripted.
        for call in script['calls']:call.update(at_token=0,forced_tokens=0)
        answer=P.script_answer(task,script) if not script['errors'] else None
        text='fixture reasoning\n</think>\n\n'+(answer or '')
        decoded=budgeted(processor,text,script['calls'],script['heads'],fire=generation_count==1)
        if generation_count==1:decoded['strict_no_answer']=True
        return decoded
    P.generate=generate

    # The real cache-bind CLI must reproduce the shipped draft receipt exactly.
    old=N.load(Path(N.__file__).parents[2]/'orchard_native/MASK_CACHE_P6_BOUND.json')
    rebound=Path(dest)/'MASK_CACHE_REBOUND.json'
    argv=[N.__file__,'cache-bind','--manifest',old['manifest']['path'],
          '--candidates',str(Path(old['binding']['path']).parent),
          '--dense-candidates',str(Path(old['dense_manifest']['path']).parent/'candidates'),
          '--items',old['items']['path'],'--output',str(rebound)]
    previous=sys.argv
    try:
        sys.argv=argv;runpy.run_path(N.__file__,run_name='__main__')
    finally:sys.argv=previous
    if N.load(rebound)!=N.load(family['worker_contract']['mask_cache']['path']):
        raise ValueError('Real cache-bind differs from shipped receipt')
    N.dump(Path(dest)/'CACHE_BIND_PROOF.json',dict(command=argv,output=N.pin(rebound),
        changed_fields=[k for k,v in N.load(rebound).items() if old.get(k)!=v]))

    # Preserve actual source line numbers for coverage of AST-derived kernels.
    def covered_kernel(node,namespace):
        module=ast.fix_missing_locations(ast.Module(body=[deepcopy(node)],type_ignores=[]))
        filename=G.__file__ if node.name in ('native_geometry','native_geometry_restore') else N.__file__
        local=dict(namespace);exec(compile(module,filename,'exec'),local)
        return local[node.name]
    kernels.function=covered_kernel
