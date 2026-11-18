from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
root=L/'work/rows_slices/slices_final';root.mkdir(parents=True,exist_ok=True);rows=[]
for name in ('a0_recovery','a0_units','a0_pool_abs_distance_reworded','a0_room'):
    source=L.parent/'work/rows_slices/slices_final'/(name+'.jsonl');target=root/source.name
    assert source.stat().st_size<50_000_000
    h=hashlib.sha256();count=0
    with source.open('rb') as f,target.open('wb') as out:
        for line in f:
            count+=1;assert count<=2000;h.update(line);out.write(line)
    rows.append(dict(source=str(source),target=str(target),count=count,sha256=h.hexdigest()))
(B/'LOCAL_SLICES.json').write_text(json.dumps(rows,indent=2)+'\n')
root=B/'kits'
if root.exists():root.rename(B/'proofs/kits/preflight_source')
print(json.dumps(rows))
