"""Compare two greedy replays against the pinned completed reference read."""
from pathlib import Path
import sys
from adapter import *
from scorer import final_text

def signature(decoded):
    return dict(tokens=decoded.get('tokens'),calls=[c['call'] for c in decoded['calls']],
                responses=[c['response'].encode('utf-8').hex() for c in decoded['calls']],answer=final_text(decoded))

def compare(reference,first,repeat,output,synthetic=False):
    expected={r['key']:r['decode'] for r in reference};a={r['key']:r['decode'] for r in first};b={r['key']:r['decode'] for r in repeat}
    if len(expected)!=len(reference) or set(expected)!=set(a) or set(a)!=set(b):raise ValueError('proof membership differs')
    result=[]
    for key,decode in expected.items():
        target=signature(decode);one=signature(a[key]);two=signature(b[key]);divergence=None
        for field in target:
            if target[field]!=one[field] or one[field]!=two[field]:
                ref,x,y=target[field],one[field],two[field]
                position=next((i for i in range(max(len(ref or []),len(x or []),len(y or []))) if
                    (ref[i:i+1] if ref is not None else None)!=(x[i:i+1] if x is not None else None) or
                    (x[i:i+1] if x is not None else None)!=(y[i:i+1] if y is not None else None)),None)
                divergence=dict(field=field,position=position,reference=ref[position:position+1] if position is not None and ref is not None else None,
                                first=x[position:position+1] if position is not None and x is not None else None,
                                repeat=y[position:position+1] if position is not None and y is not None else None)
                break
        result.append(dict(key=key,identical=target==one==two,token_equal=target['tokens']==one['tokens']==two['tokens'],
                           repeat_equal=one==two,first_divergence=divergence))
    report=dict(schema='equality-proof-v1',synthetic=synthetic,items=len(result),identical_count=sum(r['identical'] for r in result),
                equal_token_share=sum(r['token_equal'] for r in result)/len(result),records=result,
                proven=not synthetic and all(r['identical'] for r in result),
                not_checked=['GPU repeat and historical equality'] if synthetic else [])
    dump(output,report);return report

def compare_geometry(current,original,output):
    import numpy as np
    old={r['native']:r for r in original['records']};records=[]
    for row in current['records']:
        ref=old[row['native']]
        checks={k:row.get(k)==ref.get(k) for k in ('status','error','scale','diagnostics','conditioning_question_id','prefill_sha256')}
        if row['output'] and ref['output']:
            with np.load(checked(row['output']),allow_pickle=False) as a,np.load(checked(ref['output']),allow_pickle=False) as b:
                for key in ('scale','camera_to_world','K'):
                    checks[key+'_bit_identical']=a[key].dtype==b[key].dtype and a[key].shape==b[key].shape and a[key].tobytes()==b[key].tobytes()
        records.append(dict(native=row['native'],checks=checks,equal=all(checks.values())))
    value=dict(records=records,identical=sum(r['equal'] for r in records),captures=len(records),
               compared=['scale','camera_to_world','K','status','error','gravity diagnostics','conditioning question','prefill tokens'],not_compared=[])
    dump(output,value);return value

