from pathlib import Path
import ast,json
L=Path(__file__).resolve().parents[2];B=L/'work/build16'
for name in ('report16.py','mode_test16.py','qualify16.py'):
    ast.parse((B/name).read_text());print(name,'syntax valid')
for name in ('proofs/final/suite_tree/r2/results.json','proofs/operator/P_PRODUCER_EQUALITY.json','proofs/operator/STAGING.json'):
    p=B/name
    if p.exists():
        x=json.loads(p.read_text());print(name,[(k,type(v).__name__) for k,v in x.items()] if isinstance(x,dict) else dict(entries=len(x),first=x[0]))
print('seal',json.loads((L/'out/TREE_SEAL.json').read_text())['tree_sha256'])
