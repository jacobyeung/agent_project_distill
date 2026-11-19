set -u
W=/scratch/jjyeung/orch_n30
df -h /scratch | tail -1
OMP_NUM_THREADS=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json, collections, os
W='/scratch/jjyeung/orch_n30'
d = json.load(open(W+'/geo_k1/stage/K1_MANIFEST.arkit_timing.json'))
C = d['captures']
print('split x k1_split', collections.Counter((c.get('split'), c.get('k1_split')) for c in C))
print('dataset x k1_split', collections.Counter((c['canonical'].split('/')[0], c.get('k1_split')) for c in C))
c = C[0]
for k, v in c.items():
    s = json.dumps(v)
    print(' ', k, type(v).__name__, (len(v) if hasattr(v, '__len__') else ''), s[:700])
# a scannet and a scannet++ train capture
for ds in ('scannet', 'scannetpp'):
    for c in C:
        if c['canonical'].startswith(ds + '/') and c.get('k1_split') == 'train':
            print('--', c['canonical'], c['room'], 'gt', json.dumps(c['gt'])[:400]); print('   dense_frames[0:2]', json.dumps(c['dense_frames'][:2])[:500]); print('   anchor_slots', c['anchor_slots'][:8], 'anchor_indices', c['anchor_indices'][:8], len(c['anchor_indices'])); break
print('frame_staging_authorized', json.dumps(d['frame_staging_authorized'])[:600])
print('k1a_frame_parity', json.dumps(d['k1a_frame_parity'])[:600])
# do frame files exist for train capture 0's anchors?
PY
