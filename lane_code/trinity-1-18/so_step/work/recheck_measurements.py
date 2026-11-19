"""Recompute the delivered statistics from the named, rounded production log."""
import json
from pathlib import Path
import re
import statistics

ROOT=Path(__file__).resolve().parents[1]
source=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/look1.out')
rows=[]
for number,line in enumerate(source.read_text().splitlines(),1):
    match=re.match(r'^S (\d+) (\[.*?\]) (\[.*?\]) ',line)
    if match:
        rows.append((int(match[1]),json.loads(match[2]),json.loads(match[3]),number))
assert len(rows)==200
stable=[r for r in rows if r[0]>=21]
record=json.loads((ROOT/'out/evidence/measurements.json').read_text())
for rank in range(4):
    wall=[r[1][rank] for r in stable]
    data=[r[2][rank] for r in stable]
    for name,values in [('wall',wall),('data',data)]:
        actual=dict(median=statistics.median(values),mean=statistics.mean(values),min=min(values),max=max(values))
        assert actual==record[name][str(rank)],(rank,name,actual)
    print(f'rank{rank}: wall median={statistics.median(wall):.1f}s mean={statistics.mean(wall):.6f}s; data median={statistics.median(data):.2f}s mean={statistics.mean(data):.6f}s')
paired=statistics.median(r[1][0]-r[2][0] for r in stable)
assert paired==record['residual_rank0_median']
print(f'PASS: {len(rows)} measured records; {len(stable)} stable records; lines {stable[0][3]}-{stable[-1][3]}; rank0 paired wall-data median={paired:.1f}s')
