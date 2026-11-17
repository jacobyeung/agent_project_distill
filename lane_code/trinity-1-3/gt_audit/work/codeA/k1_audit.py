"""K1 half-extent audit: classify every K1 distance-row box with rows_r1's audit tool (read-only copy) and recompute labels.

Boxes are the K1 GT raster's own obb arrays for the row's gt_instances, the boxes behind the stored gt_value.
Writes only under /scratch/jjyeung/orch_n30/gt_audit/work/k1audit.
"""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', CUDA_VISIBLE_DEVICES='')
import collections, hashlib, importlib.util, json, math, pathlib, sys
import numpy as np

LANE = pathlib.Path('/scratch/jjyeung/orch_n30/gt_audit')
W = LANE / 'work/k1audit'
MANIFEST = LANE / 'work/k1/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'
RROOT = LANE / 'work/k1r'

spec = importlib.util.spec_from_file_location('audit_tool', str(LANE / 'work/codeA/audit.py'))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
A.CODE = W
A.ROOTS = [str(RROOT / 'orch_cd/dose_pool/out')]


def local(c):
    return RROOT / c['gt']['path'][len('/scratch/jjyeung/'):]


def main():
    W.mkdir(parents=True, exist_ok=True)
    M = json.load(open(MANIFEST))
    rows, boxes = [], {}
    for c in M['captures']:
        can = c['canonical']; p = local(c)
        drows = [r for r in c['rows'] if r['type'] == 'object_abs_distance']
        if not drows:
            continue
        if not p.exists():
            for r in drows:
                rows.append(dict(id=r['id'], capture=can, split=c['k1_split'], dataset=can.split('/')[0], source_qid=r.get('source_qid'),
                                 operands=r['operands'], stored_m=r['gt_value'], box_keys=[], raster=None, note='raster absent'))
            continue
        with np.load(p, allow_pickle=False) as z:
            ids = [int(x) for x in z['ids']]; cen, ln, ax = z['obb_centroid'], z['obb_lengths'], z['obb_axes']
            labels = [str(x) for x in z['labels']]
        for r in drows:
            keys, names = [], []
            for name in r['operands']:
                iid = int(r['gt_instances'][name]); j = ids.index(iid)
                b = dict(name=name, instance_id=iid, centroid=[float(x) for x in cen[j]], axesLengths=[float(x) for x in ln[j]],
                         normalizedAxes=[float(x) for x in ax[j]])
                k = A.boxkey(can, b); boxes[k] = dict(canonical=can, box=b); keys.append(k); names.append(labels[j])
            rows.append(dict(id=r['id'], capture=can, split=c['k1_split'], dataset=can.split('/')[0], source_qid=r.get('source_qid'),
                             operands=r['operands'], raster_labels=names, stored_m=r['gt_value'], box_keys=keys, raster=str(p)))
    print('rows', len(rows), 'boxes', len(boxes), flush=True)
    cache, checks = A.measure_rasters(boxes)
    out = []
    for i, r in enumerate(rows):
        bs = [boxes[k]['box'] for k in r['box_keys']]
        st = [cache[k]['status'] for k in r['box_keys']]
        v = {}
        if len(bs) == 2:
            for f in [(1, 1), (2, 2), (1, 2), (2, 1)]:
                try:
                    v[''.join(map(str, f))] = float(A.pair_distance(bs, f))
                except Exception as e:
                    v[''.join(map(str, f))] = None
        sel = None
        if len(st) == 2 and 'unknown' not in st:
            sel = v.get(''.join('2' if s == 'half' else '1' for s in st))
        r.update(box_statuses=st, x1_m=v.get('11'), x2_m=v.get('22'), x12_m=v.get('12'), x21_m=v.get('21'), selective_m=sel,
                 replay_ok=(v.get('11') is not None and abs(v['11'] - r['stored_m']) <= 1e-6))
        out.append(r)
        if i % 100 == 0:
            print('dist', i, len(rows), flush=True)
    with open(W / 'K1_ROW_AUDIT.jsonl', 'w') as f:
        for r in out:
            f.write(json.dumps(r, sort_keys=True) + '\n')
    A.dump(W / 'K1_BOX_AUDIT.json', {k: dict(cache[k], box=boxes[k]['box'], canonical=boxes[k]['canonical']) for k in boxes})
    print('done', flush=True)


if __name__ == '__main__':
    main()
