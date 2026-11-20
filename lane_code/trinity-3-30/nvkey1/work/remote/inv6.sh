G=/scratch/jjyeung/orch_n30/grd_funnel1
echo "== objects544"; head -c 1500 $G/work/objects544.jsonl; echo; wc -l $G/work/objects544.jsonl $G/work/items544.jsonl $G/work/objects400.jsonl
echo "== items544"; head -c 1200 $G/work/items544.jsonl; echo
echo "== gt staging"; ls $G/kit $G/work | head -40; ls $G/kit/rerun2 2>/dev/null | head; head -c 1500 $G/kit/rerun2/gt_staging.json 2>/dev/null; echo
echo "== manifest"; /scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json
m = json.load(open('/scratch/jjyeung/devs1_r2/anchors/g3s32/scannet__scene0155_00/A_MANIFEST.json')) if __import__('os').path.exists('/scratch/jjyeung/devs1_r2/anchors/g3s32/scannet__scene0155_00/A_MANIFEST.json') else None
import os
d = '/scratch/jjyeung/devs1_r2/anchors/g3s64/scannet__scene0155_00/A_MANIFEST.json'
m = json.load(open(d)); print('keys', list(m)); s = m['selections']; print('n selections', len(s))
for x in s[:2]:
    print({k: (v if not isinstance(v, list) or len(v) < 6 else ('list', len(v), v[:3])) for k, v in x.items()})
print({k: (v if not isinstance(v, (list, dict)) else type(v).__name__) for k, v in m.items() if k != 'selections'})
PY
