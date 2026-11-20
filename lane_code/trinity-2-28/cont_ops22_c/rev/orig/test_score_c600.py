"""Prove the wrapper rejects mismatched bindings and preserves the 99.82% look.

Run after rehearse_c600.py. This is synthetic scoring evidence, not a step-600 result.
"""
import copy
import hashlib
import importlib.util
import json
import os
import runpy
import subprocess
import sys
import tarfile
from pathlib import Path

H=Path(__file__).resolve().parent
W=(H/(sys.argv[1] if len(sys.argv)>1 else 'rehearsal')).resolve()
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def link(p,q):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.is_symlink():assert p.resolve()==q.resolve()
    else:p.symlink_to(q.resolve())

result=read(W/'RESULT.json');P=Path(result['package']);pub=read(P/'0.json')
O=W/'scoring_fix';O.mkdir(exist_ok=True);A=O/'A';A.mkdir(exist_ok=True)
source=H/'in/out4s'
original_scorer_sha=sha(source/'score_r5_look.py')
(O/'score_r5_look.py').write_bytes((source/'score_r5_look.py').read_bytes())
assert sha(O/'score_r5_look.py')==sha(source/'score_r5_look.py')
link(O/'bases',source/'bases');link(A/'package',P)
(A/'tower_sequence.py').write_bytes((P/'a/6.py').read_bytes())
link(A/'tower_pair.py',source/'A/tower_pair.py')
(A/'src').mkdir(exist_ok=True)
for p in (source/'A/src').iterdir():
    if p.name!='9.json':link(A/'src'/p.name,p)
with tarfile.open(str(P/'0.tgz')) as t:
    (A/'src/9.json').write_bytes(t.extractfile('9.json').read())
op=runpy.run_path(str(P/'a/6.py'),run_name='camera_test')
plan=read(source/'A/READ_PLAN.json');binding=read(H/'in/BIND600.json')
plan.update(token=pub['token'],plan_sha256=pub['plan_sha256'],operator_sha256=sha(P/'a/6.py'),
    expected=[450],read_settings=op['descriptors'](str(P)),sequence=[list(x) for x in op['SCHEDULE']],
    walltime='03:00:00',export_binding={k:binding[k] for k in plan['export_binding']},
    export_identity_seal='PACKAGE.json pins the operator and fill helper; payload 9.json seals the step-600 export binding.',
    operations_file='REPORT_A600C.md')
camera=('camera_displacement','camera_rotation','camera_movement_direction')
items=read(A/'src/items/devs1_routed.json')['items']
camera_ids={i['id'] for i in items if i['question_type'] in camera}
assert len(camera_ids)==450
plan['item_ids_in_execution_order']=[i for i in plan['item_ids_in_execution_order'] if i in camera_ids]
plan['item_sets']={'dev-S1':450}
assert len(plan['item_ids_in_execution_order'])==450
from make_read_plan_c600 import make
assert plan==make(P,binding,read(source/'A/READ_PLAN.json'))
write(A/'READ_PLAN.json',plan)
assert read(H/'READ_PLAN_C600.json')==plan

old=H/'in/out3/A10b/ret';ret=O/'synthetic_camera_return'
identity=read(old/'metadata/IDENTITY.json')
identity.update(plan=pub['plan_sha256'],operator_sha256=sha(A/'tower_sequence.py'),
                inputs=sha(P/'a/1.json'),reads=plan['read_settings'],schedule=plan['sequence'])
write(ret/'metadata/IDENTITY.json',identity)
pin=read(old/'metadata/EXPORT_PIN.json')
for k in ('run','step','member_directory','object','config_sha256','archive_sha256','archive_bytes'):
    pin[k]=binding[k]
write(ret/'metadata/EXPORT_PIN.json',pin)
found={};sources=[]
for t,kind in enumerate(camera):
    rel='metadata/reads/0/metadata/journals/%d/0'%t
    lines=(old/rel/'items.jsonl').read_text().splitlines(True)
    selected=[l for l in lines if json.loads(l)['type'] in camera]
    rows=[json.loads(l) for l in selected]
    assert len(rows)==150 and all(r['type']==kind for r in rows)
    for row in rows:
        assert row['id'] not in found;found[row['id']]=row
    dest=ret/rel;dest.mkdir(parents=True,exist_ok=True)
    (dest/'items.jsonl').write_text(''.join(selected))
    assert (dest/'items.jsonl').read_bytes()==(old/rel/'items.jsonl').read_bytes()
    env=read(old/rel/'environment.json');env['binding']['step']=600
    env['binding']['ids']=[i for i in env['binding']['ids'] if i in camera_ids]
    env['binding']['count']=450
    # Retain opaque model/output hashes as inherited synthetic provenance, not real 600 evidence.
    write(dest/'environment.json',env)
    (dest/'STARTED.json').write_bytes((old/rel/'STARTED.json').read_bytes())
    sources.append(dict(source=str(old/rel/'items.jsonl'),sha256=sha(dest/'items.jsonl'),rows=150))
assert set(found)==camera_ids
write(ret/'SYNTHETIC.json',dict(synthetic=True,source_step=400,target_step=600,
    warning='Step-400 outputs relabeled solely to test scorer compatibility; no step-600 inference.',
    retained_opaque_hashes=['export_sha256','artifact_manifest_sha256','mapping_sha256'],sources=sources))
