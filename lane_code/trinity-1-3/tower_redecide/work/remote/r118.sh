#!/bin/bash
# tower_redecide: read-only pose extraction on trinity-1-18 (CPU; reads node-local /scratch only; writes nothing).
set -u
cd /scratch/jjyeung/orch_n30/geo_k1 || { echo NO_GEO_K1; exit 3; }
echo "## geom"; ls geom; for a in pi3x_native da3_native; do echo "$a $(ls geom/$a | wc -l)"; done
echo "## k1towers"; ls k1towers | head -40
echo "## guard lines"; grep -n -i "guard\|validate\|opposes\|refus" k1towers/k1_convert.py | head -20
echo "## kit"; ls /scratch/jjyeung/geo_bakeoff_assets/kit 2>&1 | head -20
PY=""; for p in /scratch/jjyeung/envs/p1cpu/bin/python /scratch/jjyeung/envs/geo_kit/bin/python python3; do if $p -c "import numpy" 2>/dev/null; then PY=$p; break; fi; done
echo "## python $PY"
GDJSON='__GDJSON__'
$PY - "$GDJSON" <<'EOF'
import json, os, sys, glob, io, base64, struct
import numpy as np
gd = json.loads(sys.argv[1])
out, keys = {}, {}
for arm in ('pi3x_native', 'da3_native'):
    for p in sorted(glob.glob(f'/scratch/jjyeung/orch_n30/geo_k1/geom/{arm}/*.npz')):
        z = np.load(p, allow_pickle=False)
        keys.setdefault(arm, {k: list(z[k].shape) for k in z.files})
        cap = os.path.basename(p)[:-4]
        out[f'{arm}|{cap}|c2w'] = z['camera_to_world'].astype(np.float32)
        if 'scale' in z.files:
            out[f'{arm}|{cap}|scale'] = np.asarray(z['scale'], np.float64)
for cap, p in gd.items():
    if not os.path.exists(p):
        continue
    z = np.load(p, allow_pickle=False)
    keys.setdefault('GD', {k: list(z[k].shape) for k in z.files})
    c = cap.replace('/', '__')
    out[f'GD|{c}|c2w'] = z['camera_to_world'].astype(np.float32)
    if 'scale' in z.files:
        out[f'GD|{c}|scale'] = np.asarray(z['scale'], np.float64)
print('KEYS', json.dumps(keys))
kit = '/scratch/jjyeung/geo_bakeoff_assets/kit'
for root, dirs, files in os.walk(kit):
    if root[len(kit):].count('/') > 5:
        dirs[:] = []
        continue
    for f in files:
        if f.endswith(('.safetensors', '.pt', '.pth', '.bin', '.ckpt')):
            fp = os.path.join(root, f); sz = os.path.getsize(fp); n = None
            if f.endswith('.safetensors'):
                with open(fp, 'rb') as h:
                    hl = struct.unpack('<Q', h.read(8))[0]; hd = json.loads(h.read(hl))
                n = sum(int(np.prod(v['shape'])) for k, v in hd.items() if k != '__metadata__')
            print('WEIGHT', fp, sz, n)
buf = io.BytesIO(); np.savez_compressed(buf, **out)
print('NPZ_B64_BEGIN'); print(base64.b64encode(buf.getvalue()).decode()); print('NPZ_B64_END')
EOF
