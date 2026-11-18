from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build12'
print((B/'STATUS.md').read_text())
for rel in ('FINAL_RUNS.json','proofs/n1/suite_tree/progress.json','proofs/n1/suite_tree/generator/progress.json',
            'proofs/n1/suite_tree/legacy/progress.json','proofs/n1/suite_tree/r2/progress.json'):
    p=B/rel
    if p.exists():print(rel,json.dumps(json.loads(p.read_text())))
for rel in ('proofs/n1/suite_tree/generator','proofs/n1/suite_tree/legacy','proofs/n1/suite_tree/r2'):
    p=B/rel/'results.json'
    if p.exists():
        v=json.loads(p.read_text());print(rel,{k:len(v[k]) if isinstance(v[k],list) else v[k] for k in ('tests','passed','failures','errors','skips','complete')})
