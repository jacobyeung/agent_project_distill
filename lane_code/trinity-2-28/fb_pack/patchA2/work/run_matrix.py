"""Run CPU suites serially with the retained PATCH_A harness."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=[]
for tree in ('base','patch_a','live'):
    plan.append((tree,'must_'+tree,['test_r1_patch_a2','patch_a2_checks']))
for tree in ('base','new','live'):
    for group,args in (('subset',['test_r1_subset']),('focused',['alias-focused']),('integration',['alias-integration'])):
        plan.append((tree,group+'_'+tree,args))
plan.append(('live_base','host_live_base',['tests.test_host24j']))
plan.append(('live','host_live',['tests.test_host24j']))
plan.append(('new_camform','camform_regression',['tests.test_r1_camera_trace_form','tests.test_r1_subset','tests.test_r1_patch_a2']))
for tree in ('base','new','live_base','live'):
    plan.append((tree,'full_'+tree,['full']))
inputs={str(p):sha(p) for p in (Path(__file__),ROOT/'work/run_tests.py',ROOT/'out/PATCH_VALIDATION.json')}
runs=[]
for tree,label,args in plan:
    command=['env','PYTHONDONTWRITEBYTECODE=1','OMP_NUM_THREADS=16','MKL_NUM_THREADS=16','OPENBLAS_NUM_THREADS=16','nice','-n','10',PY,'-B','work/run_tests.py',tree,label,*args]
    start=time.monotonic()
    with (ROOT/'out'/(label+'.log')).open('x') as log:
        p=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    row=dict(tree=tree,label=label,command=' '.join(command),returncode=p.returncode,seconds=time.monotonic()-start)
    report=ROOT/'out'/(label+'.json')
    if report.exists():
        r=json.loads(report.read_text());row.update({k:r[k] for k in ('tests','failures','errors','skipped')});row['report_sha256']=sha(report)
    runs.append(row)
    (ROOT/'out/RUN_MATRIX.json').write_text(json.dumps(dict(command='env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 '+PY+' -B work/run_matrix.py',inputs_sha256=inputs,runs=runs,planned=[(t,l,a) for t,l,a in plan]),indent=2)+'\n')
    print(json.dumps(row),flush=True)
    if p.returncode<0:
        print('STOP: process killed; no further tests launched',flush=True)
        sys.exit(2)
