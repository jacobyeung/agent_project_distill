"""Qualify a frozen local source with the unchanged bounded suite runner."""
from pathlib import Path
import os,sys,json,hashlib,subprocess,shutil,time
L=Path(__file__).resolve().parents[2];B=L/'work/build20';O=B/'proofs/final';O.mkdir(parents=True,exist_ok=True)
T=L/'work/tree_r1';F=O/'frozen';tree=F/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
files=inventory(T)
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
assert sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())+sum((T/n).stat().st_size for n in files)<1_500_000_000
for name in files:
    q=tree/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((T/name).read_bytes())
for rel in ('work/base','work/build20/inputs','work/build19/inputs','work/build18/inputs','work/build17/inputs','work/build16/inputs','work/build15/inputs','work/build_n1/inputs'):
    q=F/rel;q.parent.mkdir(parents=True,exist_ok=True)
    if not q.exists():q.symlink_to(L/rel,target_is_directory=True)
assert inventory(tree)==files
records={}
absent={'generator':'/scratch/jjyeung/orch_cd/ground_backend/work/c1mix_sb/student_pilot/ground_lifting.py',
        'legacy':'/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/MANIFEST.json'}
for group,missing in absent.items():
    assert not Path(missing).exists()
    record=dict(status='not rerun: input absent ('+missing+')',build18_pass=False,
        historical_result='work/build14/proofs/final/suite_tree/'+group+'/results.json',
        inherited_result_qualified=False,reason='The required input is absent. Historical totals do not qualify the current source.')
    records[group]=record
    p=O/'suite_tree'/group;p.mkdir(parents=True,exist_ok=True)
    (p/'NOT_RERUN.json').write_text(json.dumps(record,indent=2))
group='r2';target=O/'suite_tree'/group;target.mkdir(parents=True,exist_ok=True)
empty=O/'empty';empty.mkdir(exist_ok=True)
env={**os.environ,'R2_TREE':str(tree),'R2_LANE_ROOT':str(L),'R2_ALL_TESTS':'1','R2_SUITE_GROUP':group}
runner=L/'work/n1fix2/test_runner.py'
before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert before<=200_000_000
start=time.time()
(B/'STATUS.md').write_text('# Build 20 status\n\nA/C/Cprime configuration comparisons pass; complete native proof remains blocked. Frozen R2 suite is running; generator/legacy groups have absent external inputs. GO=false.\n')
with (target/'console.log').open('w') as log:
    result=subprocess.run([sys.executable,'-I','-s','-B',str(runner),str(target)],cwd=empty,env=env,stdout=log,stderr=subprocess.STDOUT)
if result.returncode<0:raise SystemExit('Suite process was killed; stop without retry')
after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert after<=200_000_000
assert inventory(tree)==files and inventory(T)==files
records[group]=dict(returncode=result.returncode,seconds=time.time()-start,tmp_before=before,tmp_after=after,
    source_sha256=digest(files),runner_sha256=hashlib.sha256(runner.read_bytes()).hexdigest(),result=str((target/'results.json').relative_to(L)))
(B/'SUITE_RUNS.json').write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2))
