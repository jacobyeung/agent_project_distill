from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
N=L;G=N/'w9g';R=Path('/scratch/jjyeung/orch_n30/review_treen1/work/n1c')
O=L/'work/build12/proofs/n1/review_inputs';O.mkdir(parents=True,exist_ok=True)
files=[R/name for name in ('N1_HANDOVER.json','N1_HANDOVER_C.json','N3_VARIANTS.json','N5.json','F1_prod.json','F6.json')]
files.extend(R.glob('H6_h6_*.json'));files.extend(R.glob('F6*.json'))
files.append(N/'work/design/reviewn1c/REVIEW_VERDICT_TREE_N1C.md')
files.append(N/'w9f/out/TREE_FILES.sha256')
receipts=[]
for p in dict.fromkeys(files):
    raw=p.read_bytes();target=O/p.name;target.write_bytes(raw)
    receipts.append(dict(source=str(p),target=str(target.relative_to(L)),sha256=hashlib.sha256(raw).hexdigest()))
prior=G/'work/n1fix/CHANGED_COVERAGE.json'
raw=prior.read_bytes();(B/'inherited/CHANGED_COVERAGE.json').write_bytes(raw)
receipts.append(dict(source=str(prior),sha256=hashlib.sha256(raw).hexdigest()))
old=json.loads(raw)
for name in {r['file'] for r in old['statements']}:
    p=G/'work/tree_r1'/name
    target=B/'original'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
p=B/'coverage_current.py'
s=p.read_text().replace("L.parent/'w9f/work/tree_r1'/name","B/'original'/name")
p.write_text(s)
(O/'INPUT_HASHES.json').write_text(json.dumps(receipts,indent=2))
variants=json.loads((O/'N3_VARIANTS.json').read_text())
print(json.dumps(dict(review_files=len(receipts),unicode_keys=list(variants),n1a=json.loads((O/'N1_HANDOVER_C.json').read_text())),default=str)[:4500])
