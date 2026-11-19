"""Check immutable inputs, scan kit q once, and honor the mandatory stop."""
from pathlib import Path
import datetime,hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21f';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import naming21
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
start=read(D/'START.json');tests=read(D/'TESTS.json');coverage=read(D/'COVERAGE.json')
assert tests['successful'] and not tests['errors'] and not tests['failures']
regressions=read(D/'REGRESSION_TESTS.json');regression_coverage=read(D/'REGRESSION_COVERAGE.json')
assert regressions['successful'] and not regressions['errors'] and not regressions['failures']
assert regression_coverage['work/build21/naming21.py']['sha256']==coverage['work/build21/naming21.py']['sha256']
regression_count=sum(name.startswith(('naming_test21c.','naming_test21d.')) for name in regressions['selection'])
for name,record in coverage.items():assert sha(L/name)==record['sha256'],name
kit={str(p.relative_to(K)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in K.rglob('*') if p.is_file()}
assert kit==start['kit_files']
seal=sha(K/'SHA256SUMS.txt');assert seal==start['kit_seal']
sealed_names=set()
for line in (K/'SHA256SUMS.txt').read_text().splitlines():
    digest,name=line.split('  ',1);assert kit[name]['sha256']==digest,name
    sealed_names.add(name)
assert set(kit)==sealed_names|{'BUILD.json','SHA256SUMS.txt'}
for base in start['bases']:
    p=L/base['path'];assert sha(p)==base['sha256'] and p.stat().st_size==base['bytes']
manifest=read(L/'attic/build21f/PACKAGE_MANIFEST.json');tree_count=0
for name,record in manifest['files'].items():
    if name.startswith('work/tree_r1/'):
        p=L/name;assert p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],name
        tree_count+=1
assert read(L/'out/TREE_SEAL.json')==start['tree']
growth=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())-start['workspace_bytes']
assert growth<2_000_000_000
integrity=dict(status='PASS',kit_seal_before=start['kit_seal'],kit_seal_after=seal,kit_files=len(kit),
    kit_bytes_unchanged=True,tree_files_verified=tree_count,tree_seal=start['tree']['tree_sha256'],
    bases_unchanged=start['bases'],workspace_growth_bytes=growth)
write(D/'INTEGRITY.json',integrity)
mutations=read(D/'MUTATIONS.json')
required=[x for x in mutations if 'old' in x]
reviewer=next(x for x in required if x['label']=='reviewer_tuple')
summary='; '.join(f'{Path(name).name}: {v["changed_covered"]}/{v["changed_statements"]}' for name,v in coverage.items())
try:
    result=naming21.scan_decoded(K)
except ValueError as error:
    finding=str(error)
    after={str(p.relative_to(K)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in K.rglob('*') if p.is_file()}
    assert after==kit
    integrity['kit_files_rechecked_after_scan']=True
    integrity['kit_seal_after']=sha(K/'SHA256SUMS.txt')
    assert integrity['kit_seal_after']==seal
    write(D/'INTEGRITY.json',integrity)
    write(D/'SCAN_RESULT.json',dict(status='REFUSE',GO=False,error=finding,kit_seal=seal,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    report=f'''NO-GO: {finding}

The final kit scan refused an unresolved environment operation. GO remains false.
Kit q and the sealed tree are unchanged. The required stop condition applies; no package was produced.

The scanner checks names first, then refuses unresolved environment writes and passed maps.
It follows environment aliases, blocks capability escapes, and rejects unsupported reflection and shell indirection.
The explicit runtime-value allowlist is empty. Computed keys and inherited maps have no exemption.
Scanner files: `work/build21/naming21.py`, `work/build21/environment21f.py`.
The job-side checker has no duplicate environment-scanning logic and was not edited.

Final scanner suite: {tests['tests']} methods passed, with no failures or errors (`work/build21f/TESTS.json`).
Selected naming21c/21d controls: {regression_count} methods passed (`work/build21f/REGRESSION_TESTS.json`).
Every naming21d negative Python case also runs verbatim in naming21f. Literal positive fixtures pass.
The forbidden-name controls execute before the strict gate; their naming21.py hash matches the final file.
All {len(required)} requested full-kit mutations passed the frozen scanner and refused the new scanner
at the injected `b/o.py` location (`work/build21f/MUTATIONS.json`).
The reviewer's tuple mutation returned old PASS with {reviewer['old_checked_strings']:,} checked strings;
the new result is `{reviewer['error']}` (same source).
Changed-statement coverage: {summary} (`work/build21f/COVERAGE.json`).
Uncovered statements remain listed there; this report does not claim complete coverage.

Kit q seal before and after: `{seal}`.
Every kit file matched its starting bytes and SHA-256 (`work/build21f/INTEGRITY.json`).
The sealed-tree files matched the delivery manifest (same source).
Build21e's package and report matched their starting hashes (same source; originals preserved).

Not run after refusal: full naming21c/21d baseline suites, `focused.py`, or packaging.
No kit, tree, upload inventory, or build21e artifact was changed. No upload was attempted.
The report follows the explicit instruction to put the real-kit finding first and stop.
The old/new mutation comparison is retained as requested regression evidence.
'''
    assert len(report.splitlines())<60
    (L/'out/BUILD21F_REPORT.md').write_text(report)
    print(finding,flush=True)
    print('Stopped: out/BUILD21F_REPORT.md',flush=True)
    raise SystemExit(2)
else:
    write(D/'SCAN_RESULT.json',result)
    print('PASS; full suites and packaging still required',flush=True)
