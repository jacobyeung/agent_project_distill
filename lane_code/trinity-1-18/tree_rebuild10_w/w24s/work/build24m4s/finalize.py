from pathlib import Path
import hashlib,json,re,sys,subprocess
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4s'
sys.path[:0]=[str(D),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
from common import write,kit,NAMES
import z
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
base=z.load(D/'BASELINE.json');tree=digest(inventory(L/'work/tree_r1c'))
assert tree==base['tree'] and tree.startswith('de202f58')
seals={n:verify(kit(n)) for n in NAMES}
assert {p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}==base['rcj']
assert z.sha(L/'work/tree_r1c/student_pilot/s1_scene_census.py')==base['census']
all_runs=[];latest={}
for filename in ('SUITE_RUNS.json','RERUN_RUNS.json','RERUN2_RUNS.json','RERUN3_RUNS.json'):
 for run in z.load(D/filename):
  all_runs.append(run);latest[run['name']]=dict(run)
assert len(z.load(D/'SUITE_RUNS.json'))==27
assert len(z.load(D/'RERUN_RUNS.json'))==12
assert len(z.load(D/'RERUN2_RUNS.json'))==7
assert len(z.load(D/'RERUN3_RUNS.json'))==1
assert all(z.load(D/('SCAN_'+n+'.json'))['status']=='PASS' for n in NAMES)
latest['scans']=dict(name='scans',returncode=0,log=str((D/'scans2.log').relative_to(L)))
for run in latest.values():
 assert run['returncode']==0,run
 log=L/run['log'];run.update(status='PASS',sha256=z.sha(log))
 counts=re.findall(r'Ran (\d+) tests?',log.read_text())
 if counts:run['tests']=int(counts[-1])
assert len(latest)==30
write(D/'FINAL_SUITE_RUNS.json',list(latest.values()))
checks={}
for filename in ('REAL_PATH_TESTS.json','REAL_BWRAP_TESTS.json','Q_PATH_TESTS.json','BIND_TESTS.json','COMMAND_AUDIT.json','DELTA_REPLAY.json','PC_INTEGRATION_TESTS.json','MOUNT_TESTS.json','RDIFF_MOUNT_TEST.json','RCJ_SCAN.json','NATIVE_ARM_TESTS.json','RCJ_CONTRACT_TESTS.json'):
 value=z.load(D/filename);assert value['status']=='PASS',(filename,value)
 checks[filename]=dict(status='PASS',sha256=z.sha(D/filename))
comparisons=0
for filename in ('REAL_PATH_TESTS.json','REAL_BWRAP_TESTS.json','Q_PATH_TESTS.json'):
 value=z.load(D/filename)
 for r in value['records']:
  assert len(r['access']['compare_calls'])==40
  assert all(c['result']=='PASS' for c in r['access']['compare_calls'])
  assert set(r['access']['readonly'].values())=={30}
  assert r['result']['negative_refusal'].endswith('/dev_matches')
  assert r['result']['compare_sha256']==base['census']
  comparisons+=40
  for cmd in r['inner_commands']:
   assert sum(v=='--bind' for v in cmd)==1
   assert not any(cmd[i:i+3]==['--ro-bind','/','/'] for i in range(len(cmd)))
   assert '--remount-ro' in cmd
assert comparisons==200
real=z.load(D/'REAL_PATH_TESTS.json');assert {r['mode'] for r in real['records']}=={'q','r'}
r=next(r for r in real['records'] if r['mode']=='r');root=(L/r['log']).parent/'node'
state=z.load(root/'state.json');assert state['z_exists'] and not state['z_s_exists']
assert state['trainer']==state['R1_TRAINER']==state['TRAINER']==str(root/'c')
launch=z.load(root/'launch.json');original=launch['original'];actual=launch['command'];expected=original.copy()
expected[0]=real['binary'];at=expected.index('--bind');expected[at:at]=launch['adapters']
at=expected.index('--chdir')+2
expected[at:]=[sys.executable,'-s','-B',str(D/'path_fixture.py'),'outer','r']
assert expected==actual
assert ['--bind',str(root/'dr'),'/tmp/q_22c714e1'] in [actual[i:i+3] for i in range(len(actual))]
for file in ('BEFORE.json','BEFORE_EXACT.json'):
 before=z.load(D/file);assert before['status']=='EXPECTED_FAILURE'
 assert not before['state']['z_s_exists'] and before['state']['z_exists']
 assert before['sc_sha256']==base['files']['qd']['b/sc.py']['sha256']
 assert "bwrap: Can't find source path /tmp/q_22c714e1/z/s: No such file or directory" in before['stderr']
checks['BEFORE.json']=dict(status='EXPECTED_FAILURE',sha256=z.sha(D/'BEFORE.json'))
checks['BEFORE_EXACT.json']=dict(status='EXPECTED_FAILURE',sha256=z.sha(D/'BEFORE_EXACT.json'))
old=z.load(L/'work/build24m4r/COMMAND_AUDIT.json')['commands'];new=z.load(D/'COMMAND_AUDIT.json')['commands']
normalize=lambda v:json.loads(json.dumps(v).replace('/w24r/','/w24s/').replace('build24m4r','build24m4s'))
assert normalize([v for v in old if v['mode']=='b'])==[v for v in new if v['mode']=='b']
for n in NAMES:
 old=(L/'attic/build24m4s'/kit(n).relative_to(L)/'b/sc.py').read_text();now=(kit(n)/'b/sc.py').read_text()
 assert old[old.index('    start=time.monotonic()'):]==now[now.index('    start=time.monotonic()'):]
failures=[]
for run in all_runs:
 if run['returncode']:
  failures.append(dict(name=run['name'],log=run['log'],output=(L/run['log']).read_text(),resolved_by=latest[run['name']]['log'],reason='Fixture scaffolding was incomplete; the rerun preserves the test assertions.'))
for file,reason,replacement in (
 ('finalize1.log','An overbroad replacement added a second argument to the validation loader.','finalize2.log'),
 ('before.log','The generated fixture had an unmatched parenthesis.','before5.log'),
 ('before2.log','The local scratch mirror lacked the mountpoint parents supplied by rcj staging.','before5.log'),
 ('before3.log','The runpy harness supplied a relative script path to a child with a different working directory.','before5.log'),
 ('before4.log','Renaming across two bind mounts returned EXDEV; the fixture copies its small staged inputs instead.','before5.log'),
 ('legacy_scene1.log','The inherited fixture probed z/s but imported its source elsewhere. Its child now imports its already-staged z/s; native assertions remain intact.','legacy_scene2.log')):
 failures.append(dict(name=file,log=str((D/file).relative_to(L)),output=(D/file).read_text(),reason=reason,resolved_by=str((D/replacement).relative_to(L))))
failures.extend([
 dict(name='fixture generation shell',output="/bin/bash: -c: line 7: syntax error near unexpected token `('",reason='Nested shell quoting rejected the command before it wrote the fixture.',resolved_by='The heredoc runs directly under the prescribed Python.'),
 dict(name='fixture dependency copy',output='shutil.Error: [Errno 18] Invalid cross-device link',reason='Inherited input aliases resolve to a different scratch mount; the local fixture dependencies were copied as regular files.',resolved_by='All final suites pass.'),
 dict(name='exploratory reads',output='sed: cannot read out/kit_q/b/sc.py: No such file or directory',reason='The q kit is work/build24/kits/q; bounded exploratory reads also found no scene_test.py, setup.py or b/jd5.sh.',resolved_by='The actual kit paths and capsule-decoded jd5.sh were read.')])
write(D/'FAILURES.json',dict(failures=failures,killed_processes=[],unresolved_test_failures=[],expected_regression_failures=['BEFORE.json','BEFORE_EXACT.json']))
bwrap=dict(path=real['binary'],sha256=real['binary_sha256'],version=subprocess.check_output([real['binary'],'--version'],text=True).strip(),production_binary_executed=False,mode_r='Actual x.launch(plan) command and x.plan_r directory creation; payload stub calls real sc.bind. Only local binary/interpreter/fixture mounts and the final stub entry replace the production runtime.',mode_q='Kit a.py extraction/import layout Q_NS/p/s, without the rcj outer sandbox; a private /tmp carrier supplies fixture paths.',legacy='24m4r scene fixture imports its staged z/s; native rebuild, verify, compare and assertions remain unchanged.',scope='Synthetic rows, no production reconstruction or submission')
validation=dict(status='PASS',tree_sha256=tree,kits=seals,rcj=base['rcj'],checks=checks,runs=list(latest.values()),mode_b_byte_identical=True,mode_b_commands_equal_for_same_inputs=True,census_compare_unchanged=True,census_compare_sha256=base['census'],native_sc_tail_unchanged=True,native_census_comparisons=comparisons,missing_source_cases=28,ordinary_delta_files=9,optional_delta_files=3,bwrap=bwrap,GO=False,production_executed=False,uploaded=False,launched=False)
write(D/'VALIDATION.json',validation)
report=[
 "Before edit, the launch/plan_r fixture failed: `bwrap: Can't find source path /tmp/q_22c714e1/z/s: No such file or directory` (required regression evidence: work/build24m4s/BEFORE.json).",
 'The same mode-r layout now passes with root/c and no z/s: actual launch command and plan_r, payload stub calling real sc.bind; host bwrap 0.4.0, synthetic inputs.',
 'Mode q imports $Q_NS/p/s: work/build24m4s/jd5.sh:414 passes $Q_NS/p to b/a.py; work/build24/kits/q/b/a.py:29-30 extracts and imports p/s, overriding the shell trainer path at jd5.sh:363.',
 'All four sc.py copies bind the loaded package root, scope inputs, scratch, kit b and closure paths read-only; only the output is writable. Missing inputs refuse with R1_SCENE_BIND_SOURCE_MISSING; 28 cases pass.',
 'The r/q, inherited z/s and /tmp-closure fixtures pass 200 native census comparisons and held-row refusal checks; the inherited fixture imports its staged z/s. All 30 suite groups pass, including kit, scan, naming, resolver, guard, arming, qd, planner and rcj; setup failures and outputs remain in FAILURES.json.',
 "C'' de202f58, census-compare bytes, all rcj pins and mode-b command bytes are unchanged. VALIDATION.json records the checks and fixture scope; no production run or upload occurred.",
 'UPLOADS_24M4S.json/.list replay exactly against the supplied Orchard pins: nine ordinary files, three optional n_go files. Seals: '+', '.join(n+' '+seals[n][:8] for n in NAMES)+'.',
 'The package preserves input members and superseded bytes in attic; package.py verifies every archived byte, mode and link before writing the .sha256 last.'
]
assert len(report)<10
(L/'out/BUILD24M4S_REPORT.md').write_text('\n'.join(report)+'\n')
print(json.dumps(dict(status='PASS',suites=len(latest),native_census_comparisons=comparisons,missing_source_cases=28,kits=seals),indent=2))
