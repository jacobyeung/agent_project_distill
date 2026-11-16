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

def run(reference_path,request_path,spec,output):
    """Run in the original input namespace; do not enable the camera-only policy."""
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
    # The loader uses the original authenticated preparation, export and tree.
    from engine import NativeBoundary
    boundary=NativeBoundary(spec)
    tasks,captures=N.tasks_and_captures(request['inputs']);tasks={'devrows:'+t['id']:t for t in tasks}
    from routed import trainer_row
    geometry=load(checked(request['grounding']['geometry_manifest']));masks=P.Masks(request['mask_cache'])
    references=load(reference_path);outputs=[[],[]]
    for destination in outputs:
        for ref in references:
            key=ref['key'];task=tasks[key]
            row=trainer_row(task,captures[task['native']],request['frames_root'],verify=True)
            geo=P.load_geometry(geometry,row)
            decoded=P.generate(boundary.model,boundary.processor,boundary.batch(row),geo,budget=request['decode_budget'])
            if not P.replay(decoded,geo,None)['byte_equal']:raise ValueError('proof response replay differs')
            destination.append(dict(key=key,decode=decoded))
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    dump(out/'FIRST.json',outputs[0]);dump(out/'REPEAT.json',outputs[1])
    value=compare(references,*outputs,out/'PROOF.json');value['inputs']=dict(reference=pin(reference_path),request=pin(request_path),mask_cache=request['mask_cache'])
    dump(out/'PROOF.json',value);return value
