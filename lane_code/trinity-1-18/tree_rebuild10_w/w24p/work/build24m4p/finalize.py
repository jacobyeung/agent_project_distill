from pathlib import Path
import sys, json, os
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import L, D, T, z, kit, write
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify

base = json.loads((D/'BASELINE.json').read_bytes())
prior = json.loads((L/'out/UPLOADS_24M4O3.json').read_bytes())
older = json.loads((L/'work/build24m4n/BASELINE.json').read_bytes())
tree = digest(inventory(T))
assert tree == base['tree']
seals = {n: verify(kit(n)) for n in base['kits']}
assert seals == json.loads((D/'SEALS.json').read_bytes())

def files(root):
    return {str(p.relative_to(root)): dict(sha256=z.sha(p), bytes=p.stat().st_size,
            mode=p.stat().st_mode & 511) for p in root.rglob('*') if p.is_file()}

new = {n: files(kit(n)) for n in seals}
for n in seals:
    assert set(new[n]) == set(base['files'][n])
    changed = {p for p in new[n] if new[n][p] != base['files'][n][p]}
    assert changed == {'BUILD.json', 'SHA256SUMS.txt', 'b/pl.py', 'b/sc.py'}, (n, changed)
rcj = {p.name: z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}
assert set(rcj)-set(base['rcj']) == {'f.json'}
assert {n for n in base['rcj'] if rcj[n] != base['rcj'][n]} == {'x.py', 'nd.py'}
for n in ('rcj.sh', 'ps.py', 'P_SAMPLE_I.json'):
    assert rcj[n] == prior['baseline_rcj'][n]

original = {n: (older['files']['qd'] if n == 'qd' else base['files'][n]) for n in ('q','n','qd')}
rows = []
def entry(name, path, old):
    return dict(name=name, relative_path=str(path.relative_to(L)), local_path=str(path),
        action='replace' if old else 'add', baseline_sha256=old,
        sha256=z.sha(path), bytes=path.stat().st_size, mode=format(path.stat().st_mode & 511, '04o'),
        transfer='local-upload')
for n, old in original.items():
    assert not set(old)-set(new[n])
    for name, v in new[n].items():
        if old.get(name) != v:
            rows.append(entry(n+'/'+name, kit(n)/name, old.get(name, {}).get('sha256')))
for name, h in rcj.items():
    if prior['baseline_rcj'].get(name) != h:
        rows.append(entry('rcj/'+name, L/'out/rcj'/name, prior['baseline_rcj'].get(name)))
rows.sort(key=lambda r:r['name'])
assert len(rows) == 18, [r['name'] for r in rows]
up = dict(schema='cpu-publication-delta-v1', build='24m4p', baseline='Stated Orchard pins; includes 24m4o and 24m4o3 changes',
    baseline_kit_seals=prior['baseline_kit_seals'], baseline_rcj=prior['baseline_rcj'],
    tree_sha256=tree, kit_seals={n:seals[n] for n in ('q','n','qd')},
    sealed_variant=dict(kit_sha256=seals['n_go'], manifest='out/UPLOADS_24M4P_GO.json', applied=False),
    files=rows, total_files=len(rows), total_bytes=sum(r['bytes'] for r in rows),
    GO=False, uploaded=False, launched=False, config_delta=False)
write(L/'out/UPLOADS_24M4P.json', up)
(L/'out/UPLOADS_24M4P.list').write_text(''.join(r['name']+'\n' for r in rows))

# The existing optional variant remains a separate overlay on the new N kit.
go_rows = [entry('n/'+name, kit('n_go')/name, new['n'].get(name, {}).get('sha256'))
           for name,v in new['n_go'].items() if new['n'].get(name) != v]
go_rows.sort(key=lambda r:r['name'])
assert {r['name'] for r in go_rows} == {'n/BUILD.json','n/SHA256SUMS.txt','n/k/a.json'}
go = dict(schema='build24m4p-go-diff-v1', base_kit_seal=seals['n'], kit_seal=seals['n_go'],
    original_variant_seal=base['kits']['n_go'], files=go_rows, total_files=len(go_rows),
    total_bytes=sum(r['bytes'] for r in go_rows), uploaded=False, applied=False,
    authority='Preserves the delivered optional variant; this inventory does not authorize or perform arming.')
write(L/'out/UPLOADS_24M4P_GO.json', go)
(L/'out/UPLOADS_24M4P_GO.list').write_text(''.join(r['name']+'\n' for r in go_rows))

