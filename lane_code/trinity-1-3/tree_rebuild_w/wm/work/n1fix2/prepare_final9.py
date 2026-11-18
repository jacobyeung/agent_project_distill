from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';N=L
p=N/'work/build_n1/proofs/audit/INFERENCE_COMPONENTS.json';out=L/'work/merge11/proofs/n1/audit';out.mkdir(exist_ok=True)
(out/p.name).write_bytes(p.read_bytes())
for name in ('CARRIED_BLOCKERS.json','CHANGED_COVERAGE.json','N1_CHANGED_COVERAGE.json','INPUT_BINDINGS.json'):
    p=N/'work/build_n1'/name
    if p.exists():(B/('N1_'+name)).write_bytes(p.read_bytes())
p=B/'make_delivery.py';text=p.read_text().replace('tree_rebuild_bn1_','tree_rebuild_b9f_')
text=text.replace("'work/n1fix2/inputs',", "'work/n1fix2/inputs','work/build_n1/inputs','work/rows_slices/slices_final',")
p.write_text(text)
inventory=[]
for root in (L/'work/tree_r1',L/'work/base/tree_b01ce449',L/'fixtures',L/'work/contracts_r6'):
    inventory.append(dict(path=str(root),bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())))
(B/'DELIVERY_PLAN.json').write_text(json.dumps(inventory,indent=2)+'\n')
print(json.dumps(inventory))
