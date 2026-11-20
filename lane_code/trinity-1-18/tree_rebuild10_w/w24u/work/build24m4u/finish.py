from pathlib import Path
import sys,json,hashlib,re,gzip,ast
L=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path[:0]=[str(L/'out/kit_qd/b'),str(L/'work/tree_r1c')]
import z
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
base=z.load(D/'BASELINE.json');tree=digest(inventory(L/'work/tree_r1c'))
assert tree==base['tree'] and tree.startswith('de202f58')
assert z.sha(L/'work/tree_r1c/student_pilot/s1_scene_census.py')==base['census']
seals={n:verify(L/('out/kit_'+n if n in ('qd','n_go') else 'work/build24/kits/'+n)) for n in base['kits']}
assert seals==base['kits']
rcj={p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}
assert {n for n in rcj if rcj[n]!=base['rcj'][n]}=={'x.py','nd.py'}
runs=[];latest={}
for name in ('SUITE_RUNS.json','RERUN_RUNS.json','RERUN2_RUNS.json','RERUN3_RUNS.json'):
    for r in z.load(D/name):runs.append(r);latest[r['name']]=r
assert len(latest)==35 and not [n for n,v in latest.items() if v['returncode']],latest
for value in latest.values():
    p=L/value['log'];value.update(status='PASS',sha256=z.sha(p))
    found=re.findall(r'Ran (\d+) tests?',p.read_text())
    if found:value['tests']=int(found[-1])
checks={}
for name in ('LIVE_TESTS.json','PUBLICATION_INTEGRATION.json','U_TESTS.json','DELTA_REPLAY.json','REAL_EVIDENCE.json','RCJ_SCAN.json','PC_INTEGRATION_TESTS.json','MOUNT_TESTS.json','RDIFF_MOUNT_TEST.json','BIND_TESTS.json'):
    v=z.load(D/name);assert v['status']=='PASS',(name,v)
    checks[name]=dict(status='PASS',sha256=z.sha(D/name))
comparisons=0
for name in ('REAL_PATH_TESTS.json','REAL_BWRAP_TESTS.json','Q_PATH_TESTS.json'):
    v=z.load(D/name);assert v['status']=='PASS'
    for r in v['records']:
        assert len(r['access']['compare_calls'])==40
        assert all(c['result']=='PASS' for c in r['access']['compare_calls'])
        assert set(r['access']['readonly'].values())=={30}
        assert r['result']['compare_sha256']==base['census']
        comparisons+=40
assert comparisons==200
for name in ('after.log','run.log'):assert 'REAL_PATH_PASS' in (D/name).read_text()
for name in ('new_final.log','rcj_scan_final.log','publication_final.log','deliver_verified.log'):
    text=(D/name).read_text();assert 'PASS' in text or '\nOK\n' in text,name
source=z.load(D/'REAL_INPUTS.json')['files']
for name,v in source.items():
    p=D/'real173725'/name;assert z.sha(p)==v['sha256'] and p.stat().st_size==v['bytes']
assert sum(v['bytes'] for n,v in source.items() if n!='job.log')==8419362
timing=z.load(D/'publication_result/timings.json')
total=sum(p.stat().st_size for p in (D/'publication_result').rglob('*') if p.is_file())
assert total==timing['aggregate_publication_bytes']<5_000_000
na=json.loads(gzip.decompress((D/'observations/na.json.gz').read_bytes()))
assert na['count']==4797 and na['unattributed']==0 and len(na['rows'])==4797
nd=z.load(D/'observations/nd.json');assert nd['metadata_classes']['ordinal']['rows']==39892
assert sum(v['rows'] is None for v in nd['metadata_classes'].values())==3
rt=z.load(D/'observations/routing_types.json');assert rt['status']=='PASS' and rt['total_rows']==43101
ext=z.load(D/'EXTENT_EVIDENCE.json');assert ext['normalized_missing']==2368 and ext['exact_missing']==4460
assert z.load(D/'P_INVENTORY.json')['tree_sha256'].startswith('b83a8a35')
for suffix,count in (('',14),('_CANDIDATE',2),('_GO',4)):
    v=z.load(L/'out'/('UPLOADS_24M4U'+suffix+'.json'));assert len(v['files'])==count
    assert (L/'out'/('UPLOADS_24M4U'+suffix+'.list')).read_text()==''.join(r['name']+'\n' for r in v['files'])
    for row in v['files']:
        p=L/row['relative_path'];assert z.sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
