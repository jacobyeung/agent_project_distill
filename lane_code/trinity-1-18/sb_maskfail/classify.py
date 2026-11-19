"""Classify stored measured overlaps using RULES.md; does not rerun perception."""
import gzip,json,pickle
import analyze as A

caps,ids,labels,old=A.setup()
parity=[];parity_pins={};missing_prompts={}
for c in caps:
    rp=A.WORK/(A.stub(c)+'.json.gz');pp=A.PROV/(A.stub(c)+'.json');pk=A.WORK/(A.stub(c)+'.pkl')
    with gzip.open(rp,'rt') as f:d=json.load(f)
    with pk.open('rb') as f:s=pickle.load(f)
    for r in s['parity']:
        expected=old[(r['arm'],r['row_id'])]['prediction']
        assert r['prediction']==expected
        parity.append(dict(r,expected_prediction=expected,passed=True))
    prov=json.loads(pp.read_text())
    original=A.HERE/'out/executed_sources/measurement.py'
    assert A.sha(original)==prov['input_sha256'][str(A.HERE/'analyze.py')]
    prov['input_sha256'][str(original)]=A.sha(original)
    for p in [A.HERE/'RULES.md',A.HERE/'analyze.py',A.HERE/'classify.py']:
        prov['input_sha256'][str(p)]=A.sha(p)
    A.write(pp,prov);h=A.sha(pp)
    parity_pins[str(pp)]=h
    teacherpath=A.HERE/'teacher/teacher_k1_full/teacher_k1'/A.stub(c)/'teacher.json.gz'
    teacher=A.readj_gz(teacherpath) if teacherpath.exists() else None
    for r in d['records']:
        if teacher is not None and r['object'] not in teacher['frames'][str(r['frame']-1)]['phrases']:
            expected=str(teacherpath)+'#frames.'+str(r['frame']-1)+'.phrases.'+r['object']
            r['teacher_best_iou']=None;r['teacher_status']='MISSING: '+expected
            missing_prompts[expected]=dict(capture=c['canonical'],status='MISSING',expected_path=expected)
        r['pricing_best_frame']=s['base'][r['object']].get('best')
        if not r['valid']:r['iou']=None
        elif not r['visible']:r['iou']=0. if r['served_area'] else None
        r['failure_kinds']={str(t):A.classify(r,t) for t in A.THRESH};r['failure_kind']=r['failure_kinds']['0.5']
        r['input_sha256']={str(pp):h}
    d['input_sha256']=prov['input_sha256']
    with gzip.open(rp,'wt') as f:json.dump(d,f,separators=(',',':'))
    for n in s['kinds']:
        rr={r['frame']:r for r in d['records'] if r['object']==n}
        s['kinds'][n]={str(t):[rr[f]['failure_kinds'][str(t)] for f in range(1,33)] for t in A.THRESH}
    s['input_sha256']=prov['input_sha256']
    with pk.open('wb') as f:pickle.dump(s,f,protocol=5)
A.aggregate(caps)
A.write(A.OUT/'ENDPOINT_PARITY.json',dict(rows=parity,input_sha256=parity_pins))
missing=[]
for c in caps:
    path=A.HERE/'teacher/teacher_k1_full/teacher_k1'/A.stub(c)/'teacher.json.gz'
    if not path.exists():missing.append(dict(capture=c['canonical'],status='MISSING',expected_path=str(path)))
A.write(A.OUT/'MISSING_INPUTS.json',dict(missing=missing,missing_prompt_records=list(missing_prompts.values()),input_sha256={str(A.TAR):A.sha(A.TAR),str(A.HERE/'classify.py'):A.sha(A.HERE/'classify.py')}))
print('All stored overlaps classified; FIRST_TABLE.md is ready.',flush=True)
