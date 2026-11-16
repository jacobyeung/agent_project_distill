set -u
S=/dev/shm/jjyeung/b14; M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
W=/scratch/jjyeung/orch_n30/geo_k1/stage; mkdir -p $W/code $W/k1/run_tower_sam_2; date -u
/scratch/jjyeung/envs/planner_local_v1/bin/python - <<PY
import json, glob, os, shutil, numpy as np
m = json.load(open('$M'))
fr = sorted({f['path'][len('/scratch/jjyeung/'):] for c in m['captures'] for f in c['dense_frames']})
assert all(p.startswith('k1_frames/') for p in fr)
n = 0
for d in sorted(glob.glob('/scratch/jjyeung/k1/run_tower_sam_2/*/PHASE_COMPLETE.json')):
    src = os.path.dirname(d); dst = '$W/k1/run_tower_sam_2/' + os.path.basename(src); os.makedirs(dst, exist_ok=True)
    shutil.copy2(d, dst)
    with np.load(src + '/tower.npz', allow_pickle=False) as z:
        np.savez(dst + '/tower.npz', frame_indices=z['frame_indices'], anchor_slots=z['anchor_slots'])
    n += 1
kit = ['geo_bakeoff_kit/' + x for x in ['KIT_SEAL.json', 'PAYLOAD.json', 'runtime', 'work', 'assets/downloads.jsonl', 'assets/moge2']]
kit += sorted(x[len('/scratch/jjyeung/'):] for x in glob.glob('/scratch/jjyeung/geo_bakeoff_kit/assets/*-src'))
open('$W/files_common.txt', 'w').write('\n'.join(kit + fr) + '\n')
print('towers', n, 'frames', len(fr), 'frame_GB', sum(os.path.getsize('/scratch/jjyeung/' + p) for p in fr) / 1e9)
PY
cp -p /scratch/jjyeung/orch_n30/geo_k1/k1towers/*.py $W/code/ && cp -p $M $W/
du -sh $W/k1
cd /scratch/jjyeung
time (tar cf - -T $W/files_common.txt -C $W code k1 K1_MANIFEST.arkit_timing.json | timeout 900 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib "mkdir -p $S && tar xf - -C $S && du -sh $S && du -sh /dev/shm/jjyeung/* | grep -v '^[0-9.]*[KM]'") 2>&1 | tail -12
