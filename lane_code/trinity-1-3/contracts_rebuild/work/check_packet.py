from pathlib import Path
import hashlib
import json

L=Path(__file__).resolve().parents[1]
names=['PATCH_geometry.diff','PATCH_candidates.diff','PATCH_box.diff','PATCH_MANIFEST.json',
       'TEST_RUN_B1.log','CHANGED_LINE_COVERAGE_B1.md','CONTRACTS_REPORT.md',
       'DESIGN_RECORD_contracts_rebuild_20261115.md','CPU_PROOF_B1.json','BUILD1_SUMMARY.md']
manifest=json.loads((L/'out/PATCH_MANIFEST.json').read_text())
for name,entry in manifest['files'].items():
    for root in ('work/src','work/trees/patched','work/trees/apply_ordered_final_b1'):
        assert hashlib.sha256((L/root/name).read_bytes()).hexdigest()==entry['patched_sha256'],(root,name)
index={}
for name in names:
    path=L/'out'/name
    size=path.stat().st_size
    assert 0<size<20_000_000,name
    index[name]=dict(path=str(path),bytes=size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
lane_bytes=sum(p.stat().st_size for p in L.rglob('*') if p.is_file())
assert lane_bytes<2_000_000_000
index['lane_check']=dict(bytes_before_index=lane_bytes,limit_bytes=2_000_000_000)
(L/'out/PACKET_INDEX.json').write_text(json.dumps(index,indent=2)+'\n')
print('All requested deliverables exist; source, tested tree and applied tree hashes match; lane is below the disk limit.')
