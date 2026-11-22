"""STAB shared paths, registered sha256 values, loaders and joins (no score is read here).

Reused code (imported, not copied):
- lever6/k5b/kit/score_k5.py: authenticated, arms_from, split_records, pair (A1 vs D1 = arms 0, 2).
- cont_ops24_c/gbuild/gt/v2.py: alignment (the 2026-11-20 audit's rigid fit; gross = rotation_max_deg > 60).
- lever7/nfa/kit/score_nfa.py: item_score (the scoring that reproduces 171253's baselines 82.33/75.60/94.67/26.93).
"""
import hashlib
import json
import sys
from pathlib import Path

STAB = Path('/scratch/jjyeung/orch_n30/lever7/stab')
K5 = Path('/scratch/jjyeung/orch_n30/lever6/k5b')
GB = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild')
NFA = Path('/scratch/jjyeung/orch_n30/lever7/nfa')
J = NFA/'ref/ret/metadata/reads'

TYPES = ('camera_displacement', 'camera_rotation', 'camera_movement_direction', 'object_abs_distance')
DS = {'scannet': 'ScanNet', 'scannetppv2': 'ScanNet++', 'arkitscenes': 'ARKit'}
VOID_TAU = 3.9
EXCLUDED_FIT = ('arkitscenes/41254810',)   # rank 5 excluded it (DESIGN_STAB.md, Threshold)

# Registered inputs (FACTS_STAB.json, DESIGN_STAB.md); every one is checked before use.
REG = {
    'k5_reference': (K5/'kit/REFERENCE_K5.json', 'b570a994de0cb051f59c00e28b6d720d0a26c99c48d69c1d2aecbe164fbaf996'),
    'k5_g0': (K5/'ret/g0/50.json', 'ccc1f7e2c63f0868b6baf8c1ccdae00d974a230c8bd77904db965765a182afe5'),
    'k5_g1': (K5/'ret/g1/51.json', 'c086a16c1e045b18d76c365fda26fc13eb709c134a13864bc5c25dc57cdd11e9'),
    'score_k5': (K5/'kit/score_k5.py', '3ff86b25477339de7dd72a8136f5f40d8b209954a872601a0eb297e49a28eae3'),
    'gt_v2': (GB/'gt/v2.py', '42066b8b45c5bc4ead1149858100358003d83f7077ba3a3d2b713905ca8c9ff7'),
    'camera_split': (Path('/scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_t1/CAMERA_SPLIT.json'),
                     '453d7db15085a57f601fb88100873c9fa1faaa1f278cb5eeecad292345850c6d'),
    'k5s': (Path('/scratch/jjyeung/orch_n30/lever7/k5s/K5S.json'), 'd54b3ab1811c530117b1609c98e8a29ce5a6ab5bd705a4d7f8c040aa03fc7908'),
    'nogt_tar5': (Path('/scratch/jjyeung/orch_n30/lever1_c/arch5/nogt_gt15_20261120.tar'),
                  '9287ce416ae353db4d7d31ab60e310f0c2e2906d4c11b8dcf9456b2224594dd0'),
    'nogt_tar6': (Path('/scratch/jjyeung/orch_n30/lever1_c/arch6/nogt_arkit7_20261120.tar'),
                  '84098c02f033026c778bf9e3fb7191c77b5ad1a6b33a43405b09dce5effa03cc'),
    'items': (NFA/'ref/payload/items/devs1_routed.json', '2849206e3eb66f40b3e2fba49cfe84abe3c0465a318f85aaeaeca6ff6f26fe21'),
    'base_disp': (J/'0/metadata/journals/0/0/items.jsonl', '621b8503d78d956c6502bd402566daed01fd7e95c4703fa6e9bd69ba88232f81'),
    'base_rot': (J/'0/metadata/journals/1/0/items.jsonl', '9c181501231e3d460131d7ebc9b95b67354111c0a7a19034123c372bb1945b02'),
    'base_dir': (J/'0/metadata/journals/2/0/items.jsonl', 'dfd3cbba12623e6b98c524c4cac0113f74c16d795be7673fc27f2d2bdff04e06'),
    'base_dist_r0_null': (J/'0/metadata/journals/3/0/items.jsonl', '78a2781a06814516f836339fdde089e588d4299323de0025cc5bb5ebea1bd562'),
    'base_dist_r1_cand': (J/'1/metadata/journals/3/0/items.jsonl', 'd30aa74917ee66d0e023a7c7a2e5925386e9ae615a6fee775409610545f87bd5'),
    'own_cam_170631': (STAB/'banked/own/170631_items.jsonl', '9a74924a89badccbc30b8a9e59cae3d99ebedda3069a430a45b991ef1e25a81a'),
    'own_dist_170706': (STAB/'banked/own/170706_items.jsonl', '826385c63cd9f44e131733f83609c9e712714ac4a0f4513b37161cd7bf3a7a2a'),
    'direct_169526': (STAB/'banked/DIRECT_B2048_COMPACT.json', '0ece1ea5e9f04c50fad3060ee94b9867fc789dfcbf765d2f6040cff24ce98428'),
}
# score_nfa.py is still edited by the NF-A lane, so its item_score is pinned by function source, not by file
# (file sha 08c5ba6a... when this kit was written; item_score source unchanged in ca2bf291...).
ITEM_SCORE_SRC_SHA256 = '19e48d2c480d3f91c0fd0956b216038fcf404b99f290ba5b579291d013d3f243'
CAMGT_DIR = Path('/scratch/jjyeung/orch_n30/cont_ops25_c/cam/gt/t1_gt/gt')
TAU_JSON = STAB/'code/TAU.json'
TAU_SHA256 = '2d82d31fbb296d5158ca8c45d0540c8003727571581bfe32baad1eb8feacf282'   # TAU.json as reviewed (F2)
# Optional anchor-level frames of the direct read (from the e193c2a3c full return, not fetched): {item id: [32 source frame indices]}.
DIRECT_FRAMES = STAB/'banked/DIRECT_FRAMES.json'
BASE_FILE = {'camera_displacement': 'base_disp', 'camera_rotation': 'base_rot', 'camera_movement_direction': 'base_dir',
             'object_abs_distance': 'base_dist_r1_cand'}