failures=[dict(r,output=(L/r['log']).read_text(),resolved_by=latest[r['name']]['log']) for r in runs if r['returncode']]
failures.extend(z.load(D/'FINISH_SETUP_FAILURES.json'))
failures.append(dict(name='initial workspace listing',output="FileNotFoundError: [Errno 2] No such file or directory: 'rcj'",resolution='The extracted helper directory is out/rcj.'))
failures.append(dict(name='named optional input probes',output='Named paths work/build24m4h/inputs.json, student_pilot/r1_build.py and student_pilot/r1_slices.py were absent; RERUN2_RUNS.json was read before its first completed suite.',resolution='No required input was inferred from these missing paths. The authentic extent receipt was located through the preserved upload manifest.'))
write(D/'FAILURES.json',dict(failures=failures,killed_processes=[],unresolved_test_failures=[],
    unresolved_production=['The original hidden nd exception subtype is irrecoverable from the supplied files.','The actual SQL stores needed for three metadata classes and exact helper replay were not supplied.','The frozen native extent reader has no configurable stream scope and the audit carry lacks complete coverage.']))
write(D/'FINAL_SUITE_RUNS.json',list(latest.values()))
validation=dict(status='QUALIFIED',checks_status='PASS',tree_sha256=tree,kits=seals,rcj=rcj,
    checks=checks,runs=list(latest.values()),inherited_suite_groups=34,new_tests=7,
    mode_b_byte_identical=True,mode_b_commands_identical=True,census_compare_unchanged=True,native_census_comparisons=comparisons,
    missing_source_cases=28,original_publication_bytes=8419362,replayed_publication_bytes=total,
    absent_rows=4797,absent_unattributed=0,routing_types='PASS',metadata_classes_counted=['ordinal'],
    extent_candidate='BLOCKED; no config-only option',exact_original_helper_fail_before_after=False,
    production_helper_cause='Execution outside staged runtime addressed; original exception subtype remains unproved.',
    ordinary_delta_files=14,candidate_delta_files=2,optional_delta_files=4,
    GO=False,config_delta=False,production_executed=False,uploaded=False,launched=False)
write(D/'VALIDATION.json',validation)
report=[
    'QUALIFIED: publication and helper diagnostics are repaired; the original hidden helper exceptions, three metadata classes and routing extent admission still need production evidence or a changed constraint.',
    f'Real 173725 publication replay is {total:,} bytes, below 5 MB; priority evidence stays, successful processor token arrays become hashes/counts, sample classes remain represented, and omitted files retain full hashes/sizes. Budget pressure does not fail the job.',
    'task_a and nsample report the same child failure; routing_types is the second child. Both now use the staged runtime/namespace and publish full screened exception lines/tracebacks. The discarded original subtype cannot be recovered or honestly reproduced from the supplied artifacts.',
    'Real-input na.json.gz attributes all 4,797 absences: 4,768 merged-dev and 29 listed rows. routing_types.json passes all five P quota checks; the largest absolute deviation is 6.615%.',
    'Real-input nd.json counts 39,892 ordinal changes over all 43,101 matched rows. The other three classes remain explicitly unavailable because full SQL row/target text was not published; no substitute databases were constructed.',
    'EXTENT_24M4U.md proves P had no extent reader, C″ always checks required rows, and no stream-scope config exists. The authentic audit misses 2,368 pool QIDs even after diagnostic normalization; carry is impossible. No config candidate or new kit seal was fabricated.',
    'All 34 inherited suite groups, seven new tests, seven live-publication cases and the outside-publisher integration pass. The 24m4t real plan/run fixtures pass; 200 native census comparisons and 28 missing-source refusals pass. FAILURES.json preserves failed-test output and its resolution.',
    'C″ remains de202f58; census comparison bytes, mode-b commands/publication bytes, all kit seals, ch.py, pc.py, f.json, ps.py, rcj.sh and P_SAMPLE_I remain unchanged.',
    'UPLOADS_24M4U.json/.list replay exactly against the reviewed overlay: 14 files. CANDIDATE replay against c_291c6f58 contains only rcj/x.py and rcj/nd.py; optional GO contains four inherited kit files. GO is false; no upload, production rerun, submission or production arming occurred.',
    'The authentic log and all published files are preserved in work/build24m4u/real173725. Exact production helper fail-before/pass-after remains unmet; the injected subtype regression is labeled separately in HELPER_DIAGNOSIS.json.',
    'The package preserves inherited and superseded bytes, verifies every archived byte/mode/link, and writes its .sha256 last. VALIDATION.json distinguishes passing local checks from unresolved production requirements.'
]
assert len(report)<14 and len((L/'out/EXTENT_24M4U.md').read_text().splitlines())<25
(L/'out/BUILD24M4U_REPORT.md').write_text('\n'.join(report)+'\n')
print(json.dumps(dict(status='QUALIFIED',checks='PASS',suite_groups=len(latest),publication_bytes=total,rcj=rcj),indent=2))
