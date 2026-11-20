"""Audit local inputs without substituting stored GT for reproduction inputs."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gt')
MIRROR = Path('/scratch/jjyeung/distill_sync/repo/lane_code/trinity-1-18/gt_rasters/work')
TARGETS = {
    'arkitscenes': '41126645 41159771 41159772 41254810 42446097 42899829 47331002'.split(),
    'scannet': 'scene0261_02 scene0320_01 scene0380_01 scene0515_00 scene0515_01 scene0642_01 scene0666_01'.split(),
    'scannetppv2': '246fe09e98 37c9538a2b 38fcf02d0b 3ce6d36ab5 ca3b651c23 d6bb698875 e35232b92f e667e09fe6'.split(),
}
FRAME_ROOTS = [Path('/scratch/jjyeung/devs1_frames'),
               Path('/scratch/jjyeung/orch_n30/nvkey1/work/c0stage/devs1_frames')]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def schema(path):
    result = {}
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            with z.open(name) as f:
                version = np.lib.format.read_magic(f)
                if version == (1, 0):
                    shape, order, dtype = np.lib.format.read_array_header_1_0(f)
                else:
                    shape, order, dtype = np.lib.format.read_array_header_2_0(f)
                result[name[:-4]] = dict(shape=list(shape), dtype=str(dtype), fortran=order)
    return result


def require_reproduction(results):
    """Each dataset requires an independent rebuild with every array equal."""
    for dataset in TARGETS:
        if not any(r.get('dataset') == dataset and r.get('independent_inputs') is True
                   and r.get('all_arrays_equal') is True for r in results):
            raise RuntimeError('Reproduction gate unmet: ' + dataset)


def main():
    manifest = json.loads((ROOT / 'DEVS1_MANIFEST.json').read_text())
    by_id = {r['scene'].split('/')[-1]: r for r in manifest['captures']}
    listing = (ROOT / 'list.txt').read_text().splitlines()
    stage_ok = 'PIPE_RC 0 0 0 0' in (ROOT / 'stage.log').read_text()
    rows = []
    for dataset, ids in TARGETS.items():
        for cid in ids:
            m = by_id[cid]
            raw = [p for p in listing if cid in Path(p).parts]
            missing = [p for p in raw if not (ROOT / 'raw' / p).is_file()]
            frame_checks = []
            for frame in m['frames']:
                p = next((base / frame['path'] for base in FRAME_ROOTS
                          if (base / frame['path']).is_file()), None)
                frame_checks.append(dict(index=frame['index'], path=str(p) if p else None,
                                         sha256=frame['sha256'], verified=p is not None and sha(p) == frame['sha256']))
            rows.append(dict(dataset=dataset, capture=cid, raw_files=len(raw), missing_raw=missing,
                             anchors=m['anchor_indices'], hw=m['hw'], frames=frame_checks,
                             status='BLOCKED_REPRODUCTION', accepted=False,
                             self_consistency=None, binding=None, applied_box_convention=None))
    references = []
    for path in sorted(REFERENCE.glob('*_gt/gt/*.npz')):
        references.append(dict(path=str(path), schema=schema(path)))
    requests = [
        dict(dataset='scannet', capture='scene0166_00',
             reference=str(REFERENCE / 't1_gt/gt/scannet__scene0166_00.npz'),
             required=['instance_mesh.npz', 'official_cameras.npz', 'instances.json'],
             raw_alternative=['scene0166_00.sens', 'scene0166_00_vh_clean_2.ply',
                              'scene0166_00_vh_clean_2.0.010000.segs.json',
                              'scene0166_00.aggregation.json', 'scene0166_00.txt']),
        dict(dataset='scannetppv2', capture='17c5e6a336',
             reference=str(REFERENCE / 't1_gt/gt/scannetppv2__17c5e6a336.npz'),
             searched_proof_dir=str(MIRROR / 'proof_pinned/spp_17c5e6a336'),
             available=['instances.json'], missing=['instance_mesh.npz', 'official_cameras.npz']),
        dict(dataset='arkitscenes', capture='41069053',
             reference=str(REFERENCE / 'arkit_gt/gt/41069053.npz'),
             searched_proof_dir=str(MIRROR / 'proof_arkit2/src'),
             available=['41069053_3dod_annotation.json'],
             missing=['41069053_frames/lowres_wide.traj', '32 anchor lowres_depth PNGs',
                      '32 matching lowres_wide_intrinsics pincams', 'full timestamp-sorted depth listing']),
    ]
    for r in requests:
        r.update(independent_inputs=False, all_arrays_equal=None, status='NOT_RUN_MISSING_INPUTS')
    meta = json.loads((MIRROR / 'proof_pinned/spp_17c5e6a336/instances.json').read_text())
    with np.load(requests[1]['reference']) as z:
        lengths_equal = np.array_equal(z['obb_lengths'], [g['obb']['axesLengths'] for g in meta['segGroups']])
    out = dict(stage_complete=stage_ok, captures=rows, references=references, reproduction=requests,
               spp_metadata_lengths_equal=bool(lengths_equal),
               spp_mesh_extent_comparison=None, accepted=0, required_passes=15,
               verdict='BLOCKED: independent reproduction inputs unavailable; 15/22 bar not evaluated')
    (ROOT / 'out/PREFLIGHT.json').write_text(json.dumps(out, indent=2) + '\n')
    (ROOT / 'out/REPRO_INPUTS_REQUIRED.json').write_text(json.dumps(requests, indent=2) + '\n')
    print(json.dumps(dict(stage_complete=stage_ok, targets=len(rows), references=len(references),
                          raw_files=sum(r['raw_files'] for r in rows),
                          missing_raw=sum(len(r['missing_raw']) for r in rows),
                          verified_frames=sum(f['verified'] for r in rows for f in r['frames']),
                          accepted=0, verdict=out['verdict'])))


if __name__ == '__main__':
    main()
