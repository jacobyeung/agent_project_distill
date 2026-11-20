"""Measure the anomalous Down capture without assuming its sky rotation."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
LOW = Path('/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/out')
sys.path.append('/scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3.12/site-packages')
import cv2
cv2.setNumThreads(1)


def main():
    recipe = json.loads((LOW/'RECIPE_K3.json').read_text())
    records = []
    for rec in recipe['records']:
        with Image.open(rec['source']) as im:
            source = np.array(im.convert('RGB'))
        h = rec['served_sha256']
        with Image.open(Path(recipe['served_root'])/h[:2]/(h+'.png')) as im:
            target = np.array(im.convert('RGB'))
        sideways = target.shape[0] > target.shape[1]
        turn = 3 if sideways else 0
        result = cv2.resize(np.rot90(source, turn).copy(),
                            (target.shape[1], target.shape[0]), interpolation=cv2.INTER_CUBIC)
        delta = np.abs(result.astype(np.int16)-target.astype(np.int16))
        records.append(dict(video=rec['video'], index=rec['index'], turns_ccw=turn,
                            source_hw=list(source.shape[:2]), served_hw=list(target.shape[:2]),
                            pixel_exact=not bool(delta.any()), max_abs=int(delta.max()),
                            mae=float(delta.mean())))
    result = dict(recipe_sha256=hashlib.sha256((LOW/'RECIPE_K3.json').read_bytes()).hexdigest(),
                  diagnostic='OpenCV bicubic, Up/Down unrotated, Left clockwise; not an exact recipe',
                  pixel_exact=sum(r['pixel_exact'] for r in records),
                  max_abs=max(r['max_abs'] for r in records),
                  mean_absolute_error=sum(r['mae'] for r in records)/len(records),records=records)
    with (ROOT/'SERVED_IDENTITY_K3b.json').open('x') as f:
        json.dump(result, f, indent=2)
    print(json.dumps({k:v for k,v in result.items() if k != 'records'}))


if __name__ == '__main__':
    main()
