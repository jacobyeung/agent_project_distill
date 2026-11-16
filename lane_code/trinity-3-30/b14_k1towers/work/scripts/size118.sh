K=/scratch/jjyeung/geo_bakeoff_kit; date -u
du -sh $K/runtime/* $K/assets/* $K/work $K/data 2>/dev/null
du -sh /scratch/jjyeung/k1_frames
/scratch/jjyeung/envs/planner_local_v1/bin/python - <<'PY'
import json, os
m = json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
ps = {f['path'] for c in m['captures'] for f in c['dense_frames']}
gt = {f['path'] for c in m['captures'] if c.get('gt') and os.path.isfile(c['gt']['path']) for f in c['dense_frames']}
print('frames all', len(ps), sum(os.path.getsize(p) for p in ps) / 1e9, 'GB; gt-only', len(gt), sum(os.path.getsize(p) for p in gt) / 1e9)
import glob
t = glob.glob('/scratch/jjyeung/k1/run_tower_sam_2/*/tower.npz'); print('tower.npz', len(t), sum(os.path.getsize(p) for p in t) / 1e9)
PY
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
