from pathlib import Path
import json,hashlib,collections
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1'
v=json.loads((B/'CHANGED_COVERAGE.json').read_text());print(v['classes'])
old=json.loads((B/'inherited/CHANGED_COVERAGE.json').read_text())
for name,rows in __import__('itertools').groupby(sorted(v['statements'],key=lambda r:r['file']),key=lambda r:r['file']):
    gaps=[r for r in rows if r['classification']=='CPU-reachable unresolved']
    if gaps:
        previous=[r for r in old['statements'] if r['file']==name]
        print(name,[(r['line'],r['function']) for r in gaps],dict(previous=len(previous),matching_hash=any(r['sha256']==hashlib.sha256((T/name).read_bytes()).hexdigest() for r in previous)))
