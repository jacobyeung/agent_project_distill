from common import *
import ast,subprocess,copy
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
assert len(J.load(D/'TEST_RUNS.json'))==16 and all(r['returncode']==0 for r in J.load(D/'TEST_RUNS.json'))
seals={n:verify(kit(n)) for n in NAMES};assert seals==J.load(D/'SEALS.json')==J.load(D/'NATIVE_ARM_TESTS.json')['source_seals']
assert digest(inventory(T))=='0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de'
assert len({J.sha(kit(n)/'b/rb.py') for n in NAMES})==1
for name in NAMES:
 assert J.load(D/('SCAN_'+name+'.json'))['kit_seal']==seals[name]
 for p in (kit(name)/'b').glob('*.py'):compile(p.read_text(),str(p),'exec')
for case in J.load(D/'PROBE_TESTS.json'):
 if case['case']=='real':assert case['returncode']==0 and case['probe']['status']=='PASS' and len(case['probe']['modules'])==75
 else:assert case['returncode'] and case['probe']['status']=='REFUSE'
for name in ('EXTRA_TESTS','RCJ_TESTS','TRANSPORT_TESTS','RCJ_SCAN','OFFLINE','INTEGRATION'):
 assert J.load(D/(name+'.json'))['status']=='PASS',name
assert J.load(D/'NAMESPACE_TEST.json')['returncode']==0
assert J.load(D/'LOCAL_IMPORT_TRACE.json')['status']=='PASS'
assert len(J.load(D/'RCJ_PLAN_AUDIT.json')['required_hashes'])==65
assert not J.load(D/'RCJ_PLAN_AUDIT.json')['unmapped_hashes']
# Verify the helper bytes actually listed for upload, including executable mode.
u=J.load(L/'out/UPLOADS_24M4J.json');assert len(u['files'])==16
for row in u['files']:
 p=Path(row['local_path']);assert J.sha(p)==row['sha256'] and p.stat().st_size==row['bytes'] and p.stat().st_mode&511==int(row['mode'],8)
 if row['name'].startswith('rcj/'):assert p.read_bytes()==(L/'out'/row['name']).read_bytes()
assert set(u['baseline_kit_seals'])=={'q','n','qd'}
assert u['baseline_kit_seals']['qd'].startswith('62d8a7f5')
for path in (D/'arming_final/workspace/out/armed/UPLOADS_ROUTING_ARMED.json',D/'arming_final/workspace/out/native_armed/UPLOADS_ROUTING_ARMED.json'):
 v=J.load(path);assert set(v['baseline_kit_seals'])=={'q','n'}
 replay=copy.deepcopy(v['baseline_files'])
 for row in v['files']:
  n,rel=row['name'].split('/',1)
  if n in replay:replay[n][rel]=dict(sha256=row['sha256'],bytes=row['bytes'],mode=int(row['mode'],8))
 for n in ('q','n'):
  k=path.parent/'kits'/n
  assert replay[n]=={str(p.relative_to(k)):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob('*') if p.is_file()}
  assert all(n+'/'+rel in {r['name'] for r in v['files']} for rel in ('k/c.json','k/n.json','k/8.json','k/s.json'))
subprocess.run(['/bin/bash','-n',str(L/'out/rcj/rcj.sh')],check=True)
compile((L/'out/rcj/x.py').read_text(),str(L/'out/rcj/x.py'),'exec')
helpers={str(p.relative_to(L/'out')):dict(bytes=p.stat().st_size,sha256=J.sha(p)) for p in (L/'out/rcj').iterdir()};assert sum(v['bytes'] for v in helpers.values())<2_000_000
J.write(D/'VALIDATION.json',dict(status='PASS',kits=seals,tree_sha256=digest(inventory(T)),all_16_suites_pass=True,native_rb_rg_pl_tests=True,import_probe_modules=75,third_party=['PIL','numpy','scipy','tokenizers','torch','transformers'],missing_and_shadow_refusals=True,environment_and_tree_readonly=True,full_hash_gates_tested=True,arming_replay=True,upload_replay=True,CPU_helpers=helpers,CPU_transport_tests=True,production_reconstruction_executed=False,production_unavailable=['Original P archive bytes locally (file inventory authenticated instead)','Production row bodies','Production processor metadata'],no_orchard_or_scheduler_or_network_or_ssh_or_git_or_gpu_or_agents=True))
print('FINAL VALIDATION PASS',seals, 'helpers',helpers)
