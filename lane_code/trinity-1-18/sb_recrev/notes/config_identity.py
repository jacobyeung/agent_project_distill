"""config_sha256 in C1 artifacts/receipts is the sealed trainer's identity(cfg), not a file hash.

identity() is copied from student_pilot/carrier_c1_run.py:38-45 inside the step-544 source seal
(t_b01ce449beffe35b.tar, 845b1789). Expected: step-544 config identity == 84ea03af while its file
sha256 differs, so a sha256sum search cannot find the step-200 config (identity 3ef158ce).
"""
import hashlib, json, sys

C544 = ('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w12/fixtures/work/kit07ca49df_meta/m/runs/469ddece/'
        'inputs/prepare_dd26bb95f37a43789206c6e4d4cd94bd/config.json')
B02 = '/scratch/jjyeung/orch_n30/sb_evidence/work/b02e4385.json'


def identity(cfg):
    value = {k: v for k, v in cfg.items() if k not in ('preparation', 'admission', 'authorization', 'milestone_gate')}
    if 'readout' in value:
        value['readout'] = {k: v for k, v in value['readout'].items() if k != 'contiguous_clips'}
    if value.get('frame_layout') == 'spread':
        value.pop('frame_layout')
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


for path in sys.argv[1:] or (C544, B02):
    raw = open(path, 'rb').read()
    cfg = json.loads(raw)
    print(path.split('/')[-1], 'file_sha256', hashlib.sha256(raw).hexdigest(), 'identity', identity(cfg),
          'init_artifact', json.dumps(cfg.get('init_artifact')), 'depth_init', (cfg.get('depth_init') or {}).get('sha256'))
