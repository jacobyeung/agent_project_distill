<!-- recovered by seal_plan: transcript=71f94277 line=27570 utc=2026-11-14T02:13:29.319Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; fold -w 1100 -s $C/evalx/events/20261114T0210Z_RESULT_native_footprint_and_transfer_plan.md | head -n 60; echo ====; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json
rows=[json.loads(l) for l in open('$C/orchard_cp2/out/production_169097/project_free.jsonl') if l.strip()]
prev=None
for r in rows:
    t=r['checked_at'][11:16]; f=r['free_bytes']/1e9
    if prev is not None and abs(f-prev)>25: print(r['checked_at'][:16], round(prev,1),'->',round(f,1))
    prev=f
print(len(rows), rows[0]['checked_at'][:16], rows[-1]['checked_at'][:16])
"