from common import *
import re
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from student_pilot.carrier_c1_run import identity
from launch_r1.build import verify
tree=J.load(D/'TREE_CPRIME.json');before=inventory(L/'work/tree_r1');after=inventory(T)
assert digest(before)==tree['before'] and digest(after)==tree['after']
assert after==tree['inventory']
changed={k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)}
assert changed==set(tree['changed'])=={'student_pilot/carrier_c1_run.py','launch_r1/entry.py','tests/test_r1_processor_compat.py'}
assert J.sha(L/'out/TREE_CHANGE_24M4K.patch')==tree['patch_sha256']
seals={n:verify(kit(n)) for n in NAMES};assert seals==J.load(D/'SEALS.json')
configs=[]
for n in NAMES:
 assert J.load(kit(n)/'k/a.json')['GO']==(n=='n_go')
 assert J.load(kit(n)/'BUILD.json')['GO']==(n=='n_go')
 for file in ('k/c.json','k/n.json'):
  c=J.load(kit(n)/file)
  assert c['max_pixels'] is None and c['min_pixels'] is None and c['frame_count']==32
  configs.append(dict(kit=n,file=file,identity=identity(c),max_pixels=None,min_pixels=None,frame_count=32))
for file in ('k/c.json','k/n.json'):assert J.load(kit('n')/file)==J.load(kit('qd')/file)
assert J.load(kit('qd')/'k/n.json')['r1_training']['init_policy']=='step400_export_weights_fresh_v1'
assert not any((kit('qd')/'b'/f).exists() for f in ('t.py','u.py','e.sh'))
runs=J.load(D/'TEST_RUNS.json');assert len(runs)==16 and all(v['returncode']==0 for v in runs)
checks=['PIN_AUDIT','RCJ_L_TESTS','SAMPLE_FINAL_TESTS','PC_INTEGRATION_TESTS','MOUNT_TESTS','RDIFF_MOUNT_TEST','RCJ_CONTRACT_TESTS','RCJ_SCAN','MODE_R_PLAN_TEST','TRANSPORT_TESTS','QD_STEP1_TESTS','UPLOAD_REPLAY','INVARIANTS']
evidence={}
for name in checks:
 p=D/(name+'.json');v=J.load(p);assert v['status']=='PASS',(name,v.get('status'))
 evidence[name]=dict(path=str(p.relative_to(L)),sha256=J.sha(p))
handover=J.load(D/'HANDOVER_TESTS.json');assert len(handover)==8 and all(x['status']=='PASS' for x in handover)
probe=J.load(D/'pc_integration/both/proc_check.json')
for row in probe['rows'][:40]:
 text=''.join(chr(i-10) for i in row['n']['values']['target_ids'])
 assert 'Check' in text and 'stale fixture target' not in text
 text=''.join(chr(i-10) for i in row['n']['values']['prompt_ids'])
 flag=J.load(kit('n')/'k/n.json').get('tool_mode_flag')
 assert not flag or flag in text