SIDE_BASE = {'object_abs_distance': 'base_dist_r0_null'}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def verify(names, reg=REG):
    """sha256 of each named input; raises on any missing file or mismatch."""
    out = {}
    for n in names:
        p, want = reg[n]
        if not Path(p).is_file():
            raise FileNotFoundError('missing input %s: %s' % (n, p))
        got = sha(p)
        if got != want:
            raise ValueError('sha256 mismatch for %s: %s != %s' % (n, got, want))
        out[n] = dict(path=str(p), sha256=got, bytes=Path(p).stat().st_size)
    return out


def item_score_fn():
    """score_nfa.item_score, refused unless its source matches the pinned sha256."""
    import inspect
    imports()
    import score_nfa
    src = inspect.getsource(score_nfa.item_score)
    if hashlib.sha256(src.encode()).hexdigest() != ITEM_SCORE_SRC_SHA256:
        raise ValueError('score_nfa.item_score source changed')
    return score_nfa.item_score, dict(path=str(NFA/'kit/score_nfa.py'), file_sha256=sha(NFA/'kit/score_nfa.py'),
                                      item_score_source_sha256=ITEM_SCORE_SRC_SHA256)


def imports():
    for p in (K5/'kit', GB, NFA/'kit'):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))


def ds_of(scene):
    return DS[scene.split('/')[0]]


def jsonl(path):
    rows = []
    with Path(path).open() as f:
        for line in f:
            if not line.endswith('\n'):
                raise ValueError('incomplete jsonl tail: %s' % path)
            rows.append(json.loads(line))
    return rows


def load_items(reg=REG):
    items = json.loads(Path(reg['items'][0]).read_text())['items']
    by = {}
    for it in items:
        if it['id'] in by:
            raise ValueError('duplicate item id')
        by[it['id']] = it
    return by


def type_ids(items, kind):
    return sorted(i for i, it in items.items() if it['question_type'] == kind)


