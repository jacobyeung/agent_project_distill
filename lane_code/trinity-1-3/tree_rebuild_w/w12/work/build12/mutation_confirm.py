from pathlib import Path
import ast,hashlib,importlib,io,json,os,sys,unittest
L=Path(__file__).resolve().parents[2];B=L/'work/build12';T=L/'work/tree_r1';O=B/'proofs/mutations'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(L/'work/n1fix2')]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
os.environ['LANE_TEST_OUTPUT']=str(L/'work/tmp')
from compact_tmp import inventory
from tests.test_r2_n1fix import N1Fix
from tests.test_r2_n1fix2 import Confirmation
from tests.test_r2_n1fix3 import Confirmation3
from tests.test_r2_build12 import Build12
from tests.test_r2_build9fix import Fixes
space={'M':json.loads((B/'proofs/review_inputs/MUTATION_SPEC.json').read_text())['mutations']}
cases={'M07':(N1Fix,'test_M07_room_frames'),'M09':(N1Fix,'test_M09_absent_scene'),
 'M12':(N1Fix,'test_M12_own_probability'),'H2':(Confirmation,'test_H2_binding_config'),
 'H6':(Confirmation,'test_H6_artifact_config'),'X1':(Confirmation,'test_optimizer_config_scales'),
 'X2':(Confirmation3,'test_extension_contract'),'X3':(Confirmation,'test_target_forgery'),
 'X4':(Confirmation,'test_target_forgery'),'X5':(Confirmation,'test_preparation_checkpoint_anchor'),
 'X6':(Confirmation3,'test_checkpoint_step'),'X7':(Confirmation,'test_preparation_checkpoint_anchor'),
 'X8':(Confirmation,'test_relative_symlink_and_nonempty_token'),'X9':(Confirmation,'test_relative_symlink_and_nonempty_token'),
 'X10':(Confirmation,'test_unicode_and_independent_reader'),'X11':(Confirmation3,'test_extra_unicode_and_cf'),
 'X12':(Confirmation3,'test_host_python_minimum'),'X13':(Confirmation,'test_target_forgery'),
 'M01':(Fixes,'test_status_authentication_and_whitespace')}
records=[]
space['M']['Y5']=['student_pilot/carrier_c1_run.py',
    'model.handover_group_tables = verify_trainable_groups(cfg, model)',
    'model.handover_group_tables = None']
cases['Y5']=(Build12,'test_trainer_hook_y5')
if len(sys.argv)>1:
    cases={k:v for k,v in cases.items() if k in sys.argv[1:]}
    records=[r for r in json.loads((O/'RESULT.json').read_text())['results'] if r['mutant'] not in cases]
for name,(Test,test) in cases.items():
    path,old,new=space['M'][name];p=T/path;source=p.read_text();assert source.count(old)==1,(name,source.count(old))
    module=importlib.import_module(path[:-3].replace('/','.'))
    before=sum(inventory(L/'work/tmp').values());assert before<=200_000_000
    clean=unittest.TextTestRunner(stream=io.StringIO()).run(Test(test));assert clean.wasSuccessful(),(name,clean.errors,clean.failures)
    changed=source.replace(old,new)
    if name=='X12':
        # The test reads the generated script's source constant; mutate that read only.
        from unittest.mock import patch
        native=Path.read_text
        with patch.object(Path,'read_text',lambda self,*a,**k:changed if self==p else native(self,*a,**k)):
            mutated=unittest.TextTestRunner(stream=io.StringIO()).run(Test(test))
    else:
        try:
            exec(compile(changed,str(p),'exec'),vars(module))
            mutated=unittest.TextTestRunner(stream=io.StringIO()).run(Test(test))
        finally:exec(compile(source,str(p),'exec'),vars(module))
    after=sum(inventory(L/'work/tmp').values());assert after<=200_000_000
    equivalent=name in ('M01','X13')
    row=dict(mutant=name,test=Test.__module__+'.'+Test.__name__+'.'+test,clean_pass=True,
        caught=not mutated.wasSuccessful(),equivalent=equivalent,source=path,
        test_source_sha256=hashlib.sha256((T/Path(*Test.__module__.split('.')).with_suffix('.py')).read_bytes()).hexdigest(),
        fixture_source_sha256=hashlib.sha256((T/'tests/test_r2_n1fix.py').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(source.encode()).hexdigest(),mutation_sha256=hashlib.sha256(changed.encode()).hexdigest(),
        old=old,new=new,failures=[(str(t),s) for t,s in mutated.failures],errors=[(str(t),s) for t,s in mutated.errors],
        before_bytes=before,after_bytes=after)
    records.append(row);(O/'RESULT.json').write_text(json.dumps(dict(results=records),indent=2))
    print(json.dumps({k:row[k] for k in ('mutant','clean_pass','caught','equivalent')}),flush=True)
    assert equivalent or (row['caught'] and not row['errors']),row
