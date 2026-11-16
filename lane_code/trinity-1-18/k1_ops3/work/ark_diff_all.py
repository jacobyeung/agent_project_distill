"""Verify the 2,200 pinned ARKit PNGs and measure each against the decoded frame (ruling 19:46Z)."""
import collections, hashlib, json, os, sys
import cv2, numpy as np
cv2.setNumThreads(1)
W = '/scratch/jjyeung/orch_n30/k1_ops3/work'; S = '/scratch/jjyeung/k1_frames'
rows = [json.loads(l) for l in open(W + '/ARKIT_MISMATCH_2200.jsonl')]
res = []
for r in rows:
    pp = os.path.join(W, 'ark_pinned', r['pin'][:2], r['pin'] + '.png')
    data = open(pp, 'rb').read(); ok = hashlib.sha256(data).hexdigest() == r['pin']
    A = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
    B = cv2.imread(os.path.join(S, r['built'][:2], r['built'] + '.png'), cv2.IMREAD_UNCHANGED)
    if A.shape != B.shape:
        res.append(dict(r, sha_ok=ok, shape_ok=False)); continue
    d = np.abs(A.astype(np.int16) - B.astype(np.int16)); px = int((d.max(axis=2) > 0).sum()) if d.ndim == 3 else int((d > 0).sum())
    res.append(dict(r, sha_ok=ok, shape_ok=True, diff_px=px, npx=A.shape[0] * A.shape[1], maxdiff=[int(x) for x in d.reshape(-1, d.shape[-1] if d.ndim == 3 else 1).max(0)]))
json.dump(res, open(W + '/ARK_DIFF_ALL.json', 'w'))
held = [x for x in res if not x['sha_ok'] or not x['shape_ok'] or max(x['maxdiff']) > 1 or x['diff_px'] > 0.001 * x['npx']]
json.dump(sorted({x['pin'] for x in held}), open(W + '/ARK_HELD_PINS.json', 'w'))
px = np.array([x.get('diff_px', -1) for x in res]); md = collections.Counter(max(x['maxdiff']) for x in res if x['shape_ok'])
q = np.percentile(px, [0, 50, 90, 99, 100]).tolist()
caps = collections.Counter(x['canonical'] for x in held)
L = ['# PARITY_DIFF_ARKIT_ALL (k1_ops3, trinity-1-18)', '',
     'All 2,200 mismatching pinned ARKit frames. Pinned PNG from the Orchard replica (packed tar sha256 8049ab2e...); decoded PNG from wa.py on 1-18 (cv2 4.10.0, numpy 1.26.4). Orchard k6 used opencv-python-headless 4.14.0.94, numpy 2.2.6.', '',
     f'- sha256 equals pin: {sum(x["sha_ok"] for x in res)} of {len(res)}; shape equal: {sum(x["shape_ok"] for x in res)}',
     f'- max abs difference per frame (grey levels): {dict(sorted(md.items()))}',
     f'- differing pixels per frame (of 307,200): min/median/p90/p99/max = {[int(v) for v in q]}',
     f'- frames over a limit (max diff > 1 or differing pixels > 0.1% = 307): {len(held)} in {len(caps)} captures; substitutable: {len(res) - len(held)}',
     '', '| canonical | index | max diff BGR | differing px |', '|---|---:|---|---:|']
for x in sorted(held, key=lambda x: (x['canonical'], x['index'])):
    L.append(f"| {x['canonical']} | {x['index']} | {x.get('maxdiff')} | {x.get('diff_px')} |")
open(W + '/PARITY_DIFF_ARKIT_ALL.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L[:10]))