def original_path(relative, h):
    candidates=[L/relative]+[L/'attic'/b/relative for b in ('build24m4p','build24m4n','build24m4o','build24m4o3')]
    for p in candidates:
        if p.is_file() and z.sha(p)==h: return p
    raise ValueError('Missing baseline bytes: '+relative)

replay=D/'replay'; replay.mkdir()
def copy(p, q, mode):
    q.parent.mkdir(parents=True, exist_ok=True)
    with q.open('xb') as f: f.write(p.read_bytes())
    q.chmod(mode)

for n, old in original.items():
    for name, v in old.items():
        relative=str((kit(n)/name).relative_to(L))
        copy(original_path(relative,v['sha256']),replay/n/name,v['mode'])
    assert verify(replay/n)==prior['baseline_kit_seals'][n]
for name,h in prior['baseline_rcj'].items():
    p=original_path('out/rcj/'+name,h)
    copy(p,replay/'rcj'/name,p.stat().st_mode & 511)
for row in rows:
    q=replay/row['name']
    if q.exists():
        a=L/'attic/build24m4p/replay'/row['name'];a.parent.mkdir(parents=True,exist_ok=True);q.rename(a)
    copy(L/row['relative_path'],q,int(row['mode'],8))
for n in ('q','n','qd'):
    assert verify(replay/n)==seals[n]
    assert files(replay/n)==new[n]
assert files(replay/'rcj')==files(L/'out/rcj')
for name,v in new['n'].items(): copy(replay/'n'/name,replay/'n_go'/name,v['mode'])
for row in go_rows:
    name=row['name'][2:];q=replay/'n_go'/name
    a=L/'attic/build24m4p/replay/n_go'/name;a.parent.mkdir(parents=True,exist_ok=True);q.rename(a)
    copy(L/row['relative_path'],q,int(row['mode'],8))
assert verify(replay/'n_go')==seals['n_go']
assert files(replay/'n_go')==new['n_go']
write(D/'DELTA_REPLAY.json',dict(status='PASS',files=len(rows),variant_files=len(go_rows),
    exact_bytes_modes=True,baseline=prior['baseline_rcj'],rcj=rcj,kits=seals))

run_files=[L/'attic/build24m4p/suites1/SUITE_RUNS.json',L/'attic/build24m4p/suites2_runs.json',
           L/'attic/build24m4p/suites3_runs.json',D/'SUITE_RUNS.json']
runs=[r for p in run_files for r in json.loads(p.read_bytes())]
latest={r['name']:r for r in runs}
assert all(r['returncode']==0 for r in latest.values())
latest['publication_tests']=dict(name='publication_tests',returncode=0,log=str(D/'publication_final.log'))
for name,log in [('planner_tests','planner3.log'),('evidence_test','evidence3.log')]:
    latest[name]=dict(name=name,returncode=0,log=str(D/log))
checks={}
for name in ('NEW_TESTS','PUBLICATION_TESTS','PLANNER_TESTS','ABSENCE_EVIDENCE_TEST','CENSUS_TEST',
             'RCJ_SCAN','ARM_TESTS','REVIEW_AUTH_TESTS','ARM_COVERAGE','ARM_MISSING_DB_TEST',
             'ARM_NEGATIVES','NATIVE_ARM_TESTS','QD_STEP1_TESTS','SCAN_q','SCAN_n','SCAN_n_go','SCAN_qd'):
    v=json.loads((D/(name+'.json')).read_bytes());assert v['status']=='PASS';checks[name]=v
for name in ('KIT_TESTS','NAMING_TESTS','RESOLVER_TESTS'):
    v=json.loads((D/(name+'.json')).read_bytes());assert v['successful'];checks[name]=v
for path in ('contract/RCJ_CONTRACT_TESTS.json','sample/SAMPLE_TESTS.json'):
    v=json.loads((D/path).read_bytes());assert v['status']=='PASS';checks[path]=dict(status='PASS',path=str((D/path).relative_to(L)))

failed=[]
for r in runs:
    if r['returncode']:
        p=Path(r['log']);failed.append(dict(name=r['name'],returncode=r['returncode'],
            log=str(p.relative_to(L)),output_tail=p.read_text(errors='replace')[-8000:],resolved_by=latest[r['name']]['log']))
for log, successor in [('planner1.log','planner3.log'),('planner2.log','planner3.log'),
                        ('publication1.log','publication_final.log'),('rcj_scan1.log','rcj_scan2.log'),
                        ('evidence1.log','evidence3.log'),('evidence2.log','evidence3.log')]:
    p=D/log
    failed.append(dict(name=log,log=str(p.relative_to(L)),output_tail=p.read_text(errors='replace')[-8000:],
        resolved_by=str((D/successor).relative_to(L))))
