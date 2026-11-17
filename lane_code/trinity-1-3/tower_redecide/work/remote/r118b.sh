#!/bin/bash
# tower_redecide: read-only lookups on trinity-1-18 (weights sizes, convert summaries, timing receipts). Writes nothing.
set -u
cd /scratch/jjyeung/orch_n30/geo_k1 || { echo NO_GEO_K1; exit 3; }
echo "## k1_infer paths"; grep -n -o "/scratch/[A-Za-z0-9_./-]*" k1towers/k1_infer.py | sort -u | head -20
echo "## k1_infer weight refs"; grep -n -i "weight\|ckpt\|safetensors\|from_pretrained\|checkpoint" k1towers/k1_infer.py | head -20
echo "## convert summaries"; for m in pi3x da3; do echo "-- $m"; head -c 2500 geom/CONVERT_SUMMARY_$m.json; echo; done
echo "## receipts"; ls geom/receipts | head -20
echo "## pred_gpu"; ls pred_gpu 2>&1 | head; for m in pi3x da3; do echo "$m $(ls pred_gpu/$m 2>/dev/null | wc -l)"; done
echo "## tower run"; ls /scratch/jjyeung/k1/run_tower_sam_2 2>&1 | head -5
PY=/scratch/jjyeung/envs/p1cpu/bin/python
$PY - <<'EOF'
import json, os, re, struct, glob
import numpy as np
src = open('/scratch/jjyeung/orch_n30/geo_k1/k1towers/k1_infer.py').read()
roots = sorted(set(re.findall(r"/scratch/[A-Za-z0-9_./-]+", src)))
cands = set()
for r in roots:
    for up in (r, os.path.dirname(r), os.path.dirname(os.path.dirname(r))):
        if os.path.isdir(up) and up.count('/') >= 3:
            cands.add(up)
seen = set()
for root in sorted(cands):
    for dirpath, dirs, files in os.walk(root):
        if dirpath[len(root):].count('/') >= 5:
            dirs[:] = []
            continue
        for f in files:
            if f.endswith(('.safetensors', '.pt', '.pth', '.bin', '.ckpt')):
                fp = os.path.realpath(os.path.join(dirpath, f))
                if fp in seen:
                    continue
                seen.add(fp); sz = os.path.getsize(fp); n = None
                if sz < 1e7:
                    continue
                if f.endswith('.safetensors'):
                    with open(fp, 'rb') as h:
                        hl = struct.unpack('<Q', h.read(8))[0]; hd = json.loads(h.read(hl))
                    n = sum(int(np.prod(v['shape'])) for k, v in hd.items() if k != '__metadata__')
                print('WEIGHT', os.path.join(dirpath, f), sz, n)
# tower run receipts: weights pins and seconds
for p in sorted(glob.glob('/scratch/jjyeung/k1/run_tower_sam_2/*.json'))[:3]:
    print('RECEIPT', p, open(p).read()[:1500])
for p in sorted(glob.glob('/scratch/jjyeung/orch_n30/geo_k1/geom/receipts/*'))[:2]:
    print('GEOMRECEIPT', p, open(p).read()[:800] if os.path.isfile(p) else 'dir')
EOF
