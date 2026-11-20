from common import *
import re,copy
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from student_pilot.carrier_c1_run import identity
from launch_r1.build import verify
tree=J.load(D/'TREE_CPRIME.json');assert inventory(T)==tree['inventory']
assert digest(inventory(T))=='de202f58b31793608f886360a9fdfb5f58c24932e35976efcf74acead62e3cfe'
tests=J.load(D/'TREE_TESTS.json');assert [r['tests'] for r in tests]==[15,3] and all(r['successful'] and not r['skipped'] and not r['errors'] and not r['failures'] for r in tests)
runs=J.load(D/'TEST_RUNS.json');assert len(runs)==16
final=copy.deepcopy(runs)
for r in final:
 r['log']='work/build24m4m/'+r['name']+'.log'
 if r['name']=='kit_tests':
  r.update(returncode=J.load(D/'RETEST_RUNS.json')[0]['returncode'],log='work/build24m4m/kit_tests_m2.log')
assert all(r['returncode']==0 for r in final),final
J.write(D/'FINAL_TEST_RUNS.json',final)
fixtures=J.load(D/'FIXTURE_RUNS.json');assert len(fixtures)==11
assert all(r['returncode']==0 for r in fixtures if r['name']!='rdiff_mount_test')
checks=('PIN_AUDIT','EXACT_KIT_DELTA','COMMAND_TESTS','RCJ_L_TESTS','SAMPLE_FINAL_TESTS','PC_INTEGRATION_TESTS','MOUNT_TESTS','RDIFF_MOUNT_TEST','RCJ_CONTRACT_TESTS','RCJ_SCAN','MODE_R_PLAN_TEST','TRANSPORT_TESTS','QD_STEP1_TESTS','UPLOAD_REPLAY','INVARIANTS')
evidence={}
for n in checks:
 p=D/(n+'.json');assert J.load(p)['status']=='PASS',n
 evidence[n]=dict(path=str(p.relative_to(L)),sha256=J.sha(p))
seals={n:verify(kit(n)) for n in NAMES};assert seals==J.load(D/'SEALS.json')==J.load(D/'ARM_BASE_SEALS.json')==J.load(D/'NATIVE_ARM_TESTS.json')['source_seals']
for n in NAMES:
 assert J.load(kit(n)/'k/a.json')['GO']==J.load(kit(n)/'BUILD.json')['GO']==(n=='n_go')
 assert J.load(D/('SCAN_'+n+'.json'))['kit_seal']==seals[n]
 for f in ('k/c.json','k/n.json'):
  c=J.load(kit(n)/f);assert c['max_pixels'] is None and c['min_pixels'] is None and c['frame_count']==32
for f in ('k/c.json','k/n.json'):assert J.load(kit('qd')/f)==J.load(kit('n')/f)
assert len(J.load(D/'HANDOVER_TESTS.json'))==8
assert all(x['status']=='PASS' for x in J.load(D/'HANDOVER_TESTS.json'))
up=J.load(L/'out/UPLOADS_24M4M.json');go=J.load(L/'out/UPLOADS_24M4M_GO.json')
for v in (up,go):
 assert len(v['files'])==v['total_files'] and sum(r['bytes'] for r in v['files'])==v['total_bytes']
 for r in v['files']:
  p=Path(r['local_path']);assert p.is_relative_to(L) and J.sha(p)==r['sha256'] and p.stat().st_size==r['bytes'] and format(p.stat().st_mode&511,'04o')==r['mode']
