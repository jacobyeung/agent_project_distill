"""Cross-tree processor/admit/encoder checks for review tr19_revC1. Stubs only the
pretrained processor, frame decode and the final processor call; no files are written
outside argv[3]."""
import base64
import copy
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

tree = Path(sys.argv[1]).resolve()
label = sys.argv[2]
output = Path(sys.argv[3])
sys.path.insert(0, str(tree))

import numpy as np
import torch
from student_pilot import carrier_c1_run as run, carrier_c1_data as data, pose_samples, ground_tokens
from student_pilot.camera_targets import CARRIER_TOKEN, VIDEO_TOKEN

CENSUS = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/census24')
PCFG = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24k/work/build24m4k/p_configs')


def load_cfg(path):
    value = json.loads(Path(path).read_bytes())
    if set(value) == {'encoding', 'payload', 'sha256'}:
        value = json.loads(base64.b64decode(value['payload']))
    return value


N = {f'{k}_{s}': load_cfg(CENSUS / f'{k}_{s}.json') for k in ('q', 'n', 'n_go', 'qd') for s in ('c', 'n')}
P = {f.stem: load_cfg(f) for f in sorted(PCFG.glob('*.json'))}
PREP_KEYS = ('frame_layout', 'frame_pair_gap_seconds', 'skip_unsupervised_lm', 'depth_fov_source', 'depth_init',
             'exclusions', 'report_exclusions', 'tool_mode_flag', 'ground_target_filter', 's1_route_policy', 'h1',
             'b7_inputs', 'r1_training', 'frame_count', 'max_pixels', 'min_pixels', 'frame_markers', 'r2_membership',
             'routing_opener_init', 'routing_vocabulary', 'r2_identity', 'r2_sampling', 'extent_receipt',
             'geometry_connector', 'frame_embeddings')


def training_receipt(cfg):
    """C prepare() copy list (carrier_c1_run.py:633-637) plus prepared()'s final-mode merge (:712-720)."""
    receipt = {k: cfg[k] for k in PREP_KEYS if k in cfg}
    receipt['training_mode'] = cfg.get('training_mode', 'mixed')
    if 'mdg' in cfg:
        receipt['mdg'] = cfg['mdg']
    if cfg.get('geometry_online'):
        receipt['geometry_online'] = cfg['geometry_online']
    if cfg.get('training_mode') == 'final':
        receipt['frame_markers'] = cfg.get('frame_markers', False)
    return receipt


def build(receipt):
    proc = SimpleNamespace(tokenizer=SimpleNamespace())
    calls = []
    def routing_tokens(p, include_ground=False):
        calls.append(['routing', include_ground])
    with patch.object(run, 'processor_for', return_value=proc), \
            patch.object(run.rehearsal, 'fixture_manifest', return_value={}), \
            patch.object(run.routing, 'add_routing_tokens', side_effect=routing_tokens), \
            patch.object(ground_tokens, 'add', side_effect=lambda p: calls.append(['ground'])):
        try:
            p = run.processor_for_receipt({'root': 'unused'}, copy.deepcopy(receipt))
        except Exception as exc:
            return dict(refused=f'{type(exc).__name__}: {exc}'), None
    record = dict(tokenizer=dict(vars(p.tokenizer)), has_b7_layout=hasattr(p, '_b7_layout'),
                  b7_layout=getattr(p, '_b7_layout', None), calls=calls,
                  attrs=sorted(k for k in vars(p) if k != 'tokenizer'))
    return record, p


result = dict(tree=str(tree), label=label, processor={})
processors = {}
for name, cfg in {**{'N_' + k: v for k, v in N.items()}, **{'P_' + k: v for k, v in P.items()}}.items():
    for kind, receipt in (('config', cfg), ('training_receipt', training_receipt(cfg))):
        record, proc = build(receipt)
        result['processor'][name + ':' + kind] = record
        if proc is not None:
            processors[name + ':' + kind] = proc


# --- admit up to the step after the layout clause (C trees only) ---------------------------------
class Reached(Exception):
    pass


def admit_until_layout(cfg):
    from launch_r1 import entry
    from student_pilot import r1_coverage, r1_persisted, r1_training
    with patch.object(r1_coverage, 'deferred', return_value=False), \
            patch.object(r1_persisted, 'init_policy', return_value=None), \
            patch.object(entry, 'load', return_value={}), patch.object(entry, 'pinned', side_effect=lambda x: x), \
            patch.object(r1_training, 'validate', return_value=None), \
            patch.object(r1_training, 'boundary', side_effect=Reached()):
        try:
            entry.admit(copy.deepcopy(cfg))
            return 'returned'
        except Reached:
            return 'PASSED_LAYOUT_AND_STORE_HASHES'
        except Exception as exc:
            return f'{type(exc).__name__}: {exc}'