write(ret/'SUMMARY.json',dict(complete=True,completed=450,expected=450,failure=None,reads=[dict(read=0,complete=True,completed=450,expected=450)]))

def command(argv,log,cwd=None):
    with (O/log).open('w') as f:
        r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,cwd=cwd)
    assert r.returncode==0,(argv,str(O/log))
command([sys.executable,'-B',str(source/'score_r5_look.py'),'--step','400','--a',str(old),'--out',str(O/'full400')],'full400.log')
wrapper=[sys.executable,'-B',str(H/'score_c600.py'),'--step','600',
         '--package-root',str(A),'--read-plan',str(H/'READ_PLAN_C600.json'),
         '--baseline-root',str(source/'bases'),'--a',str(ret)]
command(wrapper+['--out',str(O/'camera600')],'camera600.log')
a=read(O/'full400/scores.json');b=read(O/'camera600/scores.json')
for kind in camera:
    assert a['types'][kind]==b['types'][kind],kind
    assert b['types'][kind]['complete'] is True
    assert b['types'][kind]['current']['completed']==150
    assert b['types'][kind]['level']==.9982
for key in ('camera_calls','h3_level','h3_stop','h3_complete'):
    assert a[key]==b[key],key
assert b['camera_calls']['completed']==450 and b['h3_complete'] is True
for kind in ('object_abs_distance','room_size_estimation'):
    assert b['types'][kind]['current']['completed']==0 and b['types'][kind]['complete'] is False
assert b['distance_call_cap']['complete'] is False
assert b['units']['current']['completed']==0
command([sys.executable,'-B',str(source/'test_score_r5_look.py'),'score_r5_look'],'look_level_test.log',O)

# The wrapper must reject metadata mismatches before creating scoring output.
rejections=[]
def reject_wrapper(path, mutate, label, error):
    original=path.read_bytes()
    out=O/('rejected_'+label)
    assert not out.exists()
    try:
        data=read(path);mutate(data);write(path,data)
        result=subprocess.run(wrapper+['--out',str(out)],stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,universal_newlines=True)
        assert result.returncode==2,(label,result.stdout)
        assert error+' differs from READ_PLAN_C600.json' in result.stdout,(label,result.stdout)
        assert not out.exists(),label
        rejections.append(label)
    finally:path.write_bytes(original)

old_pin=read(old/'metadata/EXPORT_PIN.json')
assert old_pin['archive_sha256'].startswith('dcd49569')
for field,value in (('archive_sha256',old_pin['archive_sha256']),
                    ('archive_bytes',binding['archive_bytes']+1),
                    ('object',old_pin['object']),('step',400),('member_directory','m400')):
    reject_wrapper(ret/'metadata/EXPORT_PIN.json',lambda d,k=field,v=value:d.update({k:v}),
                   field,'Export '+field)
reject_wrapper(ret/'metadata/EXPORT_PIN.json',lambda d:d.pop('archive_bytes'),
               'missing_archive_bytes','Export archive_bytes')
for field in ('plan','operator_sha256'):
    reject_wrapper(ret/'metadata/IDENTITY.json',lambda d,k=field:d.update({k:'0'*64}),
                   'identity_'+field,'Return '+field)
reject_wrapper(A/'READ_PLAN.json',lambda d:d.update(token='wrong-package'),
               'package_read_plan','Package read plan')
operator=(A/'tower_sequence.py').read_bytes()
try:
    (A/'tower_sequence.py').write_bytes(operator+b'\n# mismatched operator\n')
    result=subprocess.run(wrapper+['--out',str(O/'rejected_package_operator')],
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
    assert result.returncode==2 and 'Package operator differs from READ_PLAN_C600.json' in result.stdout
    assert not (O/'rejected_package_operator').exists()
    rejections.append('package_operator')
finally:(A/'tower_sequence.py').write_bytes(operator)

# Existing return identity checks must still fail in the unchanged scorer.
spec=importlib.util.spec_from_file_location('score_local',str(O/'score_r5_look.py'))
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
M.STEP=600;M.LEVEL=M.level_for(600)
original_read=M.read
def reject(mutator, label):
    def mutated(path):
        d=original_read(path)
        if Path(path)==ret/'metadata/IDENTITY.json':mutator(d)
        return d
    M.read=mutated
    try:M.load(ret,A,0,600,'candidates_argmax')
    except ValueError:pass
    else:raise AssertionError('Accepted '+label)
    finally:M.read=original_read
reject(lambda d:d.update(operator_sha256='0'*64),'wrong operator')
reject(lambda d:d['reads'][0].update(types=[3,0,1,2,4]),'old type selection')
reject(lambda d:d.update(plan='0'*64),'wrong plan')
assert sha(source/'score_r5_look.py')==original_scorer_sha==sha(O/'score_r5_look.py')
summary=dict(passed=True,scorer_unchanged=True,scorer_sha256=sha(O/'score_r5_look.py'),
    synthetic=True,camera_rows_equal=True,level=.9982,camera_calls=b['camera_calls'],
    cameras={k:dict(score=b['types'][k]['current']['score'],delta=b['types'][k]['paired']['value'],complete=b['types'][k]['complete']) for k in camera},
    absent_types_marked_incomplete=True,negative_binding_tests=3,
    wrapper_rejection_tests=len(rejections),wrapper_rejections=rejections,
    caveat='A-only scorer retains baseline-only room diagnostics; they are not step-600 room observations.')
write(O/'TEST_RESULT.json',summary)
print(json.dumps(summary,indent=2))
