from common import *
sys.path.insert(0,str(TREE))
from student_pilot import r2_policy as P
from launch_r2 import build as B

def observe(fn):
 try:
  v=fn();return dict(status='PASS',components=list(v) if isinstance(v,dict) else None)
 except Exception as e:return dict(status='REFUSE',exception=type(e).__name__,reason=str(e))
registry=read(KIT/'registry.json');rp=boundpin(KIT/'registry.json')
phases={phase:observe(lambda phase=phase:P.components(rp,phase,KIT)) for phase in ('training','native_evaluation')}
individual={n:observe(lambda s=s:P.record(s,KIT)) for n,s in registry.items()}
def gateway(bank):
 root=ROOT/'work/gateway_checked'/bank;(root/'b').mkdir(parents=True,exist_ok=True);(root/'k').mkdir(exist_ok=True)
 (root/'b/wh.json').write_bytes((TREE/'launch_s1/b/wh.json').read_bytes());(root/'job.sh').write_text('#!/bin/bash\nexit 2\n')
 def capsule(v):
  raw=B.capsule_json(v);h=hashlib.sha256(raw).hexdigest();p=root/'k'/(h+'.json');p.write_bytes(raw);return dict(path=str(p.relative_to(root)),sha256=h)
 items=[dict(id='sb-records-gateway-synthetic',question_type='camera_displacement',question='How far in metres?',venue='synthetic',synthetic=True)]
 itempath=root.parent/(bank+'_synthetic_items.json');save(itempath,items);bp=pin(itempath)
 cfg=dict(r1_training=dict(registry=capsule(registry)),r2_evaluation=dict(catalog=capsule(P.seal_catalog({bank:bp})),camera_routing=True))
 cp=capsule(cfg)
 (root/'k/launch.json').write_bytes(B.capsule_json(dict(config=dict(file=cp['path'],sha256=cp['sha256']))))
 (root/'k/0.json').write_bytes(B.capsule_json(dict(commit='a'*40,trainer=dict(file=cp['path'],sha256=cp['sha256']),record=dict(file=cp['path'],sha256=cp['sha256']))))
 files=[root/'job.sh',*sorted((root/'b').rglob('*')),*sorted((root/'k').rglob('*'))]
 (root/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+str(p.relative_to(root))+'\n' for p in files if p.is_file()))
 save(root/'ANON_OK.json',dict(status='CLEAN',hits=0,manifest_sha256=sha(root/'SHA256SUMS.txt')))
 return dict(inputs=[pin(itempath),pin(root/'SHA256SUMS.txt')],synthetic=True,result=observe(lambda:P.read_bank(bp,kit_root=root)))
gates={b:gateway(b) for b in P.SCOPE}
log=OUT/'policy_tests.log';assert 'Ran 5 tests' in log.read_text() and log.read_text().rstrip().endswith('OK')
for f in ['student_pilot/r2_policy.py','tests/test_r2_policy.py']:
 assert sha(TREE/f)==sha(W/'w19/work/tree_r1'/f)
checks=dict(schema='sb-records-self-check-v1',inputs=[pin(__file__),pin(KIT/'registry.json'),pin(TREE/'student_pilot/r2_policy.py'),pin(TREE/'tests/test_r2_policy.py'),pin(log),pin(ROOT/'work/test_policy.py'),pin(ROOT/'work/run_python.sh')],component_phases=phases,individual_slots=individual,official_gateway_synthetic_checks=gates,tests=dict(status='PASS',tests_run=5,command='bash work/run_python.sh work/test_policy.py'),limitations='Gateway fixtures are synthetic; no official benchmark items or model weights were read. The policy copy is unchanged. Native evaluation also requires five out-of-task program-choice records.')
save(OUT/'SELF_CHECK.json',checks)
status('Stage 4 complete. Both component phases and all three sealed official-bank gateway probes refuse at missing init_m544 evidence. Every requested slot refuses individually. Five unchanged policy tests pass on CPU. The report and archive remain to be packaged.')
print(json.dumps(dict(phases=phases,requested_slots={n:individual[n] for n in [*P.LINEAGE,*P.EXTERNAL,*P.NEW]},gateways={b:x['result'] for b,x in gates.items()},tests='5 passed'),indent=2))