pins = dict(min_pixels=16384, max_pixels=147456, frame_count=32, frame_layout='duplicate', frame_markers=True)
if (tree / 'launch_r1/entry.py').exists():
    admit = {}
    for name, cfg in N.items():
        admit[name] = admit_until_layout(cfg)
    base = N['n_n']
    def variant(**changes):
        cfg = copy.deepcopy(base)
        for k, v in changes.items():
            if v is KeyError:
                cfg.pop(k, None)
            else:
                cfg[k] = v
        return cfg
    cases = {
        'pixels_absent': variant(min_pixels=KeyError, max_pixels=KeyError),
        'pixels_explicit_P_values': variant(min_pixels=16384, max_pixels=147456),
        'max_pixels_only': variant(max_pixels=147456),
        'max_pixels_zero': variant(max_pixels=0),
        'layout_spread': variant(frame_layout='spread'),
        'layout_absent': variant(frame_layout=KeyError),
        'markers_false': variant(frame_markers=False),
        'markers_absent': variant(frame_markers=KeyError),
        'frame_count_31': variant(frame_count=31),
        'frame_count_64': variant(frame_count=64),
        'frame_count_absent': variant(frame_count=KeyError),
        'frame_count_null': variant(frame_count=None),
        'frame_count_float': variant(frame_count=32.0),
        'b7_pins_toplevel_null': variant(b7_inputs=dict(pins)),
        'b7_pins_toplevel_pinned': variant(b7_inputs=dict(pins), min_pixels=16384, max_pixels=147456),
        'b7_empty_dict': variant(b7_inputs={}),
        'b7_none': variant(b7_inputs=None),
        'store_hashes_missing_one': variant(r1_training={**base['r1_training'], 'store_hashes': {
            k: v for k, v in base['r1_training']['store_hashes'].items() if k != 'pose'}}),
    }
    for name, cfg in cases.items():
        admit['n_n+' + name] = admit_until_layout(cfg)
    result['admit'] = admit


# --- encoder: what reaches encode_frames ------------------------------------------------------
def row_for(count, pose=False):
    row = dict(dataset='scannet', scene='scene_fixture', target='A', category='vqa',
               student_input=dict(question='Q?', options=['a', 'b'], frames=[{'path': f'/f/{i}.jpg', 'sha256': '0' * 64}
                                  for i in range(count)], frame_indices=[3 * i for i in range(count)],
                                  timestamps=[3 * i / 30 for i in range(count)], fps=30.0, total_num_frames=3 * count + 1))
    return row


def encode_capture(proc, row, layout='duplicate'):
    captured = []
    rng = np.random.default_rng(7)
    arrays = rng.integers(0, 255, size=(len(row['student_input']['frames']), 4, 6, 3), dtype=np.uint8)
    def encode(processor, question, options, rgb, metadata, target, pixels, limit):
        captured.append(dict(rgb_sha256=hashlib.sha256(np.ascontiguousarray(rgb).tobytes()).hexdigest(),
                             shape=list(rgb.shape), dtype=str(rgb.dtype), pixels=list(pixels),
                             indices=list(metadata.frames_indices), fps=metadata.fps,
                             total=metadata.total_num_frames, width=metadata.width, height=metadata.height,
                             question=question, options=list(options), target=target, limit=limit))
        return {}, {'stub_audit': True}
    with patch.object(pose_samples, 'load_frames', return_value=arrays), \
            patch.object(pose_samples, 'encode_frames', side_effect=encode):
        try:
            batch, audit = data.encode_layout_row(proc, copy.deepcopy(row), layout, None)
        except Exception as exc:
            return dict(refused=f'{type(exc).__name__}: {exc}')
    return dict(call=captured[0], audit=audit)


enc = {}
for pname, proc in processors.items():
    if not pname.endswith(':training_receipt'):
        continue
    for count in (32, 31, 16, 33):
        enc[f'{pname}:{count}'] = encode_capture(proc, row_for(count))
result['encode'] = enc


# --- carrier/marker insertion with a stub tokenizer ------------------------------------------
class StubTokenizer:
    def __init__(self, attrs):
        self.vocab = {VIDEO_TOKEN: 5, '<|vision_start|>': 6, '<|vision_end|>': 8, CARRIER_TOKEN: 7}
        self.__dict__.update(attrs)

    def convert_tokens_to_ids(self, token):
        return self.vocab[token]

    def encode(self, text, add_special_tokens=False):
        return [self.vocab[text]] if text in self.vocab else [100 + ord(c) for c in text]


def carriers(attrs, groups):
    ids = [1] + [t for _ in range(groups) for t in (6, 5, 8)] + [9, 10, 11]
    labels = [-100] * (len(ids) - 2) + [10, 11]
    batch = dict(input_ids=torch.tensor([ids]), attention_mask=torch.ones(1, len(ids), dtype=torch.long),
                 labels=torch.tensor([labels]), video_grid_thw=torch.tensor([[groups, 2, 2]]))
    try:
        out = data.insert_frame_carriers(batch, StubTokenizer(attrs), merge_size=2, carrier_placement=data.C1_A,
                                         frame_layout='duplicate')
    except Exception as exc:
        return dict(refused=f'{type(exc).__name__}: {exc}')
    return {k: (v.tolist() if torch.is_tensor(v) else v) for k, v in sorted(out.items())}


ins = {}
for pname, proc in processors.items():
    if not pname.endswith(':training_receipt'):
        continue
    attrs = {k: v for k, v in vars(proc.tokenizer).items()}
    for groups in (32, 16, 33):
        ins[f'{pname}:{groups}'] = carriers(attrs, groups)
result['carriers'] = ins
output.write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + '\n')
print(label, 'processor', len(result['processor']), 'admit', len(result.get('admit', {})), 'encode', len(enc),
      'carriers', len(ins))
