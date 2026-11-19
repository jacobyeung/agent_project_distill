"""Verify the final report-bearing archive and retain admission limitations."""
from pathlib import Path
import json,hashlib,sys,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build14';sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify as r1_verify
from launch_r2.build import verify as r2_verify
def read(p):return json.loads((L/p).read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()
seal=read('out/TREE_SEAL.json');files=inventory(L/'work/tree_r1')
assert digest(files)==seal['tree_sha256']
assert sha(L/'out/TREE_FILES.sha256')==seal['inventory_sha256']
assert sha(L/'out/TREE.diff')==seal['diff_sha256']
delivery=read('work/build14/DELIVERY.json');archive=L/delivery['path']
assert sha(archive)==delivery['sha256'] and archive.stat().st_size==delivery['bytes']<150_000_000
frozen=read('work/build14/proofs/final/package/ARCHIVE.json')
assert frozen['sha256']==delivery['sha256'] and frozen['source_sha256']==seal['tree_sha256']
with tarfile.open(archive) as f:
    for name in ('out/BUILD14_REPORT.md','out/DESIGN_RECORD_tree_rebuild_20261115.md','out/TREE_SEAL.json','out/TREE_FILES.sha256','out/TREE.diff'):
        assert f.extractfile(name).read()==(L/name).read_bytes(),name
    archived={m.name[len('work/tree_r1/'):]:hashlib.sha256(f.extractfile(m).read()).hexdigest()
              for m in f.getmembers() if m.isfile() and m.name.startswith('work/tree_r1/')}
    assert archived==files
kits=read('work/build14/KIT_RESULT.json')
for name,v in kits.items():
    assert v.get('source_sha256',v.get('source_seal'))==seal['tree_sha256'] and v['GO'] is False
    assert (r1_verify if name=='r1' else r2_verify)(B/'kits'/name)==v['kit_sha256']
comparison=read('work/build14/SUITE_COMPARISON.json')
assert comparison['r2_failures']==0 and not comparison['fatal']
regressions=[r for r in comparison['failures'] if not r['preexisting']]
assert all('BF16 cached/online gradient' in r['cause'] for r in regressions)
assert read('work/build14/proofs/final/suite_tree/results.json')['complete']
coverage=read('work/build14/CHANGED_COVERAGE.json');assert not read('work/build14/GAPS.json')
assert all(row['sha256']==files[row['file']] for row in coverage['statements'])
real=read('work/build14/proofs/real/RESULT.json')
assert all(v['result']=='P_EXPORT_CONFIG_DIFFERENCE:routing_opener_init' for v in real['real'].values())
size=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
tmp=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
assert size<=1_500_000_000 and tmp<=200_000_000
record=dict(artifact_integrity='PASS',handover_acceptance='BLOCKED: routing_opener_init',GO=False,
    source_seal=seal['tree_sha256'],source_files=len(files),archive=delivery,package_source_and_report_equal=True,
    cpu_gaps=0,r2_failures=0,other_regressions=0,allowed_BF16_regressions=len(regressions),
    storage_bytes=size,tmp_bytes=tmp,parity_rerun=False)
O=B/'proofs/integrity';O.mkdir(exist_ok=True);(O/'RESULT.json').write_text(json.dumps(record,indent=2))
(B/'STATUS.md').write_text('# Build 14 status\n\nSource and CPU qualification are packaged with GO=false. Real A/C handover acceptance remains blocked by routing_opener_init (reset versus keep). The full parity sweep could not be rerun from the authorized inputs.\n\nScale binding, audited effective comparison, milestone producer/reader proofs, population/routing proofs, fresh kits, both suites, coverage and archive integrity are recorded in out/BUILD14_REPORT.md and work/build14/proofs/integrity/RESULT.json.\n')
print(json.dumps(record))
