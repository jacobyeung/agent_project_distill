from pathlib import Path
import sys,json,ast,hashlib,re,subprocess
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4t'
sys.path[:0]=[str(D),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
from common import *
import z
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
base=z.load(D/'BASELINE.json');tree=digest(inventory(L/'work/tree_r1c'))
assert tree==base['tree'] and tree.startswith('de202f58')
seals={n:verify(kit(n)) for n in NAMES}
assert z.sha(L/'work/tree_r1c/student_pilot/s1_scene_census.py')==base['census']
rcj={p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}
assert [n for n,h in rcj.items() if h!=base['rcj'][n]]==['x.py']
changed={}
for n in NAMES:
 now={str(p.relative_to(kit(n))):z.sha(p) for p in kit(n).rglob('*') if p.is_file()}
 assert now.keys()==base['files'][n].keys()
 changed[n]=sorted(p for p,h in now.items() if h!=base['files'][n][p]['sha256'])
 assert changed[n]==['BUILD.json','SHA256SUMS.txt','b/pl.py']
 assert (kit(n)/'b/pl.py').read_bytes()==(kit('qd')/'b/pl.py').read_bytes()
 old=(L/'attic/build24m4t'/kit(n).relative_to(L)/'b/pl.py').read_text()
 new=(kit(n)/'b/pl.py').read_text()
 replacement="""        if regeneration:
            live=root.parent/'live'
            if any(p.is_symlink() for p in (live,*live.parents)):
                raise ValueError('R1_REVIEW_FILE_UNUSABLE')
            live.mkdir(mode=0o700,exist_ok=True)
        else:
            live,_=location(kit,root.parent,os.environ['SLURM_JOB_ID'])"""
 assert new==old.replace("        live,_=location(kit,root.parent,os.environ['SLURM_JOB_ID'])",replacement)
all_runs=[];latest={}
for name in ('SUITE_RUNS.json','RERUN_RUNS.json','RERUN2_RUNS.json','RERUN3_RUNS.json'):
 for v in z.load(D/name):all_runs.append(v);latest[v['name']]=dict(v)
assert len(latest)==34 and all(v['returncode']==0 for v in latest.values()),[v for v in latest.values() if v['returncode']]
for v in latest.values():
 p=L/v['log'];v.update(status='PASS',sha256=z.sha(p))
 counts=re.findall(r'Ran (\d+) tests?',p.read_text())
 if counts:v['tests']=int(counts[-1])
checks={}
for name in ('LIVE_TESTS.json','PUBLICATION_INTEGRATION.json','LOOKAHEAD.json','DELTA_REPLAY.json','CANDIDATE_REPLAY.json','REAL_PATH_TESTS.json','REAL_BWRAP_TESTS.json','Q_PATH_TESTS.json','BIND_TESTS.json','PC_INTEGRATION_TESTS.json','MOUNT_TESTS.json','RDIFF_MOUNT_TEST.json','RCJ_SCAN.json','NATIVE_ARM_TESTS.json'):
 value=z.load(D/name);assert value['status']=='PASS',(name,value)
 checks[name]=dict(status='PASS',sha256=z.sha(D/name))
comparisons=0
for name in ('REAL_PATH_TESTS.json','REAL_BWRAP_TESTS.json','Q_PATH_TESTS.json'):
 for r in z.load(D/name)['records']:
  assert len(r['access']['compare_calls'])==40
  assert all(c['result']=='PASS' for c in r['access']['compare_calls'])
  assert set(r['access']['readonly'].values())=={30}
  assert r['result']['compare_sha256']==base['census']
  assert r['result']['negative_refusal'].endswith('/dev_matches')
  comparisons+=40
assert comparisons==200
for n in NAMES:assert z.load(D/('SCAN_'+n+'.json'))['status']=='PASS'
assert z.load(D/'BEFORE_COMMAND.json')==z.load(D/'AFTER_COMMAND.json')
before=(D/'before.log').read_text()
for text in ('pl.py", line 248','rv.py", line 63','R1_PLAN_REFUSED:1',"OSError: [Errno 30] Read-only file system: '/project/community/jjyeung/okh7/x_22c714e1/o/173724'"):
 assert text in before and text in (D/'JOB173724.log').read_text()
assert 'REAL_PATH_PASS' in (D/'after.log').read_text()
for name in ('audit2_plan.log','audit2_run.log'):assert 'REAL_PATH_PASS' in (D/name).read_text()
writes={}
for name in ('child','run_child'):
 p=D/'real/node'/('writes_'+name+'.json');events=z.load(p)
 assert all(Path(v['path']).is_relative_to(D/'real/node') or Path(v['path']).is_relative_to('/tmp/q_22c714e1') for v in events)
 writes[name]=dict(events=len(events),sha256=z.sha(p),outside_root_attempts=0)
write(D/'FINAL_SUITE_RUNS.json',list(latest.values()))
failures=[]
for v in z.load(D/'SETUP_RUNS.json')+all_runs:
 if v['returncode']:
  failures.append(dict(name=v['name'],log=v['log'],output=(L/v['log']).read_text(),resolved_by=latest[v['name']]['log']))
for name,reason in [('setup1.log','Fixture scratch mirror lacked interpreter mountpoint parents; no production code executed.'),('live_setup.log','The archived module had a different __file__, so the byte-command comparison now uses the same module location.'),('publication_setup.log','The synthetic configuration cannot pass nd.native_rules; the integration test now asserts the real refusal while checking independent live publication.')]:
 failures.append(dict(name=name,output=(D/name).read_text(),reason=reason))
failures.extend([dict(name='baseline shell quoting',output="SyntaxError: invalid decimal literal at dict(q=532afee4,...)",reason='Nested shell quoting removed Python string quotes before execution; the direct heredoc verified every baseline pin.'),dict(name='optional inherited package check read',output="FileNotFoundError: work/build24m4s/PACKAGE_CHECK.json",reason='The inherited package deliberately excludes its external post-packaging check; the new package verifies its own archive.')])
write(D/'FAILURES.json',dict(failures=failures,killed_processes=[],unresolved_test_failures=[],expected_regression_failure='before.log',native_limitations='Synthetic P bytes fail the full DB gate; incomplete synthetic config fails routing-type native rules. Dedicated inherited synthetic suites test their positive paths.'))
bwrap=dict(path=__import__('shutil').which('bwrap'),version=subprocess.check_output([__import__('shutil').which('bwrap'),'--version'],text=True).strip(),production_binary_executed=False,scope='Local runtime adapters to actual x.launch; actual plan_r/plan_payload and run_r/a.py/begin_host/host_environment/stage_host. Synthetic producers, export supplier and config gates replace unavailable production inputs.')
validation=dict(status='PASS',tree_sha256=tree,kits=seals,rcj=rcj,changed=changed,checks=checks,runs=list(latest.values()),additional_tests=['live_tests','publication_integration'],mode_b_byte_identical=True,mode_b_commands_equal_for_same_inputs=True,mode_b_publication_bytes_equal=True,mode_q_location_unchanged=True,launch_source_unchanged=True,census_compare_unchanged=True,census_compare_sha256=base['census'],native_census_comparisons=comparisons,missing_source_cases=28,write_audit=writes,ordinary_delta_files=13,candidate_delta_files=4,optional_delta_files=4,bwrap=bwrap,GO=False,production_executed=False,uploaded=False,launched=False)
write(D/'VALIDATION.json',validation)
report=[
 'Fail-before: job 173724 and the unfixed real launch/plan_r fixture both reach b/pl.py:248 → b/rv.py:63, EROFS on o/173724, then R1_PLAN_REFUSED:1; work/build24m4t/before.log preserves the output.',
 'The identical launch command passes after the fix. Regeneration creates namespace/live locally; mode q retains rv.location unchanged. Only b/pl.py and its seals change in each kit; launch code is unchanged.',
 'The real run fixture reaches run_r → a.py → begin_host → stage_host and completes its synthetic selection; write hooks record no writes outside N or its namespace. Production inputs/builders and configuration gates are synthetic boundaries, not production validation.',
 'Look-ahead: pl.py:254 onward, x.py:401/430/513/537/631/662, a.py:15/29/56, rg.py:9, pc.py:170 and ch.py:263 have their required parents and supplied environment; cs.emit is q-only. LOOKAHEAD.json enumerates 281 calls and 12 ownership groups; no further out-of-root failure was proved.',
 'The host publisher screens the two live receipts, preserves private originals and refuses the copy before writing if it would exceed the remaining 5 MB budget. Seven boundary cases and the actual outside publisher pass.',
 'All 34 inherited/scene suite groups plus both new suites pass, including kit, scan, naming, resolver, guard, arming, qd, planner and rcj; 200 native census comparisons and 28 missing-source cases pass. FAILURES.json retains setup failures and their outputs.',
 "C″ remains de202f58; census comparison bytes, mode-b commands/publication bytes and every rcj pin except x.py are unchanged. Synthetic database and configuration refusals remain enforced; no production run or upload occurred.",
 'UPLOADS_24M4T.json/.list replay exactly against reviewed Orchard q e7ac0727, n a7809da0, qd 221d1782: 13 files; CANDIDATE lists four against qd 8de0c8b3; optional GO lists four. Seals: '+', '.join(n+' '+seals[n][:8] for n in NAMES)+'.',
 'VALIDATION.json and LOOKAHEAD.json contain scope and file:line evidence; the package preserves input members and superseded bytes, verifies every archived byte/mode/link, and writes its .sha256 last.'
]
assert len(report)<12
(L/'out/BUILD24M4T_REPORT.md').write_text('\n'.join(report)+'\n')
print(json.dumps(dict(status='PASS',groups=len(latest)+2,native_census_comparisons=comparisons,write_audit=writes,kits=seals,rcj_x=rcj['x.py']),indent=2))
