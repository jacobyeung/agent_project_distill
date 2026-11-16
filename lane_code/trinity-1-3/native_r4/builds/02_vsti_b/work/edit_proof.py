from pathlib import Path
p=Path('code/proof.py');s=p.read_text();s=s[:s.index('def run(')]+'''def compare_geometry(current,original,output):
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
    (out/'TASKS.jsonl').write_text(''.join(json.dumps(t,sort_keys=True)+'\\n' for t in conditioned))
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
    from collections import Counter
    if Counter(r['question_type'] for r in references)!={'camera_displacement':3,'camera_movement_direction':3,'camera_rotation':4}:
        raise ValueError('proof type membership differs')
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    geometry_check=preparation_check(boundary,spec,request,tasks,captures,references,out/'g')
    outputs=[[],[]]
    for destination in outputs:
        for ref in references:
            key=ref['key'];task=tasks[key]
            if N.mask_source(task['question_type']) is not None:raise ValueError('proof requires camera serving')
            row=trainer_row(task,captures[task['native']],request['frames_root'],verify=True)
            geo=P.load_geometry(geometry,row)
            decoded=P.generate(boundary.model,boundary.processor,boundary.batch(row),geo,budget=request['decode_budget'])
            if decoded.get('errors') or any(c.get('kind')=='error' for c in decoded['calls']):raise ValueError('proof call error')
            if not P.replay(decoded,geo,None)['byte_equal']:raise ValueError('proof response replay differs')
            destination.append(dict(key=key,decode=decoded))
    dump(out/'FIRST.json',outputs[0]);dump(out/'REPEAT.json',outputs[1])
    value=compare(references,*outputs,out/'PROOF.json')
    value.update(geometry_check=geometry_check,inputs=dict(reference=pin(reference_path),request=pin(request_path),mask_cache=request['mask_cache']),gravity=guard.report())
    dump(out/'PROOF.json',value);return value
''';p.write_text(s)
