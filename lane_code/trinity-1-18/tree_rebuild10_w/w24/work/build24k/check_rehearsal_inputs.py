"""Check the input cap and record the bounded probe's native result."""
import ast
import json
import sys
import subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths2 import D,R
from rehearsal_inputs2 import PLAN_LIMIT,DISK_LIMIT,plan_bytes,check_budget,usage

if '--inside-frame-test' in sys.argv:
    sys.path.insert(0,str(R/'source'))
    from rehearsal_inputs2 import frame_host
    from student_pilot.s1_admission import FrameAudit,verify_frames
    from student_pilot.orchard_paths import resolve_read as original
    plan=json.loads((R/'p2/plan.json').read_text())
    layout=json.loads((R/'INPUT_LAYOUT.json').read_text())
    root=plan['request']['frame_roots'][0]
    frame_host(root)
    from student_pilot.orchard_paths import resolve_read
    assert resolve_read('/tmp/unrelated')==original('/tmp/unrelated')
    output=R/'frame_audit_check';output.mkdir()
    audit=FrameAudit(output,[root],sample_size=1)
    try:
        audit.keep(dict(student_input=dict(frames=[dict(path='/data2/f.png',sha256=layout['frame_sha256'])])),'fixture')
        report=audit.finish()
    finally:audit.close()
    verify_frames(report)
    (output/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: native RGB containment, existence, SHA256 sample and inventory verification')
    raise SystemExit(0)

def rejected(planned,current):
    try:check_budget(planned,current)
    except RuntimeError:return True
    raise AssertionError('Oversized staging was accepted')

for name in ('rehearsal_inputs2.py','make_rehearsal_k2.py','rehearsal_boundary2.py',
             'rehearsal_runner2.py','rehearsal_paths2.py'):
    ast.parse((D/name).read_text(),filename=name)
old=json.loads((D/'rehearsal_k2_probe/p2/plan.json').read_text())
assert rejected(plan_bytes(old['entries']),0)
assert rejected(PLAN_LIMIT,0)
assert rejected(1,DISK_LIMIT-1)
check_budget(PLAN_LIMIT-1,0)
print('PASS: syntax, oversized previous plan, exact plan/disk caps, below-cap acceptance')

if '--frame-test' in sys.argv:
    view=json.loads((R/'VIEW.json').read_text())
    subprocess.run(view+[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'--inside-frame-test'],check=True)

if '--probe-result' in sys.argv:
    result=json.loads((R/'p2/q/RESULT.json').read_text())
    stages=json.loads((R/'STAGES.json').read_text())
    budgets={name:json.loads((R/name/'STAGING_BUDGET.json').read_text())
             for name in ('routing_retained','p2')}
    layout=json.loads((R/'INPUT_LAYOUT.json').read_text())
    incoming=json.loads((R/'r2.json').read_text())['_resolved']['request']
    assert incoming['frame_roots']==layout['frame_roots'] and '_paths' not in incoming
    assert incoming['staged_pins']==[]
    linked_checks=[]
    for name in ('routing_retained','p2'):
        plan=json.loads((R/name/'plan.json').read_text())
        assert plan_bytes(plan['entries']) < PLAN_LIMIT
        for h,item in layout['stores'].items():
            source=Path(item['path']).stat();staged=(R/name/'q/u'/h).stat()
            assert (source.st_dev,source.st_ino,source.st_size)==(staged.st_dev,staged.st_ino,staged.st_size)
            linked_checks.append(dict(stage=name,sha256=h,bytes=staged.st_size,same_inode=True))
    summary=dict(status='PASS' if result.get('status')=='REFUSE' and
                 result.get('refusal')=='ValueError:P_EXPORT_RUN_BINDING_MISMATCH' and
                 [(s['stage'],s['returncode']) for s in stages]==[('routing',0),('canary',1)]
                 else 'FAIL', expected_refusal='ValueError:P_EXPORT_RUN_BINDING_MISMATCH',
                 native_result=result,stages=stages,budgets=budgets,linked_store_checks=linked_checks,**usage(R),
                 furthest='native q: '+str(result.get('refusal')),
                 bytes_after_stop=usage(R)['new_bytes'],
                 training_executed=False,final_directory_absent=not (D/'rehearsal_k2').exists())
    (R/'PROBE_RESULT.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('native_result','stages','budgets','linked_store_checks')},indent=2))
    assert summary['status']=='PASS'
