python3 - <<'P'
import re
F="/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/metrics_172660.jsonl"
for l in open(F):
    m=re.match(r'\{"step": (\d+)',l); s=int(m.group(1))
    if s in (201,202,210,400):
        for mm in re.finditer(r'"stream_means": \{[^}]*\}',l): print(s,mm.group(0)[:400])
        mm=re.search(r'"wall_seconds": [0-9.e+-]+',l); print(s,mm.group(0))
P
