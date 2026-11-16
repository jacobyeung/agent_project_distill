"""Pinned item-list reader using the inherited geometry, prompt and decode code."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import time
from types import SimpleNamespace as NS
from adapter import *
from policy import camera_only,records as call_records
from scorer import final_text,score


def source_pins():
    root=Path(__file__).parent
    return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*.py'))}

def initialize(spec):
    import sys,numpy
    if sys.version_info[:2]!=(3,12) or numpy.__version__!='2.2.6':
        raise ValueError('production Python/numerical overlay differs')
    import paths
    paths.install(spec['tree'])
    import gravity_guard as guard
    from student_pilot import geometry_profiles as GP
    if not guard._installed:guard.install(GP,guard.Recorder())
    return guard

class NativeBoundary:
    synthetic=False
    def __init__(self,spec):
        import common,read_runtime
        from routed import source_pins as sealed_sources
        from evalpath import runtime
        self.spec=spec;self.cfg=load(checked(spec['config']))
        if load(checked(spec['artifact'])).get('step')!=544:raise ValueError('checkpoint step differs')
        selected=dict(root=spec['tree'],sources={n.removeprefix('student_pilot/'):h for n,h in sealed_sources().items() if n.startswith('student_pilot/')})
        self.model,self.processor,self.info=read_runtime.load_model(spec['config'],spec['artifact'],spec['data_receipt'],device=spec['device'],selected_trainer=selected)
    def batch(self,row):
        from evalpath import runtime
        from evalpath.items import assert_prompt_equal
        from common import move_batch
        assert_prompt_equal(self.processor,row)
        return move_batch(runtime.prompt_batch(self.processor,row,self.cfg,'routed'),self.spec['device'])
    def prefill(self,row):
        import torch
        from student_pilot.carrier_c1_decode import _prepare_decode
        from student_pilot.ground_context import closed_adapters
        batch=self.batch(row)
        return closed_adapters(torch.no_grad()(_prepare_decode))(self.model,self.processor,batch,max_new_tokens=16384).heads,batch
    def generate(self,task,row,geo):
        import perception as P,reader_policy as Q
        with camera_only():
            return P.generate(self.model,self.processor,self.batch(row),geo,budget=Q.DECODE_BUDGET)
    def parity(self,task,capture,root,out):
        """Execute the inherited prompt/cache/head parity statements verbatim."""
        import nomdg as N
        from evalpath.parity import LogitTap,p1,p2,p3
        from evalpath.items import assert_prompt_equal
        from evalpath import runtime
        from routed import trainer_row
        source=Path(N.__file__).read_text();tree=ast.parse(source)
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        lines=source.splitlines(True)
        start=next(n.lineno for n in function.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='probe' for t in n.targets))
        end=next(n.end_lineno for n in function.body if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=="trace_state['probe']" )
        block=''.join(line[4:] if line.startswith('    ') else line for line in lines[start-1:end])
        ctx=dict(vars(N));ctx.update(model=self.model,processor=self.processor,info=self.info,cfg=self.cfg,
            first=task,captures={task['native']:capture},request=dict(frames_root=root),args=NS(device=self.spec['device']),
            out=Path(out),selection=dict(items={'camera_displacement':task['id']}),trace_state={},
            assert_prompt_equal=assert_prompt_equal,LogitTap=LogitTap,p1=p1,p2=p2,p3=p3,
            trainer_row=trainer_row,runtime=runtime,emit=lambda *a,**k:None)
        with camera_only():
            exec(compile('\n'*(start-1)+block,str(Path(N.__file__)), 'exec'),ctx)
        return ctx['parity']

def synthetic_tower(bound,out):
    import numpy as np
    from student_pilot.tower_read import GRID_UV,WEIGHTS_SHA256,CONFIG_SHA256,REVISION
    out=Path(out);out.mkdir(parents=True,exist_ok=False);entries={}
    for c in load(checked(bound['inputs']['FRAMES.json']))['captures']:
        pose=np.zeros((32,9));pose[:,0]=np.arange(32)*.03;pose[:,6]=1.;pose[:,7:]=1.
        p=out/(digest(c['native'])+'.npz')
        np.savez(p,raw_pose=pose,depth_grid=np.ones((32,51,51)),depth_conf_grid=np.broadcast_to(np.linspace(1.,2.,51*51).reshape(1,51,51),(32,51,51)),
                 frame_indices=np.array(c['anchor_indices']),anchor_slots=np.arange(32),grid_uv=GRID_UV,
                 source_hw=[480,640],gravity_up=[0.,-1.,0.])
        entries[c['native']]=pin(p)
    manifest=dict(schema='legs1-raw-g3t-cache-v1',synthetic=True,captures=entries,
                  weights_sha256=WEIGHTS_SHA256,config_sha256=CONFIG_SHA256,revision=REVISION,
                  dense_manifest=bound['inputs']['DENSE.json'],fixture_source=pin(__file__))
    dump(out/'RAW.json',manifest);return out/'RAW.json'

def tower(bound,spec,out,synthetic=False):
    if synthetic:return synthetic_tower(bound,out)
    import geometry as G
    started=time.monotonic()
    weights=Path(spec['weights']);receipt=Path(str(weights)+'.RECEIPT.json')
    if not receipt.is_file() or weights.stat().st_size!=5627166200:raise ValueError('complete tower receipt required')
    G.tower(NS(device=spec.get('tower_device',spec['device']),weights=str(weights),config=spec['tower_config'],
               frames=str(checked(bound['inputs']['FRAMES.json'])),dense_manifest=str(checked(bound['inputs']['DENSE.json'])),
               dest=str(out),output_name='RAW.json'))
    result=load(Path(out)/'RAW.json');result['seconds']=time.monotonic()-started
    dump(Path(out)/'RAW.json',result)
    return Path(out)/'RAW.json'

def prepare_geometry(bound,spec,raw_path,out,boundary):
    import numpy as np
    import geometry as G,geometry_refusals as GR,gravity_guard as guard
    from routed import trainer_row
    from student_pilot.tower_read import TowerState,WEIGHTS_SHA256,CONFIG_SHA256,REVISION
    from student_pilot.geometry_profiles import GeometryError
    prepare_started=time.monotonic()
    raw=load(raw_path);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    if raw['dense_manifest']!=bound['inputs']['DENSE.json']:raise ValueError('tower input binding differs')
    if (raw['weights_sha256'],raw['config_sha256'],raw['revision'])!=(WEIGHTS_SHA256,CONFIG_SHA256,REVISION):raise ValueError('tower provenance differs')
    if bool(raw.get('synthetic'))!=boundary.synthetic:raise ValueError('tower/boundary mode differs')
    tasks=rows(checked(bound['inputs']['TASKS.jsonl']));captures=load(checked(bound['inputs']['FRAMES.json']))['captures']
    if set(raw['captures'])!={c['native'] for c in captures}:raise ValueError('tower capture membership differs')
    videos={};dispositions=[]
    artifact=spec['artifact']
    for c in captures:
        started=time.monotonic();task=next(t for t in tasks if t['native']==c['native'])
        row=trainer_row(task,c,bound['frames_root'],verify=True);clip=row['student_input']['video_identity']['video_sha256']
        p=checked(raw['captures'][c['native']]);output=out/(clip+'.npz');diagnostics={}
        def operation():
            if not boundary.synthetic:
                return G.prepare_capture(p,c,row,output,boundary.prefill,diagnostics)
            state=TowerState.from_npz(p)
            if state.frame_indices[state.anchor_slots].tolist()!=c['anchor_indices']:raise ValueError('tower anchors differ')
            depth,up=boundary.prefill(state)
            with np.load(p,allow_pickle=False) as z:
                hw=z['source_hw'];diagnostics['tower_gravity']=z['gravity_up'].tolist()
            return G.convert(state,depth,up,hw,output,diagnostics=diagnostics)
        with guard.capture('r0',c['native']):outcome=GR.attempt(operation,GeometryError)
        rec=dict(native=c['native'],group=c['group'],clip=clip,raw=pin(p),checkpoint=artifact,
                 status=outcome['status'],error=outcome['error'],diagnostics=diagnostics,
                 output=pin(output) if output.is_file() else None,seconds=time.monotonic()-started)
        if outcome['status']=='PASS':rec.update(outcome['data']);videos[clip]=pin(output)
        dispositions.append(rec)
    m=dict(schema=GR.SCHEMA,policy=GR.POLICY,videos=videos,checkpoint=artifact,records=dispositions,
           producer='legs1-own-scale-gravity-v1',producer_sha256=sha(G.__file__),raw_tower=pin(raw_path),
           config=spec['config'],binding=bound['binding'],synthetic=boundary.synthetic,gravity_guard=guard.identity(),
           read_preparation_seconds=raw.get('seconds',0)+time.monotonic()-prepare_started)
    G.validate_manifest(m,artifact,[c['native'] for c in captures]);dump(out/'GEOMETRY.json',m)
    return out/'GEOMETRY.json'

def make_request(bound,spec,geometry_path,synthetic):
    import reader_policy as Q
    import gravity_guard as guard
    from routed import source_pins as trainer_pins
    r=dict(schema='read-request-v1',bound=bound['binding'],keys=bound['keys'],config=spec['config'],
           artifact=spec['artifact'],data_receipt=spec.get('data_receipt'),geometry=pin(geometry_path),
           sources=source_pins(),tree_sources=trainer_pins(),budget=Q.DECODE_BUDGET,
           gravity_guard=guard.identity(),synthetic=synthetic,served=['move','turn','pose'])
    r['binding']=digest(r);return r

def replay(decoded,geo):
    import perception as P
    with camera_only():return P.replay(decoded,geo,None)

def scripted(task,geo):
    import perception as P
    i,j=task['pair']
    with camera_only():decoded=P.execute_calls(geo,None,[f'<move from={i} to={j}>'])
    answer=P.script_answer(task,decoded)
    decoded.update(script_answer=answer,text='</think>\n'+(answer or ''),tokens=[],generated_tokens=0)
    return decoded

def canary_check(records,keys,request):
    native=[r for r in records if r['arm']=='native']
    checks=dict(membership=[r['key'] for r in native]==keys,
                parse=all(r['parsed']['parse_status']=='ok' or r['no_final_answer'] for r in native),
                replay=all(r['replay']['byte_equal'] for r in records),
                scorer=all(0<=r['score']<=1 for r in records),
                timing=all(r['seconds']>=0 for r in records),
                accounting=all(r['served']+r['refused']+r.get('camera_errors',0)==len(r['calls']) for r in records),
                refusal_continuation=all(r['finish']!='program_refusal' for r in native))
    value=dict(pass_=all(checks.values()),checks=checks,keys=keys,request=request['binding'],
               synthetic=request['synthetic'],served=sum(r['served'] for r in native),refused=sum(r['refused'] for r in native))
    return value

def run(bound_path,spec,geometry_path,out,shard='0/1',canary_only=False,canary_receipt=None,limit=21600,boundary=None,deadline_utc=None,resume=(),proof_path=None):
    started=time.monotonic();bound=validate_bound(bound_path);guard=initialize(spec)
    if limit<=0 or limit>21600:raise ValueError('sealed runtime limit exceeded')
    if boundary is None:boundary=NativeBoundary(spec)
    if boundary.synthetic!=bound['synthetic']:raise ValueError('fixture cannot admit a production list')
    import geometry as G,geometry_refusals as GR,perception as P
    from routed import trainer_row
    from student_pilot.ground_profiles import load_geometry
    from student_pilot.scene_state import FrameMap
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    request=make_request(bound,spec,geometry_path,boundary.synthetic);dump(out/'REQUEST.json',request)
    tasks={t['id']:t for t in rows(checked(bound['inputs']['TASKS.jsonl']))}
    captures={c['native']:c for c in load(checked(bound['inputs']['FRAMES.json']))['captures']}
    g=load(checked(request['geometry']));G.validate_manifest(g,spec['artifact'],list(captures))
    if g.get('binding')!=bound['binding'] or g.get('config')!=spec['config'] or bool(g.get('synthetic'))!=boundary.synthetic:
        raise ValueError('geometry read/config binding differs')
    raw=load(checked(g['raw_tower']))
    if raw['dense_manifest']!=bound['inputs']['DENSE.json']:raise ValueError('foreign tower input')
    limit=min(limit,max(1e-9,21600-g.get('read_preparation_seconds',0)))
    refusal=GR.item_refusals(list(tasks.values()),g)
    assigned=shard_keys(bound,shard,canary_only);k,n=map(int,shard.split('/'))
    if k:
        if canary_receipt is None:raise ValueError('nonzero shard requires a passed canary receipt')
        receipt=load(canary_receipt)
        if not receipt['pass_'] or receipt['request']!=request['binding']:raise ValueError('canary binding differs')
    if not boundary.synthetic:
        camera=next(t for t in tasks.values() if t['question_type'] in CAMERA)
        boundary.parity(camera,captures[camera['native']],bound['frames_root'],out)
    else:dump(out/'GPU_PARITY.json',dict(pass_=False,synthetic=True,not_checked='GPU prompt/cache/head parity'))
    from budget import Budget
    budget=Budget(deadline_utc);prior=None;prior_keys=[];canary=[]
    if resume:
        prior=merge(bound_path,resume,out/'PRIOR.json',partial=True)
        if prior['request_binding']!=request['binding']:raise ValueError('resume request/config/geometry/frame pins differ')
        prior_keys=[r['key'] for r in prior['items'] if r['arm']=='native']
        for r in prior['items']:
            if r['arm']=='native':budget.observe(r['question_type'],r['seconds'])
            if r['key'] in bound['canary']:canary.append(r)
        if set(bound['canary'])<=set(prior_keys) and not canary_check(canary,bound['canary'],request)['pass_']:
            raise ValueError('resume canary failed')
    proof_pin=None
    if proof_path:
        proof_value=load(proof_path);proof_value['read_binding']=request['binding'];dump(out/'PROOF.json',proof_value)
        proof_pin=pin(out/'PROOF.json')
    elif prior:proof_pin=prior.get('proof')
    written=[];cache={};reason='complete' 
    def checkpoint(reason):
        value=dict(schema='read-complete-v1',request=pin(out/'REQUEST.json'),request_binding=request['binding'],
            geometry=request['geometry'],config=request['config'],shard=shard,assigned=assigned,keys=list(written),
            missing=[q for q in assigned if q not in written and q not in prior_keys],reason=reason,synthetic=boundary.synthetic,
            journal=pin(out/'items.jsonl') if (out/'items.jsonl').exists() else None,
            journal_bytes=(out/'items.jsonl').stat().st_size if (out/'items.jsonl').exists() else 0,seconds=time.monotonic()-started,
            gravity=guard.report(),canary_only=canary_only,geometry_seconds=g.get('read_preparation_seconds',0),resume_keys=prior_keys,proof=proof_pin,budget=budget.record())
        dump(out/'COMPLETE.json',value);return value
    checkpoint('running')
    for key in assigned:
        if key in prior_keys:continue
        if not budget.allows(tasks[key]['question_type']):reason='deadline';break
        if time.monotonic()-started>=limit:reason='time_limit';break
        begin=time.monotonic();task=tasks[key];capture=captures[task['native']]
        row=trainer_row(task,capture,bound['frames_root'],verify=True)
        clip=row['student_input']['video_identity']['video_sha256']
        pair=[]
        for arm in ('native','scripted') if task['question_type'] in CAMERA else ('native',):
            arm_started=begin if arm=='native' else time.monotonic()
            if key in refusal:
                decoded=dict(text='',calls=[],tokens=[],finish='geometry_refusal',errors=0)
                rep=dict(byte_equal=True,not_executed='geometry refusal')
            else:
                if clip not in cache:
                    with guard.capture('r0',task['native']):
                        cache[clip]=load_geometry(checked(g['videos'][clip]),FrameMap(tuple(capture['anchor_indices'])),'tower_scaled')
                geo=cache[clip]
                decoded=boundary.generate(task,row,geo) if arm=='native' else scripted(task,geo)
                rep=replay(decoded,geo)
                if not rep['byte_equal']:raise ValueError('response replay mismatch: '+key)
            calls=call_records(decoded);value=score(final_text(decoded),load(checked(bound['inputs']['SCORES.json']))[key])
            rec=dict(key=key,arm=arm,question_type=task['question_type'],native=task['native'],
                     **value,calls=calls,served=sum(c['name'] in ('move','turn','pose') and c['kind']!='error' for c in calls),
                     refused=sum(c['refused'] for c in calls),camera_errors=sum(c['name'] in ('move','turn','pose') and c['kind']=='error' for c in calls),
                     decode=decoded,finish=decoded['finish'],forced_close=decoded.get('decode_budget',{}).get('forced_close_position') is not None,
                     geometry_refusal=refusal.get(key),replay=rep,seconds=time.monotonic()-arm_started,binding=request['binding'])
            # Malformed camera calls remain error responses, not policy refusals.
            pair.append(rec)
        with (out/'items.jsonl').open('a') as stream:
            for rec in pair:stream.write(json.dumps(rec,sort_keys=True,allow_nan=False)+'\n');stream.flush()
        budget.observe(task['question_type'],time.monotonic()-begin)
        written.append(key)
        checkpoint('running')
        if key in bound['canary']:canary.extend(pair)
        if k==0 and key in bound['canary'] and set(bound['canary'])<=set(written+prior_keys):
            receipt=canary_check(canary,bound['canary'],request)
            rates={}
            for category in ('camera','other'):
                values=[r['seconds'] for r in canary if r['arm']=='native' and (r['question_type'] in CAMERA)==(category=='camera')]
                rates[category]=sum(values)/len(values) if values else None
            remaining=[tasks[q] for q in assigned if q not in written]
            receipt['seconds_per_item']=rates
            receipt['projected_remaining_seconds']=sum(budget.projected(t['question_type']) for t in remaining)
            receipt['projection_rule']=budget.record()
            dump(out/'CANARY.json',receipt)
            if not receipt['pass_']:reason='canary_failed';break
    completion=checkpoint(reason)
    if reason=='canary_failed':raise ValueError('canary failed; remaining decode stopped')
    return completion

def merge(bound_path,directories,output,partial=False):
    bound=validate_bound(bound_path);seen=set();data=[];identity=None;completions=[];proof_pin=None
    for directory in directories:
        c=load(Path(directory)/'COMPLETE.json');r=load(checked(c['request']))
        if r['bound']!=bound['binding'] or digest({k:v for k,v in r.items() if k!='binding'})!=r['binding']:
            raise ValueError('request binding differs')
        this=(r['binding'],c['geometry'],c['config'],c['synthetic'])
        if identity is None:identity=this
        if this!=identity:raise ValueError('shard pins differ')
        if c['request_binding']!=r['binding'] or c['geometry']!=r['geometry'] or c['config']!=r['config']:
            raise ValueError('completion pins differ from request')
        checked(r['geometry'])
        if c.get('proof'):
            checked(c['proof'])
            if proof_pin and proof_pin['sha256']!=c['proof']['sha256']:raise ValueError('proof pins differ')
            proof_pin=c['proof']
        if c['reason'] not in ('complete','deadline','time_limit') and not partial:raise ValueError('shard did not complete')
        if partial and c['reason']!='complete' and c['journal']:
            import hashlib
            with Path(c['journal']['path']).open('rb') as stream:blob=stream.read(c['journal_bytes'])
            if hashlib.sha256(blob).hexdigest()!=c['journal']['sha256']:raise ValueError('committed journal prefix differs')
            values=[json.loads(line) for line in blob.decode().splitlines()]
        else:
            values=rows(checked(c['journal'])) if c['journal'] else []
        native=[v['key'] for v in values if v['arm']=='native']
        if native!=c['keys'] or len(native)!=len(set(native)) or seen.intersection(native):raise ValueError('shards overlap or journal differs')
        if not set(c.get('resume_keys',[]))<=seen:raise ValueError('resume history is absent or out of order')
        if c['assigned']!=shard_keys(bound,c['shard'],c['canary_only']):raise ValueError('shard assignment differs')
        if any(v['binding']!=r['binding'] for v in values):raise ValueError('item request differs')
        expected_scripts={v['key'] for v in values if v['arm']=='native' and v['question_type'] in CAMERA}
        scripts=[v['key'] for v in values if v['arm']=='scripted']
        if len(set(scripts))!=len(scripts) or set(scripts)!=expected_scripts:raise ValueError('scripted coverage differs')
        seen.update(native);data.extend(values);completions.append(c)
    missing=[k for k in bound['keys'] if k not in seen]
    if seen-set(bound['keys']) or (missing and not partial):raise ValueError('shards do not cover bound list exactly')
    result=dict(schema='read-merged-v1',synthetic=identity[3],items=data,missing=missing,
                complete=not missing and all(c['reason'] in ('complete','deadline','time_limit') for c in completions),proof=proof_pin,request_binding=identity[0],completions=completions,bound=pin(bound_path))
    dump(output,result);return result
