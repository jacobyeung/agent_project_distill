from pathlib import Path
from collections import Counter
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2'
v=json.loads((B/'inherited/CHANGED_COVERAGE.json').read_text())
print('Inherited classes',v['classes'])
for name in ('student_pilot/r1_loader.py','student_pilot/r1_handover.py','student_pilot/carrier_c1_run.py','launch_r1/entry.py'):
    current=hashlib.sha256((L/'work/tree_r1'/name).read_bytes()).hexdigest()
    rows=[r for r in v['statements'] if r['file']==name]
    print(name,Counter(r['sha256']==current for r in rows),Counter(r['classification'] for r in rows))