raw=J.load(D/'TREE_TESTS.json');fixed=J.load(D/'TREE_FIXTURE_TESTS.json')
assert raw['tests']==37 and len(raw['errors'])==2 and len(raw['skipped'])==2 and not raw['failures']
assert fixed['successful'] and fixed['tests']==2
assert J.sha(L/'out/rcj/ps.py')==J.sha(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/ps/ps.py'))
assert J.sha(L/'out/rcj/rcj.sh')==J.load(D/'BASE_RCJ.json')['rcj.sh']['sha256']
up=J.load(L/'out/UPLOADS_24M4N.json');go=J.load(L/'out/UPLOADS_24M4N_GO.json')
for spec in (up,go):
 for r in spec['files']:
  p=Path(r['local_path']);assert J.sha(p)==r['sha256'] and p.stat().st_size==r['bytes'] and format(p.stat().st_mode&511,'04o')==r['mode']
 assert sum(r['bytes'] for r in spec['files'])==spec['total_bytes'] and len(spec['files'])==spec['total_files']
assert not any(r['name'].startswith('n_go/') or r['name']=='rcj/rcj.sh' for r in up['files'])
assert [r['name'] for r in up['files']]==(L/'out/UPLOADS_24M4N.list').read_text().splitlines()
replayed={str(p.relative_to(kit('n'))):J.sha(p) for p in kit('n').rglob('*') if p.is_file()}
for r in go['files']:replayed[r['name'].split('/',1)[1]]=r['sha256']
assert replayed=={str(p.relative_to(kit('n_go'))):J.sha(p) for p in kit('n_go').rglob('*') if p.is_file()}
logs=[]
for p in sorted(D.glob('*.log')):
 lines=p.read_text(errors='replace').splitlines()
 bad=[(i,l[:1200]) for i,l in enumerate(lines,1) if re.search(r'Traceback \(most recent|AssertionError|^FAILED|^ERROR:|^ValueError:|^FileNotFoundError:|^ModuleNotFoundError:|^TypeError:|^KeyError:',l)]
 if bad:logs.append(dict(path=str(p.relative_to(L)),sha256=J.sha(p),matches=bad,output_tail='\n'.join(lines[-5:])[-2500:]))
J.write(D/'FAILURES.json',dict(raw_tree_errors=raw['errors'],raw_tree_skips=raw['skipped'],fixture_adaptations=fixed,
 diagnostic_logs=logs,note='Logs include corrected build/fixture failures and deliberate negative cases. Full output is retained at each path. No killed cluster job was retried.'))
v=dict(status='PASS',qualification='Local build and fixtures pass; unchanged tree suite has two documented fixture errors and two skips.',
 tree_sha256=tree['after'],kits=seals,n_go_identity=identity(J.load(kit('n_go')/'k/c.json')),changed_tree_files=sorted(changed),configs=configs,
 suites=runs,evidence=evidence,tree_tests=dict(total=37,passed=33,errors=2,skipped=2,corrected_fixture_tests_passed=2),
 handover_configs=8,qd_config_differences=[],ordinary_upload_files=up['total_files'],GO_overlay_files=go['total_files'],
 production_executed=False,real_rows_checked=False,gpu_executed=False,uploaded=False,launched=False,
 failures='work/build24m4o/FAILURES.json',processor_fixture='Native isolated constructors and encoders; synthetic rows, stubbed tokenizer loading.',
 independent_patch_review='No review result received in this build session.')
J.write(D/'VALIDATION.json',v)
lines=[f"C′ {tree['after']}; q {seals['q']}; n {seals['n']}; n_go {seals['n_go']}; qd {seals['qd']}; kit_n_go identity {v['n_go_identity']}.",
 'C′ contains exactly the authorized patch’s three files; out/TREE_CPRIME.md records its seal, patch hash and tests.',
 'All eight decoded configs retain null pixel fields and 32 frames; native handover comparisons pass.',
 'All dependent pins and four archives verify; work/build24m4o/DEPENDENT_PINS.json lists them.',
 'Discovery uses the fresh step-400 policy with proof_mode=train; qd/N config templates are identical. The native selection fixture checks 288 step-1 rows; out/QD_STEP1.md gives the path and limits.',
 'The CPU helper preserves b/r launch fixes, uses the unchanged sample reference, and records sample refusal without failing either mode.',
 'Mode r publishes isolated per-row processor checks; 40+40 fixtures pass, 80-row fallback works, and a deliberate processor mismatch fails after publication.',
 'All 16 kit/scan/naming/resolver/guard/arming suites pass; sample gate, 5 MB refusal, staging, transport and read-only publication fixtures pass.',
 'The original C′ suites ran 37 tests: 33 passed, two skipped and two fixture errors. Both externally corrected fixtures pass; C′ test files remain unchanged.',
 'work/build24m4o/FAILURES.json links the retained error output and fixture corrections; work/build24m4o/VALIDATION.json records final checks.',
 f"The ordinary delta contains {up['total_files']} files ({up['total_bytes']} bytes); out/UPLOADS_24M4N_GO.json separately contains three GO overlay files. GO is false except out/kit_n_go.",
 'out/RCJ_USAGE.md and out/ARM_ROUTING_USAGE.md describe the helpers; arming baselines use 24m4l.',
 'No production rows, GPU forward, Orchard upload or job launch ran locally. No independent patch-review result was received.',
 'out/DELIVERY_24M4N.json identifies the full package, checksum and verified member inventory.' ]
assert len(lines)<15
replace(L/'out/BUILD24M4N_REPORT.md','\n'.join(lines)+'\n')
print('FINAL VALIDATION PASS; 16 suites; 8 handovers; documented raw tree fixture errors/skips; delta',up['total_files'],up['total_bytes'])
