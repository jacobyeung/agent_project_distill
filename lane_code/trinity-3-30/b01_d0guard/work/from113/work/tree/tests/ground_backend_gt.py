"""Independent GT world transforms versus decode's pose9/depth-grid adapter."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from scipy import ndimage
from scipy.spatial.transform import Rotation

from student_pilot import carrier_c1_decode as decode, carrier_c1_routing as routing
from student_pilot import ground_lifting as lifting, p3_printed_calculator as calculator


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gt', default='/scratch/jjyeung/orch_cd/derivgen_help/data/remote_out/real_pilot_inputs_01/d1_v1d4a92c38fa3/native/GT.npz')
    ap.add_argument('--out', required=True)
    ap.add_argument('--reference-programs', default='/scratch/jjyeung/orch_cd/evalx/work/tp/programs.py')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if not Path(args.gt).is_file():
        (out/'RESULT.json').write_text(json.dumps(dict(status='PENDING-INPUT', paths=[args.gt])))
        return
    path = args.reference_programs
    spec = importlib.util.spec_from_file_location('_gt_adapter_reference', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    gt = module.GTSource(args.gt)
    if not gt.valid[0]:
        raise ValueError('Frame 1 must define the public level frame')
    pose9 = np.zeros((32, 9))
    pose9[:, 6] = 1
    pose9[:, 7:] = [2*np.arctan(gt.H/(2*gt.K[1, 1])), 2*np.arctan(gt.W/(2*gt.K[0, 0]))]
    for k in range(32):
        if gt.valid[k]:
            E = np.linalg.inv(gt.c2w[k]) @ gt.c2w[0]
            pose9[k, :3] = E[:3, 3]
            pose9[k, 3:7] = Rotation.from_matrix(E[:3, :3]).as_quat()
    up = gt.c2w[0, :3, :3].T @ [0., 0., 1.]
    queries = []
    def depth(k, uv):
        uv = np.asarray(uv)
        x, y = gt.px(uv)
        values = gt.depth[k-1, y, x].astype(float)
        queries.append(dict(frame=k, depth=values.tolist()))
        return values
    own = routing.OwnGeometry(pose9, up, depth)
    adapter = lifting.OwnGeometryAdapter(own)
    registry, calls, ground_queries, rows = calculator.PrintedPointRegistry(), [], [], []
    candidates = sorted(((int(i), name, int((gt.inst == i).sum())) for i, name in zip(gt.ids, gt.labels)
                         if name not in ('wall', 'floor', 'ceiling') and gt.labels.count(name) == 1),
                        key=lambda x: -x[2])[:5]
    for iid, name, area in candidates:
        native = (gt.inst == iid) & gt.valid[:, None, None]
        masks = np.stack([ndimage.zoom(m, (80/m.shape[0], 112/m.shape[1]), order=0, prefilter=False)
                          for m in native]).astype(bool)
        prob = (native.mean((1, 2)) >= .002).astype(float)
        expected = lifting.lift_object(name, masks, prob, gt, tau=.5)
        actual = lifting.lift_object(name, masks, prob, adapter, tau=.5)
        text = lifting.render_ground(actual, registry)
        calls.append(dict(call=f'<ground obj="{name}">', response=text, kind='ground'))
        ground_queries.append(dict(name=name, backend='mdg', mask_shape=list(masks.shape),
            mask_bits=np.packbits(masks).tolist(), prob=prob.tolist(), tau=.5))
        row = dict(name=name, raw=expected['seen'], adapter=actual['seen'],
                   same_frames=actual['frames'] == expected['frames'],
                   same_best=actual.get('best') == expected.get('best'))
        if actual['seen'] and expected['seen']:
            row['camera_max_error_m'] = float(np.max(np.abs(np.array(actual['camera'])-expected['camera'])))
            row['f1_max_error_m'] = float(np.max(np.abs(np.array(actual['f1'])-expected['f1'])))
        rows.append(row)
    record = dict(heads=dict(pose9=pose9.tolist(), gravity=up.tolist(), depth_queries=queries,
                            ground_queries=ground_queries), calls=calls)
    replay = decode.replay(record)
    usable = [r for r in rows if r['raw'] and r['adapter']]
    passed = (bool(usable) and replay['byte_equal'] and all(r['same_frames'] and r['same_best']
              and r['camera_max_error_m'] <= .02 and r['f1_max_error_m'] <= .02 for r in usable))
    result = dict(status='PASS' if passed else 'FAIL', gt=args.gt, tolerance_m=.02, rows=rows, replay=replay,
                  intrinsic_centre_offset_px=[float(gt.K[0, 2]-gt.W/2), float(gt.K[1, 2]-gt.H/2)])
    (out/'RESULT.json').write_text(json.dumps(result, indent=2))
    (out/'record.json').write_text(json.dumps(record, separators=(',', ':')))
    print(json.dumps(result))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
