"""Lane sb_countdesign, CPU pilot on K1: per-frame mask duplicate suppression for the SAM 3 teacher proposals.
For each (capture, GT name, frame): sort by joint score; drop a proposal when its mask has IoU > 0.5 with a kept one or when more than
80% of the smaller mask lies inside the other (part / whole duplicates). Output K1_NMS.npz: rows (cap, name, frame, k, keep, max_iou, max_contain)."""
import json, gzip, os, time
import numpy as np
LAB = '/scratch/jjyeung/orch_n30/b05_owngrd/work/labels_k1'
TEA = '/scratch/jjyeung/orch_n30/b05_owngrd/work/teacher_k1_full/teacher_k1'
meta = json.load(open('K1_LIFT_META.json'))
capix = {c['capture']: i for i, c in enumerate(meta['captures'])}; nameix = {n: i for i, n in enumerate(meta['names'])}
def rle_decode(r):
    h, w = r['size']; counts = r['counts']
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape((h, w), order='F')
out = []; t0 = time.time(); n = 0
for fn in sorted(os.listdir(LAB)):
    if not fn.endswith('.labels.json.gz'): continue
    lab = json.load(gzip.open(os.path.join(LAB, fn)))
    if lab['canonical'] not in capix: continue
    ci = capix[lab['canonical']]
    tea = json.load(gzip.open(os.path.join(TEA, fn[:-len('.labels.json.gz')], 'teacher.json.gz')))
    for name, role in lab['roles'].items():
        if role != 'gt': continue
        ni = nameix[name]
        for k in range(32):
            tf = tea['frames'][str(k)]['phrases'].get(name)
            if tf is None or not tf['instances']: continue
            ins = tf['instances']
            if len(ins) == 1:
                out.append((ci, ni, k, 0, 1, 0.0, 0.0)); continue
            order = sorted(range(len(ins)), key=lambda i: -ins[i]['joint_score'])
            masks = {i: rle_decode(ins[i]['mask'])[::2, ::2] for i in order}
            kept = []
            for i in order:
                m = masks[i]; a = int(m.sum()); mi = 0.0; mc = 0.0
                for j in kept:
                    inter = int((m & masks[j]).sum())
                    if inter == 0: continue
                    b = int(masks[j].sum())
                    mi = max(mi, inter / float(a + b - inter)); mc = max(mc, inter / float(max(1, min(a, b))))
                keep = int(a > 0 and mi <= 0.5 and mc <= 0.8)
                if keep: kept.append(i)
                out.append((ci, ni, k, i, keep, mi, mc))
    n += 1
    if n % 50 == 0: print(n, len(out), '%.0fs' % (time.time() - t0), flush=True)
np.savez_compressed('K1_NMS.npz', rows=np.asarray(out, np.float32))
print('DONE', len(out), '%.0fs' % (time.time() - t0))