write(D/'FAILURES.json',dict(failures=failed,killed_processes=[],unresolved_test_failures=[],
    setup_notes=['Missing delivered fixture modules, pins and fixture directories were supplied from this workspace.',
        'The rcj scanner refused dynamic keyword expansion; the implementation uses an explicit dictionary update.',
        'Bounded exploratory reads of absent guessed filenames returned No such file or directory; no files changed.']))

evidence=L/'work/build24m4o/evidence'
# The original evidence sizes are recorded explicitly; no production database was reconstructed.
budget=dict(requested_total_bytes_less_than=5_000_000,status='UNMET',
    observed_existing=dict(rd0_gzip=4_974_929,rd0_summary=4_489,p_sample=1_739_398),
    existing_minimum_bytes=6_718_816,helper_outputs_and_tails_limit=5_000_000,
    behavior='Preserves existing outputs, limits helper artifacts, and reports aggregate bytes and FAIL in timings when total exceeds the cap.')
assert sum(budget['observed_existing'].values())==budget['existing_minimum_bytes']
write(D/'PUBLICATION_LIMIT.json',budget)
qualifications=[
    'The literal total-publication cap is unmet: the supplied unchanged rd0 and P sample already total 6718816 bytes. New helper artifacts and tails remain below 5000000 bytes.',
    'No full production N database is supplied; no production-wide content verdict or camera-type table was run locally.',
    'C reader dependencies promote the proposed metadata classes to content under the sampling exception. The 39892 known changed ordinals cannot pass criterion (i).',
    'The supplied source totals imply acceptable distance and units rates but do not determine the three camera rates.',
    'Planner fixtures mock the P producer and scene child boundaries; the native merged-scene rebuild and census run separately on fixtures.'
]
validation=dict(status='PASS',status_scope='Local validation only',requirements_status='QUALIFIED',
    tree_sha256=tree,kits=seals,rcj=rcj,checks=checks,suites=list(latest.values()),
    mode_b_byte_identical=True,build_refusal_status_preserved=True,qd_stops_before_training=True,
    publication_limit=budget,production_executed=False,uploaded=False,launched=False,GO=False,
    qualifications=qualifications)
write(D/'VALIDATION.json',validation)
lines=[
    "C'' de202f58; kit seals q 098987e2, n a4554161, n_go f62a1c8a, qd 022c1c7a.",
    'The r/q planners build P first when needed, rebuild the pool under merged dev a1869ae2, and bind that selection; native compare and all other stream expectations remain unchanged.',
    'TASKA_FIELDS_24M4P.md and rcj/f.json close the C reader dependencies: ordinal lookup and recursive admission reach sampling, so the four candidate metadata classes receive no unconditional exemption.',
    'The CPU publisher compares every matched row field and SQL target, counts all four classes, attributes every absent P row, and records Task A and routing-type statuses without changing build/refusal behavior; rd0 is unchanged.',
    '173680 evidence attributes 4,768 absences to merged dev scenes and 29 to a pinned list; U_Faithful keeps 718. Its 39,892 changed ordinals fail criterion (i) under the sampling exception.',
    'At 43,101 rows, absolute_distance is 16.252059/step (-0.5382%) and units is 1.066147 (+6.6147%); camera-type counts are unavailable, so overall rate status is UNDETERMINED. No config delta was built.',
    'Kit, scan, naming, resolver, guard, arming, qd and rcj suites pass, including 11 new fixtures, 10 publication fixtures, r/q planner checks and exact delta replay; mode b bytes match and qd stops before training.',
    'UNMET: the literal total-publication limit is incompatible with preserving existing rd0 and P sample (6,718,816 bytes already); helper artifacts/tails are bounded below 5 MB, and timings records aggregate bytes and FAIL.',
    'UPLOADS_24M4P.json/.list contain 18 files against the stated Orchard pins, including 24m4o/24m4o3 changes; the separately sealed optional n_go overlay has three files and was not applied.',
    'No production reconstruction, full-DB comparison, upload, submission, training or arming ran. VALIDATION.json states fixture scope; FAILURES.json retains failed test outputs and their successful replacements.',
    'The verified package includes superseded bytes in attic; DELIVERY_24M4P.json and PACKAGE_CHECK.json record its members, seals and checksum.'
]
assert len(lines)<12
(L/'out/BUILD24M4P_REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(status='PASS',requirements_status='QUALIFIED',upload_files=len(rows),
    upload_bytes=up['total_bytes'],variant_files=len(go_rows),kits=seals),indent=2))
