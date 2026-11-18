from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix';O=B/'proofs/review_inputs';O.mkdir(exist_ok=True)
source=L.parent/'work/design/reviewn1'
records=[]
for name in ('PEXPORT.json','ADMIT_SEQ.json','F1_prod.json','F1_noext.json','F6.json','F6_routing.json','R0_V7.json','REVIEW_VERDICT_TREE_N1.md'):
    path=source/name
    if path.is_file():
        raw=path.read_bytes();(O/name).write_bytes(raw)
        records.append(dict(source=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
(O/'PINS.json').write_text(json.dumps(records,indent=2)+'\n')
before=json.loads((B/'BUILD9FIX_FILES.json').read_text())
after={str(p.relative_to(L/'work/tree_r1')):hashlib.sha256(p.read_bytes()).hexdigest()
       for p in (L/'work/tree_r1').rglob('*') if p.is_file()}
changes=[dict(file=name,before=before.get(name),after=after.get(name)) for name in sorted(set(before)|set(after)) if before.get(name)!=after.get(name)]
(B/'DIFF_VS_BUILD9FIX.json').write_text(json.dumps(changes,indent=2)+'\n')
print(json.dumps(changes))
