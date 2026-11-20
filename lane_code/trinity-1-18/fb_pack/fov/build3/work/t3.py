"""Probe build3 anchor_grid with rows in the producer's fov_check 762093b8 schema."""
import hashlib, importlib.util, json, sys
import numpy as np
spec = importlib.util.spec_from_file_location('sf3', '/scratch/jjyeung/orch_n30/fb_pack/fov/build3/score_fov.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
cap = {'key': 'k', 'anchor_indices': list(range(0, 32))}
g = hashlib.sha256(np.linspace(0, 1000, 51, dtype=np.float32).tobytes()).hexdigest()
assert g.startswith('c52b96a9'), g
good = dict(key='k', scored=True, served_equal=True, anchor_indices=cap['anchor_indices'], capture_sha256_equal=True,
            grid_uv=g, receipt_ok=True, second_pass_max_abs=0.0)
out = {'good': m.anchor_grid(dict(good), cap, 'X')}
for name, ch in [('wrong_sha', {'grid_uv': '0' * 64}), ('unscored', {'scored': False}), ('receipt_bad', {'receipt_ok': False}),
                 ('cap_bad', {'capture_sha256_equal': False}), ('second_pass', {'second_pass_max_abs': 1e-7}),
                 ('anchors', {'anchor_indices': list(range(1, 33))}), ('values_ok', {'grid_uv': np.linspace(0, 1000, 51).tolist()})]:
    try:
        out[name] = ('PASS', m.anchor_grid(dict(good, **ch), cap, 'X'))
    except BaseException as e:
        out[name] = ('REFUSED', type(e).__name__, str(e)[:120])
print(json.dumps(out, indent=1, default=str))
