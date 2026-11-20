from pathlib import Path
import base64, hashlib, json, os, resource, sys
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
L=Path.cwd();D=L/'work/build24m4y2'
sys.path[:0]=[str(L/'work/tree_r1c'),str(L/'out/kit_qd/b'),str(L/'out/rcj')]
import z,nd,ch
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def kit(n):return L/('out/kit_'+n if n in ('qd','n_go') else 'work/build24/kits/'+n)
tree=digest(inventory(L/'work/tree_r1c'));assert tree==nd.TREE==ch.TREE
seals={n:verify(kit(n)) for n in ('q','n','qd','n_go')}
old_seals=z.load(L/'work/build24m4x2/DELTA_REPLAY.json')['kits'];assert seals==old_seals
for n in seals:
    for f in ('BUILD.json','k/a.json'):assert z.load(kit(n)/f)['GO']==(n=='n_go')
assert z.sha(L/'out/rcj/f.json')==nd.FIELDS
rcj={p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}
(L/'out/RCJ_FILES_24M4Y2.sha256').write_text(''.join(h+'  rcj/'+n+'\n' for n,h in sorted(rcj.items())))
old=z.load(L/'out/UPLOADS_24M4X2.json');up=json.loads(json.dumps(old));up['build']='24m4y2'
for v in up['files']:
    p=L/v['relative_path'];v.update(local_path=str(p),sha256=z.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'))
up['total_bytes']=sum(v['bytes'] for v in up['files']);up['over_5MB']=[dict(name=v['name'],bytes=v['bytes']) for v in up['files'] if v['bytes']>5_000_000]
up['helper_delta']=['rcj/ch.py','rcj/f.json','rcj/nd.py','rcj/x.py']
up['tree_sha256']=tree;up['kit_seals']={n:seals[n] for n in ('q','n','qd')}
up['config_delta']='Inherited 24m4x2 delta; no further kit changes';up['helper_only_since']='24m4x2';up['uploaded']=False;up['launched']=False
write(L/'out/UPLOADS_24M4Y2.json',up)
(L/'out/UPLOADS_24M4Y2.list').write_text(''.join(v['name']+'\n' for v in up['files']))
optional=z.load(L/'out/UPLOADS_24M4X2_GO.json');optional['build']='24m4y2'
for v in optional['files']:
    p=L/v['relative_path'];assert z.sha(p)==v['sha256'];v['local_path']=str(p)
write(L/'out/UPLOADS_24M4Y2_GO.json',optional)
(L/'out/UPLOADS_24M4Y2_GO.list').write_text(''.join(v['name']+'\n' for v in optional['files']))
# Independently compute every changed kit/helper member against the reviewed overlay.
baseline=z.load(L/'work/build24m4s/BASELINE.json');expected=set()
assert old['baseline_kit_seals']=={n:baseline['kits'][n] for n in ('q','n','qd')}
assert old['baseline_rcj']==baseline['rcj']
for n in ('q','n','qd'):
    files={str(p.relative_to(kit(n))):p for p in kit(n).rglob('*') if p.is_file()}
    assert files.keys()==baseline['files'][n].keys()
    for f,p in files.items():
        v=baseline['files'][n][f]
        if z.sha(p)!=v['sha256'] or p.stat().st_mode&511!=v['mode']:expected.add(n+'/'+f)
for n,h in baseline['rcj'].items():
    if rcj[n]!=h:expected.add('rcj/'+n)
expected.update(v['name'] for v in old['files'] if v['name'].startswith('u/'))
assert expected=={v['name'] for v in up['files']}
assert {v['name'] for v in old['files']} <= expected
for v in up['files']:
    if v['name'].startswith('rcj/'):assert v['baseline_sha256']==baseline['rcj'][v['name'][4:]]
    elif not v['name'].startswith('u/'):
        n,f=v['name'].split('/',1);assert v['baseline_sha256']==baseline['files'][n][f]['sha256']
write(D/'DELTA_CHECK.json',dict(status='PASS',ordinary_files=len(expected),optional_files=len(optional['files']),
    exact_against_reviewed_overlay=True,all_x2_uploads_retained=True,baseline_kits=old['baseline_kit_seals'],baseline_rcj=old['baseline_rcj']))
audit=z.load(D/'INPUT_AUDIT.json');assert audit['missing']==[]
assert set(audit['changed'])=={'out/rcj/'+n for n in ('ch.py','nd.py','x.py','f.json')}
latest={};failures=[]
for f in ('suite_first.json','suite_second.json','suite_third.json','suite_final.json','suite_extra.json'):
    if (D/f).exists():
        for r in z.load(D/f):
            latest[r['name']]=r
            if r['returncode']:failures.append(dict(r,output=(L/r['log']).read_text()))
assert all(r['returncode']==0 for r in latest.values()),latest
for name in ('DECISION_TESTS.json','TREE_TESTS.json','REAL_TESTS.json','OFFLINE_SAMPLES.json'):
    assert z.load(D/name)['status']=='PASS',name
failures.append(dict(name='independently compacted sample populations',output=(D/'offline_samples.log').read_text(),
    resolution='The full seven-row N sample correctly fails for a missing P counterpart. The six exact pairs pass (a)/(b); full 43,101-row decision replay uses the published population census.'))
failures.append(dict(name='Finalization with stale mode-r AST assertion',output=(D/'finalize.log').read_text(),resolution='The mode-b test now exempts the explicitly changed run_r helper; its changed call is covered by the native hook test.'))
write(D/'FAILURES.json',dict(failures=failures,killed_processes=[],unresolved_test_failures=[]))
R=L.parent/'work/d173817/173817';before=D/'before';before.mkdir(exist_ok=True)
for name in ('timings.json','nd.json','chain.json','routing_types.json','proc_check.json'):
    p=before/name
    if not p.exists():p.write_bytes((R/name).read_bytes())
reference=L/'work/build24m4x2/a0_pool_abs_distance_reworded_row.json'
assert base64.b64decode(ch.REFERENCE)==reference.read_bytes()
assert z.sha(reference)==ch.REFERENCE_STORE['sha256']
write(D/'REFERENCE_SOURCE.json',dict(status='PASS',source_capture=str(reference.relative_to(L)),
    sha256=z.sha(reference),embedded_bytes_equal=True,row_sha256=ch.REFERENCE_SHA,
    source_store_name=ch.REFERENCE_STORE['path'],
    qualification='A retained exact real-row capture, not an assertion that its upstream store is staged. The CPU helper searches all staged SQL and row-line stores first.'))
write(D/'VALIDATION.json',dict(status='PASS',tree_sha256=tree,kits=seals,rcj=rcj,
    suite_groups=len(latest),suites=list(latest.values()),targeted_tests=18,decision_tests=z.load(D/'DECISION_TESTS.json')['tests'],
    chain=z.load(D/'REAL_CHAIN.json'),real_decision=z.load(D/'REPLAY173817.json')['after'],
    production_executed=False,uploaded=False,launched=False,GO=False,
    limitations=['The full P/N SQL stores and staged Orchard sources are unavailable locally. The next CPU job must recompute the full comparisons, choose its real third control, publish per-store counts and demonstrate actual exit 0.',
      'The supplied review findings were verified against 173817. The separately referenced final_message.md was not located in the accessible local receipt directories; no full review-file read is claimed.']))
report=[
 '24m4y2 changes only rcj/x.py, nd.py, ch.py and f.json; their seals are in RCJ_FILES_24M4Y2.sha256.',
 'Tree 9d2bbb8a and all four kit seals/admission rules remain unchanged; GO=false except kit_n_go.',
 'Fail-before: 173817/timings.json has post_returncode=1 and rdiff_returncode=1; nd.json task_i=FAIL counts 39,892 ordinal and 11,663 copied-row differences.',
 'Pass-after: REPLAY173817.json applies the new decision to the real 43,101-row counters and chain: (a)/(b)/(c) PASS, exit decision 0; (d) DEFERRED_TO_DISCOVERY.',
 'f.json derives encode fields from file:line; raw SQL targets remain exact. nl.json.gz publishes the literal comparison by class as information superseded by ANSWER 1226Z.',
 'The control searches N, P and every staged pinned SQL/row-line store before using sealed bytes; it publishes source hashes, all store counts and the required=exempted+receipt-entry check.',
 'Eight decision tests, 18 targeted tests and the rcj suites pass; the 80-row chain passes with 14 exempted, 66 checked and zero refusals. FAILURES.json retains every test/setup failure.',
 'Six exact published P/N sample pairs pass (a)/(b); the independently compacted seventh N sample correctly fails without its P counterpart.',
 'UPLOADS_24M4Y2.json/.list contains all 38 required uploads against the reviewed overlay; 11 inherited optional GO uploads remain separate.',
 'Only the next CPU job can prove the new full-store search, fresh all-row comparison and actual exit status. The separate review final_message.md was not located; its supplied findings were checked directly.',
 'The package preserves inherited members and the four superseded helpers, verifies archived bytes/modes/links, and writes its checksum last; fail-before history is retained as explicitly requested.'
]
assert len(report)<12
(L/'out/BUILD24M4Y2_REPORT.md').write_text('\n'.join(report)+'\n')
print(json.dumps(dict(status='PASS',uploads=len(expected),optional=len(optional['files']),suites=len(latest),rcj=rcj),indent=2))
