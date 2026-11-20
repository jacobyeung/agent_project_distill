from pathlib import Path
import hashlib, json, re, sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4r'
sys.path[:0]=[str(D),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
from common import write, kit, NAMES
import z
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest

base=json.loads((D/'BASELINE.json').read_bytes())
tree=digest(inventory(L/'work/tree_r1c'));assert tree==base['tree']
seals={n:verify(kit(n)) for n in NAMES}
assert {p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}==base['rcj']
runs=json.loads((D/'SUITE_RUNS.json').read_bytes());assert len(runs)==27,len(runs)
failures=[]
for run in runs:
    log=L/run['log'];output=log.read_text()
    if run['returncode']:
        assert run['name']=='native_arm_tests',run
        failures.append(dict(name=run['name'],log=run['log'],output=output,resolved_by='work/build24m4r/native_arm2.log',reason='The adapted suite needed the current SEALS.json summary. Its full rerun passes.'))
        log=D/'native_arm2.log';output=log.read_text();assert 'NATIVE ARM PASS 7 refusals' in output
        run.update(returncode=0,log=str(log.relative_to(L)),replaced_failed_log=failures[-1]['log'])
    run['status']='PASS';run['sha256']=z.sha(log)
    counts=re.findall(r'Ran (\d+) tests?',output)
    if counts:run['tests']=int(counts[-1])
write(D/'FINAL_SUITE_RUNS.json',runs)
checks={}
for rel in ('REAL_BWRAP_TESTS.json','COMMAND_AUDIT.json','RDIFF_MOUNT_TEST.json','DELTA_REPLAY.json','PC_INTEGRATION_TESTS.json','MOUNT_TESTS.json','RCJ_SCAN.json','NATIVE_ARM_TESTS.json'):
    v=json.loads((D/rel).read_bytes());assert v['status']=='PASS',(rel,v)
    checks[rel]=dict(status='PASS',sha256=z.sha(D/rel))
real=json.loads((D/'REAL_BWRAP_TESTS.json').read_bytes())
assert {r['mode'] for r in real['records']}=={'r','q'}
for r in real['records']:
    assert len(r['access']['compare_calls'])==40
    assert all(c['result']=='PASS' for c in r['access']['compare_calls'])
    assert set(r['access']['readonly'].values())=={30}
    assert r['result']['negative_refusal'].endswith('/dev_matches')
    for cmd in r['inner_commands']:
        assert not any(cmd[i:i+3]==['--ro-bind','/','/'] for i in range(len(cmd)))
        assert cmd[cmd.index('--tmpfs')+1]=='/tmp'
        assert ['--remount-ro','/tmp'] in [cmd[i:i+2] for i in range(len(cmd))]
    compare=r['result']['compare_sha256']
    assert compare==z.sha(L/'work/tree_r1c/student_pilot/s1_scene_census.py')

for filename,reason in [
    ('scene1.log','The separate post-rebuild comparison carrier omitted device mounts. The real rebuild itself completed.'),
    ('scene2.log','The post-rebuild comparison carrier lacked the destination mountpoint under its read-only root.'),
    ('scene3.log','The fixture expected stored comparison statuses, but native pool receipts store expected counts and validate them through totals().'),
    ('scene4.log','The mode-r fixture scratch mirror lacked the mountpoint parents that x.py staging normally creates.')]:
    log=D/filename;output=log.read_text();assert 'Traceback' in output
    failures.append(dict(name=filename,log=str(log.relative_to(L)),reason=reason,output=output,resolved_by='work/build24m4r/scene5.log'))
failures.append(dict(name='edit setup',reason='Shell quoting removed literals from the attempted replacement pattern. The assertion stopped before editing any kit.',output='Traceback (most recent call last):\n  File "<stdin>", line 28, in <module>\nAssertionError: q',resolved_by='The replacement ran through a quoted heredoc without nested shell quoting.'))
write(D/'FAILURES.json',dict(failures=failures,killed_processes=[],unresolved_test_failures=[],notes=['Bounded exploratory reads of absent guessed filenames produced ENOENT; no files changed.','PROBE.json records that host bwrap 0.4.0 accepts the original minimal masking command; the Orchard failure was not reproduced with this older binary.']))

pin=z.load(kit('qd')/'k/l.json')['bwrap']
old_manifest=json.loads((L/'work/build24m4q/PACKAGE_MANIFEST.json').read_bytes())['files']
assert not [n for n,v in old_manifest.items() if v.get('sha256')==pin['sha256']]
bwrap=dict(path=real['binary'],sha256=real['binary_sha256'],version='bubblewrap 0.4.0',kit_pin=pin,kit_binary_in_package=False,packaged_bwrap_entries='Symlinks to /usr/bin/bwrap',nested_real_bwrap=True,baseline_fault_reproduced_locally=False,scope='Unmodified sc.bind command and native rebuild/verify/compare on synthetic pool rows. Mode q uses only a private-/tmp carrier; mode r additionally uses x.host_root with explicit scratch, namespace and runtime mounts. Trinity interpreter roots are mounted for the fixture.')
write(D/'VALIDATION.json',dict(status='PASS',scope='Local synthetic fixtures and exact byte replay; no production reconstruction',tree_sha256=tree,kits=seals,rcj=base['rcj'],runs=runs,checks=checks,bwrap=bwrap,mode_b_byte_identical=True,census_compare_unchanged=True,census_compare_sha256=z.sha(L/'work/tree_r1c/student_pilot/s1_scene_census.py'),ordinary_delta_files=9,optional_delta_files=3,GO=False,production_executed=False,uploaded=False,launched=False))

report=[
    "C'' de202f58 and all rcj bytes are unchanged; mode b remains byte-identical.",
    'All four sc.py copies construct a fresh root, keep data inputs read-only and the output writable; pl.py, rb.py, x.py, pc.py, ch.py and rdiff contain no other instance of the covering-root fault in r/q.',
    'Real bwrap passes q and nested mode-r fixtures at /tmp/q_22c714e1/z: each completes 40 native census comparisons, preserves other-stream reports, rejects a leaked held row and passes read-only mount probes.',
    'Kit, decoded scan, naming, resolver, guard, arming, qd, planner and rcj suites pass; native census compare bytes are unchanged. VALIDATION.json records scope; FAILURES.json retains setup failures and their passing replacements.',
    'The host supplies bwrap 0.4.0; the pinned Orchard binary is absent from the package. The host binary accepts the original minimal masking command, so its production failure is not reproduced locally.',
    'UPLOADS_24M4R.json/.list contain exactly nine files against the supplied Orchard pins; the optional n_go overlay contains three. New seals: q e7ac0727, n a7809da0, n_go a41f26b7, qd 221d1782.',
    'The package preserves input members and superseded bytes in attic; every archived byte, mode and link is checked before its checksum is written last. No upload, submission or production run occurred.'
]
assert len(report)<8
(L/'out/BUILD24M4R_REPORT.md').write_text('\n'.join(report)+'\n')
print(json.dumps(dict(status='PASS',suites=len(runs),real_census_comparisons=80,kits=seals,ordinary_delta=9,optional_delta=3),indent=2))
