from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build17';P=L.parent/'w17'
B.mkdir(exist_ok=True);(L/'work/tmp').mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for folder in ('student_pilot','launch_r1','tests'):
    for p in (P/'work/tree_r1'/folder).glob('*.py'):
        q=L/'work/tree_r1'/folder/p.name
        if not q.exists() or sha(q)!=sha(p):
            records.append(dict(file=str(q.relative_to(L)),source=str(p),sha256=sha(p)))
            q.write_bytes(p.read_bytes())
for p in (P/'work/build17').iterdir():
    if p.is_file() and p.suffix in ('.py','.sh'):
        (B/p.name).write_bytes(p.read_bytes())
# Reuse the census observations, while rebinding all path-bearing pins below.
for p in (P/'work/build17/inputs').iterdir():
    if p.is_file():(B/'inputs').mkdir(exist_ok=True);(B/'inputs'/p.name).write_bytes(p.read_bytes())
(B/'REUSE.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
