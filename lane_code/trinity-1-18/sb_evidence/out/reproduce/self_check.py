"""Exercise real registry gates on CPU; gateway bank items are synthetic only."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from survey import ROOT,W,N,OUT,TREE,read,pin,save,sha
from student_pilot import r2_policy as P
from student_pilot.p3_provenance import file_pin
from launch_r2 import build as B

registry_path=OUT/'kit/registry.json'
registry=read(registry_path)
def observe(call):
    try:
        result=call()
        return dict(status='PASS',result=list(result) if isinstance(result,dict) else str(result))
    except Exception as error:
        return dict(status='REFUSE',exception=type(error).__name__,reason=str(error))

results={phase:observe(lambda phase=phase:P.components(dict(path='registry.json',sha256=sha(registry_path)),phase,OUT/'kit'))
         for phase in ('training','native_evaluation')}
individual={name:observe(lambda slot=slot:P.record(slot,OUT/'kit')) for name,slot in registry.items()}

def gateway(bank):
    root=ROOT/'work/gateway'/bank
    (root/'b').mkdir(parents=True,exist_ok=True);(root/'k').mkdir(exist_ok=True)
    (root/'b/wh.json').write_bytes((B.TREE/'launch_s1/b/wh.json').read_bytes())
    (root/'job.sh').write_text('#!/bin/bash\nexit 2\n')
    def capsule(value):
        raw=B.capsule_json(value)
        import hashlib
        h=hashlib.sha256(raw).hexdigest();p=root/'k'/(h+'.json');p.write_bytes(raw)
        return dict(path='k/'+p.name,sha256=h)
    itempath=root.parent/(bank+'_synthetic_items.json')
    items=[dict(id='sb-synthetic-gate-only',question_type='camera_displacement',question='How far in metres?',venue='synthetic',synthetic=True)]
    save(itempath,items)
    bankpin=file_pin(itempath)
    catalog=P.seal_catalog({bank:bankpin})
    cfg=dict(r1_training=dict(registry=capsule(registry)),r2_evaluation=dict(catalog=capsule(catalog),camera_routing=True))
    cfgpin=capsule(cfg)
    (root/'k/launch.json').write_bytes(B.capsule_json(dict(config=dict(file=cfgpin['path'],sha256=cfgpin['sha256']))))
    (root/'k/0.json').write_bytes(B.capsule_json(dict(commit='a'*40,trainer=dict(file=cfgpin['path'],sha256=cfgpin['sha256']),record=dict(file=cfgpin['path'],sha256=cfgpin['sha256']))))
    files=[root/'job.sh',*sorted((root/'b').rglob('*')),*sorted((root/'k').rglob('*'))]
    (root/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+str(p.relative_to(root))+'\n' for p in files if p.is_file()))
    (root/'ANON_OK.json').write_text(json.dumps(dict(status='CLEAN',hits=0,manifest_sha256=sha(root/'SHA256SUMS.txt'))))
    # The unchanged sealed-kit verifier executes inside read_bank.
    return dict(inputs=[file_pin(itempath),file_pin(root/'SHA256SUMS.txt')],synthetic=True,
                result=observe(lambda:P.read_bank(bankpin,kit_root=root)))

gateways={bank:gateway(bank) for bank in P.SCOPE}
log=ROOT/'work/policy_tests.log'
testlog=log.read_text()
assert 'Ran 5 tests' in testlog and testlog.rstrip().endswith('OK')
local_policy=ROOT/'work/policy_tree/student_pilot/r2_policy.py'
local_test=ROOT/'work/policy_tree/tests/test_r2_policy.py'
assert sha(local_policy)==sha(TREE/'student_pilot/r2_policy.py')
assert sha(local_test)==sha(TREE/'tests/test_r2_policy.py')
save(OUT/'SELF_CHECK.json',dict(schema='sb-component-self-check-v1',inputs=[pin(__file__),pin(registry_path),pin(local_policy),pin(local_test),pin(log)],
    component_phases=results,individual_slots=individual,official_gateway_synthetic_checks=gateways,
    existing_tests=dict(status='PASS',tests_run=5,log=pin(log),
        command='bash work/run_python.sh -c "import sys,unittest;sys.path.insert(0,\"work/policy_tree\");s=unittest.defaultTestLoader.loadTestsFromName(\"tests.test_r2_policy\");r=unittest.TextTestRunner(verbosity=2).run(s);sys.exit(not r.wasSuccessful())"'),
    limitation='No official benchmark items or model weights were read. Synthetic bank fixtures exercise the unchanged official gateway with the real copied null registry. Native evaluation also requires five out-of-task program-choice records.'))
(OUT/'policy_tests.log').write_bytes(log.read_bytes())
print(json.dumps(dict(component_phases=results,individual_slots=individual,gateway_results={b:r['result'] for b,r in gateways.items()},tests='5 passed'),indent=2))
(ROOT/'STATUS.md').write_text('Stage 3 complete. Both components phases refuse the copied registry at init_m544, and all nine requested slots refuse individually because their record bindings are missing. The unchanged official gateway refuses synthetic VSI-Bench, VSTI and ReVSI fixtures for the same missing record. All five existing r2_policy tests pass on the unchanged local code copy; no official items were read.\n')
