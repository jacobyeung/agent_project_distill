"""One reused mutant source directory; clean tests precede each mutation."""
from pathlib import Path
import json,os,sys,subprocess,shutil,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build15';T=L/'work/tree_r1';M=B/'mutant';O=B/'proofs/mutations'
O.mkdir(parents=True,exist_ok=True)
cases=[
 ('unassigned','student_pilot/r1_population.py','if unknown:','if False:','test_unassigned_type'),
 ('slice_identity','student_pilot/r1_population.py',"if marker != dict(family=kind, sha256=source_hash) or digest(row) != row_hash:","if False:",'test_slice_identity'),
 ('overlap','student_pilot/r1_mix.py','len(set(values)) != len(values)','False','test_overlap'),
 ('binding','student_pilot/r1_loader.py',"if cfg['r1_training'].get('row_plan_sha256') != digest(binding):",'if False:','test_binding_changed'),
 ('base_cell','student_pilot/r1_population.py',"if stream == 'routing' and kind in SLICE_CELLS:",'if False:','test_base_cells_refused'),
 ('base_composition','student_pilot/r1_routing.py',"if family(row, 'routing') in SLICE_CELLS:",'if False:','test_composition_replaces_base'),
]
files=[p for p in T.rglob('*') if p.is_file() and not set(p.relative_to(T).parts)&{'.git','__pycache__','artifacts'}]
results=[]
for name,source,before,after,test in cases:
    for p in files:
        q=M/p.relative_to(T);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
    env={**os.environ,'R2_TREE':str(M),'B15_PROOF':'mutations/run'}
    cmd=[sys.executable,'-I','-s','-B',str(B/'test15.py'),'tests.test_r1_build13.PopulationTests.'+test]
    with (O/(name+'_clean.log')).open('w') as f:clean=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
    if clean.returncode<0:raise SystemExit('Process killed; no rerun')
    assert clean.returncode==0,name
    p=M/source;raw=p.read_text();assert raw.count(before)==1,(name,raw.count(before))
    p.write_text(raw.replace(before,after))
    with (O/(name+'_mutant.log')).open('w') as f:mutant=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
    if mutant.returncode<0:raise SystemExit('Process killed; no rerun')
    assert mutant.returncode!=0,name
    results.append(dict(name=name,source=source,source_sha256=hashlib.sha256((T/source).read_bytes()).hexdigest(),
                        test=test,clean=clean.returncode,mutant=mutant.returncode,status='CAUGHT'))
    (O/'RESULT.json').write_text(json.dumps(dict(results=results),indent=2))
    print(name,'CAUGHT',flush=True)
(B/'STATUS.md').write_text('# Build 13 status\n\nGO=false. Six guard mutations were caught after clean passes (proofs/mutations/RESULT.json). Native mixture and producer tests pass; census/plan and final kits/suites are in progress.\n')
