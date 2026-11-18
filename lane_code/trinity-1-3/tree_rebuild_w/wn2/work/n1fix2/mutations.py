from pathlib import Path
import hashlib,io,json,os,sys,unittest
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=B/'proofs/mutations'
O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(B)]
os.environ.update(R2_PROOFS=str(O),R2_FIXTURES=str(L/'fixtures'))
from compact_tmp import inventory
from tests.test_r2_n1fix import N1Fix
from student_pilot import r1_training,scene_division_gate,r1_handover
from tests.test_r2_n1fix2 import Confirmation
cases=[('M09',scene_division_gate,"counts['outside'] or counts['heldout']","counts['heldout']",'test_M09_absent_scene'),
       ('M12',r1_training,"max_own_probability') != 0","max_own_probability') not in (0, 0.1)",'test_M12_own_probability'),
       ('M07',r1_training,"len(re.findall(r'\\bframe\\s+\\d+\\b', thought, re.I)) < 2 or ",'','test_M07_room_frames')]
cases.extend([
 ('H2',r1_handover,"bound.get('config_sha256') != identity or ",'','test_H2_binding_config'),
 ('H6',r1_handover,"identity != artifact.get('config_sha256') or ",'','test_H6_artifact_config')])
results=[]
for name,module,old,new,test in cases:
    path=Path(module.__file__);source=path.read_text();assert source.count(old)==1,(name,old)
    before=sum(inventory(L/'work/tmp').values());assert before<=200_000_000
    Test=Confirmation if name.startswith('H') else N1Fix
    clean=unittest.TextTestRunner(stream=io.StringIO()).run(Test(test));assert clean.wasSuccessful()
    mutated=source.replace(old,new);exec(compile(mutated,str(path),'exec'),vars(module))
    result=unittest.TextTestRunner(stream=io.StringIO()).run(Test(test))
    exec(compile(source,str(path),'exec'),vars(module))
    after=sum(inventory(L/'work/tmp').values());assert after<=200_000_000
    row=dict(mutant=name,test=test,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
             test_source='tests/test_r2_n1fix2.py' if name.startswith('H') else 'tests/test_r2_n1fix.py',
             test_source_sha256=hashlib.sha256((T/('tests/test_r2_n1fix2.py' if name.startswith('H') else 'tests/test_r2_n1fix.py')).read_bytes()).hexdigest(),
             fixture_source_sha256=hashlib.sha256((T/'tests/test_r2_n1fix.py').read_bytes()).hexdigest(),
             mutation_sha256=hashlib.sha256(mutated.encode()).hexdigest(),clean_pass=clean.wasSuccessful(),
             caught=not result.wasSuccessful(),failures=result.failures,errors=result.errors,before_bytes=before,after_bytes=after)
    row['failures']=[(str(t),s) for t,s in row['failures']];row['errors']=[(str(t),s) for t,s in row['errors']]
    results.append(row)
(O/'RESULT.json').write_text(json.dumps(dict(results=results,M01='Equivalent on reviewed real rows; unchanged.'),indent=2)+'\n')
assert all(r['caught'] and not r['errors'] for r in results)
print(json.dumps([{k:r[k] for k in ('mutant','clean_pass','caught')} for r in results]))
