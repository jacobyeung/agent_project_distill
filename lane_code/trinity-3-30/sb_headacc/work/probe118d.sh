PY=/scratch/jjyeung/envs/planner_local_v1/bin/python
$PY - <<'PYEOF'
import json, collections, os
Q='/scratch/jjyeung/orch_n30/b10_reserve/out/qsets/R0_QUESTIONS_dev_f32.jsonl'
rows=[json.loads(l) for l in open(Q)]
print('R0 dev f32 items', len(rows), 'keys', sorted(rows[0].keys())[:25])
print('types', dict(collections.Counter(r.get('question_type', r.get('type')) for r in rows)))
sc=collections.defaultdict(set)
for r in rows: sc[r['scene']].add(tuple(r['frame_indices']))
print('scenes', len(sc), 'scenes with one frame set', sum(len(v)==1 for v in sc.values()), 'frames per item', len(rows[0]['frame_indices']))
r=[x for x in rows if 'appearance' in str(x.get('question_type', x.get('type')))][:1]
if r: print('appearance example', {k:(str(v)[:160]) for k,v in r[0].items() if k not in ('frame_indices',)})
print(json.dumps(json.load(open('/scratch/jjyeung/orch_n30/b10_reserve/out/qsets/R0_QUESTIONS_SUMMARY.json')))[:700])
for f in ('/scratch/jjyeung/k1/run_tower_sam_2.preflight.json','/scratch/jjyeung/devs1_r2/REQUEST.json','/scratch/jjyeung/devs1_r2/COMPLETE.json'):
    try:
        d=json.load(open(f)); print('##', f, str({k:(v if not isinstance(v,(list,dict)) else (type(v).__name__, len(v))) for k,v in d.items()})[:900])
    except Exception as e: print('##', f, e)
PYEOF
echo "## k1/g3t"; ls -la /scratch/jjyeung/k1/g3t | head -8
echo "## own probe"; ls /scratch/jjyeung/k1/own_170235/native/probe | head -3; ls /scratch/jjyeung/k1/own_170235/native/probe | wc -l; d=$(ls -d /scratch/jjyeung/k1/own_170235/native/probe/*/ | head -1); ls -la $d | head -8
echo "## sam3"; ls -la /scratch/jjyeung/k1/partB 2>/dev/null | head -5; find /scratch/jjyeung/k1 -maxdepth 2 -name "sam3*.pt" 2>/dev/null | head -3; ls /scratch/jjyeung | head -60 | tr '\n' ' '
echo; echo "## g3s"; ls /scratch/jjyeung/devs1_r2/g3s32/export | head -3; ls /scratch/jjyeung/devs1_r2/g3s32/export | wc -l; ls /scratch/jjyeung/devs1_r2/g3s64/export | wc -l; ls /scratch/jjyeung/devs1_r2/g3s64/g3t | head -3; ls /scratch/jjyeung/devs1_r2/g3s64/g3t | wc -l; ls /scratch/jjyeung/devs1_r2/g3s32/g3t | wc -l
echo "## RUN2 head"; head -5 /scratch/jjyeung/k1/RUN2.log | cut -c1-400
