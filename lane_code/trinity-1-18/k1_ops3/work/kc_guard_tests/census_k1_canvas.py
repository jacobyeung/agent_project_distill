"""Authenticate and map every primary GT raster without candidate extraction."""
from collections import Counter
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'kc_guard/k1_build/work/kit_k1a/work'))
import k1_pipeline as K
K._native()
m = K.B.load(ROOT.parent / 'manifest_v2/a40fbc19.json')
selection = K.G.load(ROOT.parent / 'gt_sets/GT_SET_PRIMARY_296.json')
captures, meta = K.G.select(m, selection)
maps = {}
for c in captures:
    gt = K.gt_arrays(c, selection)
    assert gt['frame_indices'].tolist() == c['anchor_indices']
    assert gt['instances'].shape == (32, 240, 320)
    maps[c['canonical']] = gt['gt_canvas_map']
assert len(maps) == 296
record = dict(gt_set=meta, captures_checked=len(maps), gt_canvas_map=maps,
              gt_canvas_map_counts=dict(Counter(maps.values())), all_pins_verified=True,
              tables_executed=False)
(ROOT / 'patch3_gt_canvas_census.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k not in ('gt_set', 'gt_canvas_map')}))