def preparation_check(boundary,spec,request,tasks,captures,references,out):
    """Recompute proof captures through the read's preparation entry point."""
    import importlib.util
    import engine
    original=load(checked(request['grounding']['geometry_manifest']))
    needed={tasks[r['key']]['native'] for r in references}
    records=[r for r in original['records'] if r['native'] in needed]
    by_id={t['id']:t for t in tasks.values()}
    conditioned=[by_id[r['conditioning_question_id']] for r in records]
    raw=load(checked(original['raw_tower']));raw['captures']={k:v for k,v in raw['captures'].items() if k in needed}
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    dump(out/'RAW.json',raw);dump(out/'FRAMES.json',dict(captures=[captures[k] for k in sorted(needed)]))
    (out/'TASKS.jsonl').write_text(''.join(json.dumps(t,sort_keys=True)+'\n' for t in conditioned))
    bound=dict(binding=digest(sorted(needed)),frames_root=request['frames_root'],inputs={
        'TASKS.jsonl':pin(out/'TASKS.jsonl'),'FRAMES.json':pin(out/'FRAMES.json'),'DENSE.json':raw['dense_manifest']})
    # Keep the original decoder modules loaded. Only preparation resolves to the read's geometry module.
    path=Path(__file__).parent/'sj/orch_cd/evalx/work/milestone/native/out2/geometry.py'
    module_spec=importlib.util.spec_from_file_location('prepared_capture',path)
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    module.TREE=Path(spec['tree']);previous=sys.modules['geometry'];sys.modules['geometry']=module
    try:current=engine.prepare_geometry(bound,spec,out/'RAW.json',out/'g',boundary)
    finally:sys.modules['geometry']=previous
    return compare_geometry(load(current),original,out/'CHECK.json')

def run(reference_path,request_path,spec,output):
    """Use a fresh process with the original module namespace and serving policy."""
    import os
    os.environ['LEGS1_TREE']=spec['tree']
    sys.path.append(spec['tree'])
    if 'proof_core' not in spec:raise ValueError('original adapter root is required')
    core=Path(spec['proof_core']);sys.path.insert(0,str(core/'native/out2'))
    import nomdg as N,perception as P,gravity_guard as guard
    from student_pilot import geometry_profiles as GP
    if not guard._installed:guard.install(GP,guard.Recorder())
    request=load(request_path)
    if request['adapter_sources']!=N.adapter_sources():raise ValueError('proof adapter differs from reference')
    N.validate_request(request,live=True)
    from engine import NativeBoundary
    boundary=NativeBoundary(spec)
    tasks,captures=N.tasks_and_captures(request['inputs']);tasks={'devrows:'+t['id']:t for t in tasks}
    from routed import trainer_row
    geometry=load(checked(request['grounding']['geometry_manifest']))
    references=load(reference_path)
    from budget import Budget
    import time
    budget=Budget(spec.get('deadline_utc'))
    from collections import Counter
    if Counter(r['question_type'] for r in references)!={'camera_displacement':3,'camera_movement_direction':3,'camera_rotation':4}:
        raise ValueError('proof type membership differs')
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    geometry_check=preparation_check(boundary,spec,request,tasks,captures,references,out/'g')
    outputs=[[],[]]
    for destination in outputs:
        for ref in references:
            key=ref['key'];task=tasks[key]
            if not budget.allows(task['question_type']):
                dump(out/'INCOMPLETE.json',dict(reason='deadline',completed=[r['key'] for r in destination],missing=[r['key'] for r in references if r['key'] not in {x['key'] for x in destination}]))
                raise TimeoutError('deadline before next proof item')
            item_started=time.monotonic()
            if N.mask_source(task['question_type']) is not None:raise ValueError('proof requires camera serving')
            row=trainer_row(task,captures[task['native']],request['frames_root'],verify=True)
            geo=P.load_geometry(geometry,row)
            decoded=P.generate(boundary.model,boundary.processor,boundary.batch(row),geo,budget=request['decode_budget'])
            if decoded.get('errors') or any(c.get('kind')=='error' for c in decoded['calls']):raise ValueError('proof call error')
            if not P.replay(decoded,geo,None)['byte_equal']:raise ValueError('proof response replay differs')
            destination.append(dict(key=key,decode=decoded))
            budget.observe(task['question_type'],time.monotonic()-item_started)
            dump(out/('FIRST.json' if destination is outputs[0] else 'REPEAT.json'),destination)
    dump(out/'FIRST.json',outputs[0]);dump(out/'REPEAT.json',outputs[1])
    value=compare(references,*outputs,out/'PROOF.json')
    value.update(geometry_check=geometry_check,inputs=dict(reference=pin(reference_path),request=pin(request_path),mask_cache=request['mask_cache']),gravity=guard.report())
    dump(out/'PROOF.json',value);return value