def keyed(rows, what):
    out = {}
    for r in rows:
        if r['id'] in out:
            raise ValueError('%s: duplicate id %s' % (what, r['id']))
        out[r['id']] = r
    return out


def load_arm_rows(reg=REG):
    """Rows per (arm, type) keyed by item id. Arms: base, side (distance read 0), own, direct. No score is touched."""
    arms = {'base': {}, 'side': {}, 'own': {}, 'direct': {}}
    for kind, name in BASE_FILE.items():
        arms['base'][kind] = keyed(jsonl(reg[name][0]), name)
    for kind, name in SIDE_BASE.items():
        arms['side'][kind] = keyed(jsonl(reg[name][0]), name)
    own = [r for r in jsonl(reg['own_cam_170631'][0]) + jsonl(reg['own_dist_170706'][0]) if r['mode'] == 'none']
    for kind in TYPES:
        arms['own'][kind] = keyed([r for r in own if r['type'] == kind], 'own '+kind)
    direct = json.loads(Path(reg['direct_169526'][0]).read_text())
    for kind in TYPES:
        arms['direct'][kind] = keyed([r for r in direct if r['question_type'] == kind], 'direct '+kind)
    return arms


def join(items, arms):
    """Refuse any missing or extra key; check type and room against the item file. Returns join counts."""
    out = {}
    for arm, per in arms.items():
        for kind, rows in per.items():
            want = set(type_ids(items, kind))
            have = set(rows)
            if want - have:
                raise KeyError('%s %s: %d missing keys, e.g. %s' % (arm, kind, len(want-have), sorted(want-have)[:3]))
            if have - want:
                raise KeyError('%s %s: %d extra keys, e.g. %s' % (arm, kind, len(have-want), sorted(have-want)[:3]))
            for i in want:
                r, it = rows[i], items[i]
                if arm == 'direct':
                    if r['question_type'] != kind or r['room'] != it['room']:
                        raise ValueError('direct %s: type or room differs for %s' % (kind, i))
                else:
                    if r['type'] != kind or r['room_key'] != it['room_key']:
                        raise ValueError('%s %s: type or room differs for %s' % (arm, kind, i))
            out['%s|%s' % (arm, kind)] = len(want)
    return out


FRAME_KEYS = ('layout', 'count', 'matches_training')


def frame_checks(items, arms, direct_frames=None):
    """Frame equality before any score.
    base/side/own: each row's output.frames (layout, count, matches_training) equals the baseline row's and
    output.key == 'devrows:'+id. direct: the compact row's native capture equals the item's native capture
    (capture level); anchor level only if direct_frames ({id: indices}) is given. Raises on any inequality."""
    out = {}
    for kind in TYPES:
        ref = {i: {k: r['output']['frames'].get(k) for k in FRAME_KEYS} for i, r in arms['base'][kind].items()}
        for arm in ('base', 'side', 'own'):
            if kind not in arms[arm]:
                continue
            n = 0
            for i, r in arms[arm][kind].items():
                f = {k: r['output']['frames'].get(k) for k in FRAME_KEYS}
                if f != ref[i] or f['count'] != 32 or r['output'].get('key') != 'devrows:'+i:
                    raise ValueError('frames differ: %s %s %s' % (arm, kind, i))
                n += 1
            out['%s|%s' % (arm, kind)] = dict(equal=n, layouts=sorted({str(v['layout']) for v in ref.values()}))
        n = 0
        anchors = 0
        for i, r in arms['direct'][kind].items():
            if r['native'] != items[i]['native'] or r['key'] != 'devrows:'+i:
                raise ValueError('direct capture differs: %s %s' % (kind, i))
            n += 1
            if direct_frames is not None:
                if direct_frames.get(i) != items[i]['source_frame_indices']:
                    raise ValueError('direct anchors differ: %s %s' % (kind, i))
                anchors += 1
        out['direct|%s' % kind] = dict(capture_equal=n, anchor_equal=anchors if direct_frames is not None else None)
    out['direct_anchor_level'] = 'checked' if direct_frames is not None else 'unchecked: needs the e193c2a3c full return (39.7 MB, IO governor)'
    return out
