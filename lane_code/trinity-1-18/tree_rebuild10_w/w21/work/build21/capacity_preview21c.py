from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
import json,sys,datetime
B=Path(__file__).resolve().parent;L=B.parents[1];C=L/'work/build21c'
sys.path.insert(0,str(B))
import native21 as N
import joblib as J
O=C/'proofs/capacity_preview';O.mkdir(parents=True,exist_ok=True)
raw=(L/'attic/build21c/kit/k/n.json').read_bytes()
cfg0=J.load(B/'kits/q/k/n.json');h=cfg0['benchmark_scene_exclusions']['sha256']
upload=next(x for x in J.load(B/'UPLOADS.json')['files'] if x['opaque_name']=='u/'+h)
staged=O/'h/k'/ (h[:8]+'.json');staged.parent.mkdir(parents=True,exist_ok=True)
staged.write_bytes(J.checked(upload['local_path'],h).read_bytes())
original_open=Path.open
def opened(p,mode='r',*args,**kwargs):
    return original_open(p,mode.replace('x','w') if p.is_relative_to(O) else mode,*args,**kwargs)
result=dict(GO=False,tree_changed=False,staging_changed=True,staged_name=str(staged.relative_to(O)),
    sha256=h,scope='Existing capacity fixture: real staging authentication and q all-rank forward preview; no store regeneration.',
    stand_ins=['Existing synthetic RGB and labels','Existing tiny native model','PatchGridProcessor at processor boundary','CPU'],milestones={})
from student_pilot.source_seal import create
source=J.load(B/'kits/q/k/a.json')['source']
closure={str(p.relative_to(N.T)):N.sha256(p) for p in N.source_files([N.T/'student_pilot/carrier_c1_run.py'])}
code=J.write(O/'code.json',create(N.T,B/'kits/q'/source['path'],closure,{}))
with ExitStack() as stack:
    stack.enter_context(patch.object(Path,'open',opened))
    stack.enter_context(N.P.proof_scope())
    stack.enter_context(patch.object(N.C,'processor_for',N.processor))
    stack.enter_context(patch('student_pilot.decoupled_v_run.processor_for',N.processor))
    for step in (400,600):
        print(datetime.datetime.now(datetime.timezone.utc).isoformat(),step,flush=True)
        root=O/str(step);root.mkdir(exist_ok=True)
        request=N.load(N.O/str(step)/'request.json')
        request['staged_pins'].append(dict(path=str(staged),sha256=h))
        verified=N.Q.verify_staging(request)
        cfg=N.load(N.O/str(step)/'q/h/config.json');value=cfg['r1_training']
        closure=N.P.verify(value['handover_receipt'],value['p_run'],cfg['init_artifact']['artifact'],
            value['persisted_files'],weights=True,proof_mode='q')
        with N.P.scope({**closure['paths'],h:str(staged)}):
            assert N.pinned(cfg['benchmark_scene_exclusions'])==staged
            cfg['code']=code
            aliases={}
            def collect(v):
                if isinstance(v,dict):
                    if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str):
                        aliases[v['sha256']]=N.P.relocated(v)
                    for x in v.values():collect(x)
                elif isinstance(v,list):
                    for x in v:collect(x)
            collect(cfg)
            with N.P.scope({**aliases,**closure['paths'],h:str(staged)}):
                cfg=N.load(N.Q.bind_handover(cfg,root/'h')['path'])
                admission=N.P.admission(cfg,weights=True)
                assert admission['absolute_resume_step']==step
                preview=N.Q.forward(cfg,root,step)
        rows=N.load(root/'f.json')['records']
        baseline=N.load(N.O/str(step)/'q/f.json')['records']
        assert len(rows)==len(baseline) and {r['rank'] for r in rows}=={0,1,2,3} and all(r['finite'] for r in rows)
        for rank in range(4):assert {r['stream'] for r in rows if r['rank']==rank}=={'pose','vqa','routing','pointing'}
        result['milestones'][str(step)]=dict(status='PASS',staged_pins=len(verified),forward=preview,records=len(rows),
            source_seal=source['tree_sha256'],handover_rebound=True,absolute_resume_step=admission['absolute_resume_step'],
            pin_map_checked=len(aliases))
        J.write(O/'RESULT.json',result)
result['status']='PASS';J.write(O/'RESULT.json',result);N.m.save(O)
print(json.dumps(result,indent=2))