assert not any(r['name'].startswith('n_go/') or r['name']=='rcj/rcj.sh' for r in up['files'])
assert [r['name'] for r in up['files']]==(L/'out/UPLOADS_24M4M.list').read_text().splitlines()
assert up['baseline_kit_seals']==J.load(L/'out/UPLOADS_24M4L.json')['baseline_kit_seals']
assert up['baseline_rcj']['x.py']['sha256']==J.sha(D/'reviewed_x.py')
replay={str(p.relative_to(kit('n'))):J.sha(p) for p in kit('n').rglob('*') if p.is_file()}
for r in go['files']:replay[r['name'].split('/',1)[1]]=r['sha256']
assert replay=={str(p.relative_to(kit('n_go'))):J.sha(p) for p in kit('n_go').rglob('*') if p.is_file()}
helpers={p.name:J.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}
assert {n for n,h in helpers.items() if h!=J.load(D/'BASE_RCJ.json')[n]['sha256']}=={'x.py'}
failures=[]
for p in sorted(D.glob('*.log')):
 text=p.read_text(errors='replace')
 if any(s in text for s in ('Traceback (most recent','FAILED (','Read-only file system')):
  failures.append(dict(path=str(p.relative_to(L)),sha256=J.sha(p),output=text))
J.write(D/'FAILURES.json',dict(status='RESOLVED',records=failures,setup_fixes=['Runner J changed to current workspace before build started.','Native host comparison supplied untouched tree C at its expected sibling path.','Kit fixture uses the copied input inventory.','Rdiff fixture exposes local interpreter roots and stages the source tree inside its job root.'],cluster_kill=False,production_code_changes_for_fixtures=False))
v=dict(status='PASS',qualification='Required tree tests, all 16 kit suites and CPU helper fixtures pass; no production or GPU execution.',tree_sha256=tree['after'],kits=seals,n_go_identity=identity(J.load(kit('n_go')/'k/c.json')),tree_tests=tests,suites=final,evidence=evidence,helpers=helpers,ordinary_files=up['total_files'],ordinary_bytes=up['total_bytes'],GO_overlay_files=go['total_files'],independent_review='GO AFTER FIXES; exact required and recommended test edits applied',production_executed=False,uploaded=False,launched=False)
J.write(D/'VALIDATION.json',v)
lines=[f"C″ {tree['after']}; q {seals['q']}; n {seals['n']}; n_go {seals['n_go']}; qd {seals['qd']}; kit_n_go identity {v['n_go_identity']}.",
 'The exact Cursor test patch produces 945 files; only test_host24j.py differs from C′ and exactly four files differ from C.',
 'Host admission passes 15/15 and processor compatibility 3/3, with no skips; TREE_CPRIME2.md records both patch hashes and the tree evidence.',
 'Each kit changes exactly nine tree-dependent files; archives, source pins, config identities, SHA256SUMS and BUILD.json verify; all other fields and files match 24m4l.',
 'Mode-r launch and rdiff use the reviewed host_root; processor N/P children already assemble an empty root. Mode-b plan/run/check commands are byte-identical to 24m4l.',
 'All 16 kit, scan, naming, resolver, guard and arming suites pass. CPU fixtures cover sampling, refusal, staging, publication, real mounts, processor 40+40/fallback checks and deliberate mismatch.',
 'Eight native handovers pass; qd/n configs remain equal, with null pixels and 32 frames; the discovery fixture verifies 288 step-1 selections.',
 f"UPLOADS_24M4M.json/.list contain {up['total_files']} files ({up['total_bytes']} bytes) against the requested Orchard baseline; the separate GO overlay has three files. GO is false except out/kit_n_go.",
 'Arming baselines and usage use 24m4m. VALIDATION.json records checks; FAILURES.json retains resolved fixture/setup failures with exact output.',
 'No network, SSH, Orchard, Git, scheduler, GPU or other-agent work ran; production rows and real processor assets were not tested.',
 'DELIVERY_24M4M.json and PACKAGE_CHECK.json identify the full archive, checksum and verified members; superseded input bytes remain in attic.'
]
assert len(lines)<12
replace(L/'out/BUILD24M4M_REPORT.md','\n'.join(lines)+'\n')
print('VALIDATION PASS',seals,'N_GO_IDENTITY',v['n_go_identity'])
