"""Visual check of camera convention and visibility: decoded student frame beside the instance raster for the same frame.
usage: overlay_check.py SCENE [N_FRAMES=4] -> work/overlay/<scene>_<frame>.png (left: frame, right: frame blended with ids)"""
import os, sys
import numpy as np
from PIL import Image
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(L, 'code'))
import r0lib  # noqa: E402
scene = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
sdir = os.path.join(L, 'data_cache', 'scannetpp', scene)
S = r0lib.load_scene(sdir); total, cams, conv = r0lib.load_cameras(sdir)
lay = r0lib.layout(total, 32)
os.makedirs(os.path.join(L, 'work', 'overlay'), exist_ok=True)
rng = np.random.default_rng(0); pal = rng.integers(40, 255, (len(S['inst']) + 1, 3)).astype(np.uint8); pal[-1] = 0
for fi in lay[:: max(1, len(lay) // n)][:n]:
    img = np.asarray(Image.open(os.path.join(L, 'frames', 'scannetpp', scene, '%06d.png' % fi)).convert('RGB'))
    ids = r0lib.render_ids(S['V'], S['vlab'], *cams[fi])
    col = pal[ids]; col = np.asarray(Image.fromarray(col).resize((640, 480), Image.NEAREST))
    out = np.concatenate([img, (0.5 * img + 0.5 * col).astype(np.uint8)], 1)
    p = os.path.join(L, 'work', 'overlay', '%s_%06d.png' % (scene, fi)); Image.fromarray(out).save(p); print(p)
