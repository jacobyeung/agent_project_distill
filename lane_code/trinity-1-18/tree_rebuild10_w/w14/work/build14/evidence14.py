from pathlib import Path
import json,hashlib,ast
L=Path(__file__).resolve().parents[2];B=L/'work/build14';T=L/'work/tree_r1'
for name in ['work/build12/proofs/depth_sweep/RESULT.json','work/build13/proofs/final/packet/work/row_families_r5/off_parity_reproduction.json','work/build13/proofs/census/CENSUS.json']:
    v=json.loads((L/name).read_text());print(name,json.dumps(v)[:2400])
print('storage',sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink()))
