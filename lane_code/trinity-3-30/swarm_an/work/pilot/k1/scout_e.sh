set -u
W=/scratch/jjyeung/orch_n30
echo "== stage/k1"; ls -la $W/geo_k1/stage/k1 | head -30
echo "== manifest"; ls -la $W/geo_k1/stage/K1_MANIFEST.arkit_timing.json
OMP_NUM_THREADS=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json, collections
W='/scratch/jjyeung/orch_n30'
d = json.load(open(W+'/geo_k1/stage/K1_MANIFEST.arkit_timing.json'))
def show(x, depth=0, name='root'):
    pad = '  '*depth
    if isinstance(x, dict):
        print(pad, name, 'dict', len(x), list(x.keys())[:14])
        if depth < 3:
            for k in list(x.keys())[:6]: show(x[k], depth+1, k)
    elif isinstance(x, list):
        print(pad, name, 'list', len(x))
        if x and depth < 3: show(x[0], depth+1, name+'[0]')
    else:
        print(pad, name, type(x).__name__, json.dumps(x)[:160])
show(d)
PY
