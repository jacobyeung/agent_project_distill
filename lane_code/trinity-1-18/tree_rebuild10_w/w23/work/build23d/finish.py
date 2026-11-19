from pathlib import Path
import difflib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23d';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.source_seal import inventory
kit=J.load(D/'KIT.json');scan=J.load(D/'SCAN.json');tests=J.load(D/'GUARD_TESTS.json');legacy=J.load(D/'LEGACY_GUARD_TESTS.json');suites=J.load(D/'SUITES.json');start=J.load(D/'START.json')
assert J.seal(K)==kit['kit_seal']==scan['kit_seal']
assert inventory(L/'work/tree_r1')==start['tree']
assert tests['successful'] and legacy['successful'] and legacy['tests']==9
assert not tests['missing'] and not legacy['missing']
assert len(suites)==5 and all(r['returncode']==0 and r['successful'] for r in suites)
assert scan['status']=='PASS'
assert not any(J.load(D/'REVIEWER_BEFORE.json')['checks'].values())
assert all(J.load(D/'REVIEWER_AFTER.json')['checks'].values())
for group in suites:
 reads=J.load(B/'proofs'/('b23d_'+group['name'])/'READ_INPUTS.json')
 assert not any(p.startswith(str(L/'work/build23b')+'/') for p in reads)
delta=''.join(difflib.unified_diff((L/'attic/build23d/kit.py').read_text().splitlines(True),(B/'kit.py').read_text().splitlines(True),fromfile='build23c/work/build21/kit.py',tofile='build23d/work/build21/kit.py'))
(D/'IMPLEMENTATION.diff').write_text(delta)
for name,v in start['packages'].items():assert (L/name).stat().st_size==v['bytes'] and J.sha(L/name)==v['sha256']
uploads=J.load(L/'out/UPLOADS_NEW_23D.json')
assert len(uploads)==3 and all(set(row)=={'name','bytes','sha256','local_path'} for row in uploads)
for row in J.load(B/'UPLOADS.json')['files']:
 p=Path(row['local_path']);assert p.stat().st_size==row['bytes'] and J.sha(p)==row['sha256']
counts=dict(legacy_guard=legacy['tests'],guard=tests['tests'],regression=sum(x['tests'] for x in suites),groups=suites,reviewer_before_after_cases=2)
counts['total']=counts['guard']+counts['legacy_guard']+counts['regression'];J.write(D/'TEST_COUNTS.json',counts)
J.write(B/'FINAL_KITS.json',dict(status='PASS',GO=False,tree_seal=kit['tree_seal'],kits={'q':J.load(K/'BUILD.json')},decoded_scan=scan,upload_bytes=J.load(B/'UPLOADS.json')['total_bytes'],upload_files=len(J.load(B/'UPLOADS.json')['files']),scope='Kit-only guard diagnostics; source, config, resolver and view unchanged.'))
lines=[
'PASS: both review-23c MUSTs fixed in kit q. Production GO=false.',
'The generator and emitted guard protect all diagnostic reads and conversions; failures print one diagnostic and refuse E42.',
'CUDA_VISIBLE_DEVICES is represented only by a set flag and comma-entry count; device names must fully match [A-Za-z0-9 ._-]{1,64}, otherwise they print as "?".',
'Admission still requires available CUDA, at least one device, known memory and at least 75 GiB (work/build21/kits/q/b/g.py).',
'Both reviewer cases fail before and pass after: missing torch.__version__ produces diagnostic + E42; /tmp/private-project/model/secret-DEMO never reaches raw or screened output (work/build23d/REVIEWER_BEFORE.json, REVIEWER_AFTER.json).',
f"All {legacy['tests']} inherited guard tests pass; {tests['tests']} added tests cover read/import failures, environment summaries and device-name boundaries. Every guard statement line is covered (work/build23d/LEGACY_GUARD_TESTS.json, GUARD_TESTS.json).",
f"Kit/naming/resolver suites: {counts['regression']} passed; {counts['total']} unittest cases total, plus both reviewer comparisons (work/build23d/TEST_COUNTS.json, SUITES.json).",
f"Decoded scan: PASS, {scan['checked_strings']} checked strings (work/build23d/SCAN.json).",
f"Tree seal unchanged: {kit['tree_seal']} (work/build23d/INTEGRITY.json).",
f"Kit q seal: {kit['kit_seal']} (work/build21/kits/q/SHA256SUMS.txt).",
f"Upload diff versus a258d7e7: {len(uploads)} files, {sum(v['bytes'] for v in uploads)} bytes; q/b/g.py, q/SHA256SUMS.txt, q/BUILD.json (out/UPLOADS_NEW_23D.json).",
'The sealed tree, config, resolver identities, admission, legality and DEFERRED boundary are byte-identical. The bwrap view needs no bind change (work/build23d/INTEGRITY.json, VIEW_AUDIT.json).',
'Build-24 instructions and exact generator diff: out/GUARD_PATCH.md and out/GUARD_PATCH.diff; its generator was patched and parsed in memory only (work/build23d/BUILD24_PATCH_CHECK.json).',
'Existing packages remain unchanged. Superseded files and losslessly compressed completed evidence are retained under attic/build23d (work/build23d/START.json, RETAINED.json).',
'Package seal, size, SHA-256 and complete stream verification are recorded externally in work/build23d/DELIVERY.json to avoid circular hashing.',
'Tests use stubbed CUDA; no GPU, production proof or capacity replay ran. work/build23b was not read, written or traversed. No upload or submission occurred.',
'The requested before/after comparison is retained as regression evidence; no other historical narrative is needed.',
]
assert len(lines)<25
(L/'out/BUILD23D_REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(status='PASS',tests=counts['total'],report_lines=len(lines),kit_seal=kit['kit_seal'])))
