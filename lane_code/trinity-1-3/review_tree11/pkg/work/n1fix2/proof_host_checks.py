"""Exercise native host refusals without staging production data."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import json,os,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=L/'work/merge11/proofs/n1/host_checks'
O.mkdir(exist_ok=True);sys.path[:0]=[str(T),str(B)]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
monitor=Monitor(T)
from launch_r1 import entry
from tests.test_r2_build_n1 import configuration
from student_pilot.carrier_c1_run import recipe_for
from student_pilot.checkpoint_space import plan
from compact_tmp import inventory
cfg=configuration()
cfg={k:cfg[k] for k in ('training_mode','mix','world_size','reference_world_size','steps','milestones','scheduled_sampling','recipe')}
cfg['checkpoint_disk_guard']=plan(recipe_for(cfg),retained_archive_copies=1)
records=[]
for name,expected in [('cpu','CPU_ONLY_REQUIRED'),('disk','R1_DISK_PLAN_DIFFERS'),
                      ('binary','R1_BINARY_MISSING:'),('nonempty','R1_HOST_JOB_TMP_NOT_EMPTY'),
                      ('environment','R1_HOST_STAGING_AND_SELECTION_INPUTS_MISSING')]:
    before=sum(inventory(L/'work/tmp').values());assert before<=200_000_000
    job=O/name;value=deepcopy(cfg)
    environment=dict(os.environ,PATH='/usr/bin:/bin')
    environment.pop('TORCH_HOME',None)
    if name=='cpu':environment['CUDA_VISIBLE_DEVICES']='boundary_fixture'
    if name=='disk':value['checkpoint_disk_guard']={}
    request=dict(job_tmp=str(job),binaries=['no_such_runtime_binary' if name=='binary' else 'bash'])
    with patch.object(entry,'TMP_NAMESPACE',O),patch.object(os,'environ',environment):
        token=entry.create_job_tmp(job)
        if name=='nonempty':
            (job/'work').mkdir(mode=0o700);(job/'work/input.json').write_text('{}\n')
        try:result=entry.frame_host(value,job/'work',request,job_tmp_token=token)
        except ValueError as error:
            assert expected in str(error);result={'missing':[str(error)]}
        else:assert any(expected in e for e in result['missing']),result
    after=sum(inventory(L/'work/tmp').values());assert after<=200_000_000
    records.append(dict(case=name,expected=expected,result=result,before_bytes=before,after_bytes=after))
monitor.save(O)
(O/'RESULT.json').write_text(json.dumps(dict(cases=records,
    scope='Native CPU input checks. The temporary namespace and environment dictionary are unit-test inputs; physical CUDA visibility stays empty. No staging, model or GPU runs.'),indent=2)+'\n')
print(json.dumps([r['case'] for r in records]))
