"""Copy an mdg-export dir with every mask nearest-resampled to the kit's 80x112 grid (every grid spans the whole frame,
so this resamples by normalized coordinates). For selectors that need one grid (hrp_infer's export).
usage: python -m rk.resample --export DIR --out DIR"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from .ground import mdg
from .programs import read_index

SHAPE = (80, 112)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--export', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args(argv)
    E = mdg()
    root, entries = read_index(a.export)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for key, entry in sorted(entries.items()):
        names, values, audit = E.read_npz(root/entry['npz'])
        m = values['mask']
        if m.shape[-2:] != SHAPE:
            zoom = (1, 1, SHAPE[0]/m.shape[-2], SHAPE[1]/m.shape[-1])
            values = dict(values, mask=ndimage.zoom(m.astype(np.uint8), zoom, order=0, prefilter=False) > 0)
        audit = dict(audit, resampled_from=str((root/entry['npz']).resolve()), mask_shape=list(SHAPE))
        name = key.replace('/', '__')+'.npz'
        E.save_npz(out/name, names, values, audit)
        index[key] = dict(scene=key, scene_key=key, npz=name, frame_indices=entry['frame_indices'])
    (out/'INDEX.json').write_text(json.dumps(index, indent=1)+'\n')
    print(json.dumps(dict(scenes=len(index))))


if __name__ == '__main__':
    main()
