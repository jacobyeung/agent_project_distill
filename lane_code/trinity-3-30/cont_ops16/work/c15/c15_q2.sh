K=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f
/usr/bin/python3 -I -s -B - <<'PY'
import json
K='/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f'
c=json.load(open(K+'/inputs/prepare_9b0c4b095487492a80bd5e9030d5bbc0/config.json'))
print('prep', json.dumps(c.get('preparation'))[:600])
d=json.load(open(K+'/inputs/data_receipt.json'))
print('dr keys', list(d)[:20]); print('dr config', json.dumps(d.get('config'))[:400])
print('frame_layout', c.get('frame_layout'), 'geometry_online', c.get('geometry_online'))
PY
