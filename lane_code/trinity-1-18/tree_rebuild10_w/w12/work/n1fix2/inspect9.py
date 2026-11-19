from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
for name in ('inputs','proofs'):
    root=L/'work/build_n1'/name
    sizes={str(p.relative_to(root)):p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
    print(name,len(sizes),sum(sizes.values()),sorted(sizes.items(),key=lambda x:-x[1])[:4])
    if name=='inputs':
        for rel,size in sizes.items():
            if size>5_000_000:raise ValueError(rel)
            dst=B/name/rel;dst.parent.mkdir(parents=True,exist_ok=True)
            raw=(root/rel).read_bytes().replace(b'work/build_n1',b'work/n1fix2')
            dst.write_bytes(raw)
print('config',json.loads((B/'inputs/config.json').read_text()))
paths=[L.parent/'work/rows_slices/slices_final/a0_recovery.jsonl',
Path('/scratch/jjyeung/orch_n30/rows_r1/out/recovery_v3/rows.jsonl'),
Path('/scratch/jjyeung/orch_n30/rows_r1/out/extent_audit/ROW_AUDIT.jsonl'),
Path('/scratch/jjyeung/orch_n30/rows_r1/out/vehN_units/ROW_AUDIT_units_full.jsonl')]
for p in paths:
    with p.open() as f:row=json.loads(next(f))
    print(str(p),json.dumps(row)[:5500])
for p in (L/'work/tree_r1').rglob('*'):
    if p.is_symlink():print('LINK',p,p.resolve())
