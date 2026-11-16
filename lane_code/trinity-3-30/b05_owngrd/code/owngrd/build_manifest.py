"""Build the teacher-pass manifest for a block of captures (first block: K1's pilot captures).

Every capture passes the eligibility gate; frames are the capture's 32 anchors (path on the GPU node, sha256 pin);
names come from vocab.capture_names over the pinned GT raster. The manifest records the GT raster pins, the
anchor/GT frame-index check, the gate receipt and the vocabulary it drew confusers and absent names from.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

import numpy as np

from .common import atomic_write_json, sha256_file, sha256_json
from .eligibility import Gate
from .vocab import capture_names, gt_visible_names, STRUCTURAL


def gt_path(gt_root: Path, canonical: str):
    ds, scene = canonical.split('/', 1)
    if ds == 'arkitscenes':
        return gt_root / 'arkit_gt/gt' / f'{scene}.npz'
    tag = 'scannetppv2' if ds == 'scannetpp' else 'scannet'
    return gt_root / 't1_gt/gt' / f'{tag}__{scene}.npz'


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--k1-manifest', required=True)
    ap.add_argument('--gate-root', required=True)
    ap.add_argument('--gt-root', required=True, help='dir holding arkit_gt/gt and t1_gt/gt')
    ap.add_argument('--frame-root', required=True, help='frame store on the GPU node (<root>/<sha[:2]>/<sha>.png)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--split', choices=('train', 'heldout', 'all'), default='all')
    a = ap.parse_args(argv)
    k1 = json.loads(Path(a.k1_manifest).read_text())
    gate = Gate(a.gate_root)
    gt_root = Path(a.gt_root)
    kept, refused, missing_gt, index_mismatch = [], {}, [], []
    rasters = {}
    for c in k1['captures']:
        if a.split != 'all' and c['k1_split'] != a.split:
            continue
        why = gate.reasons(c['canonical'], c.get('room'))
        if why:
            refused[c['canonical']] = why
            continue
        p = gt_path(gt_root, c['canonical'])
        if not p.exists():
            missing_gt.append(c['canonical'])
            continue
        z = np.load(p, allow_pickle=False)
        anchors = [c['dense_frames'][s] for s in c['anchor_slots']]
        if [f['index'] for f in anchors] != c['anchor_indices'] or z['frame_indices'].tolist() != c['anchor_indices']:
            index_mismatch.append(c['canonical'])
            continue
        rasters[c['canonical']] = (p, z, anchors)
        kept.append(c)
    vocab = collections.defaultdict(collections.Counter)
    for can, (p, z, _) in rasters.items():
        px, _, _ = gt_visible_names(z)
        vocab[can.split('/')[0]].update(px.keys())
    vocab_by_ds = {ds: [n for n, k in cnt.most_common() if k >= 3 and n not in STRUCTURAL][:150] for ds, cnt in vocab.items()}
    caps = []
    for c in kept:
        p, z, anchors = rasters[c['canonical']]
        operands = [o for r in c.get('rows', []) for o in r.get('operands', [])]
        names = capture_names(c['canonical'], z, operands, vocab_by_ds)
        caps.append({'canonical': c['canonical'], 'room': c['room'], 'k1_split': c['k1_split'],
                     'aliases': [], 'frames': [{'slot': k, 'index': f['index'], 'sha256': f['sha256'],
                                                'path': f"{a.frame_root}/{f['sha256'][:2]}/{f['sha256']}.png"}
                                               for k, f in enumerate(anchors)],
                     'gt': {'path': str(p), 'sha256': sha256_file(p)}, 'operands': operands, 'names': names})
    receipt = gate.admit(caps)
    man = {'schema': 'owngrd-teacher-manifest-v1', 'source': {'k1_manifest': a.k1_manifest,
           'k1_manifest_sha256': sha256_file(a.k1_manifest), 'split': a.split}, 'gate_root': a.gate_root, 'gate_receipt': receipt,
           'refused': refused, 'missing_gt': missing_gt, 'index_mismatch': index_mismatch,
           'vocab_by_ds': vocab_by_ds, 'vocab_sha256': sha256_json(vocab_by_ds), 'captures': caps,
           'counts': {'captures': len(caps), 'names': sum(len(c['names']) for c in caps),
                      'by_role': dict(collections.Counter(n['role'] for c in caps for n in c['names'])),
                      'by_split': dict(collections.Counter(c['k1_split'] for c in caps))}}
    atomic_write_json(a.out, man)
    print(json.dumps({k: man[k] for k in ('counts', 'missing_gt', 'index_mismatch')}, indent=1),
          'refused', len(refused), 'sha256', sha256_file(a.out))


if __name__ == '__main__':
    main()
