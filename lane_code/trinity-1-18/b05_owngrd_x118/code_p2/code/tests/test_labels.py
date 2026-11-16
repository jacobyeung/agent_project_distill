import numpy as np

from owngrd.common import rle_encode
from owngrd.labels import triage_capture, triage_frame


def box(h, w, y0, y1, x0, x1):
    m = np.zeros((h, w), bool)
    m[y0:y1, x0:x1] = True
    return m


def prop(mask2x, joint, score=0.9):
    return {'joint_score': joint, 'score': score, 'mask': rle_encode(mask2x), 'query': 0, 'box': [0, 0, 1, 1]}


def up(m):
    return np.kron(m, np.ones((2, 2), bool))


H, W = 24, 32
INST = -np.ones((H, W), np.int32)
INST[2:10, 2:10] = 0      # chair
INST[12:20, 2:10] = 1     # nightstand
INST[12:20, 20:30] = 2    # sofa
ID_NAME = {0: 'chair', 1: 'nightstand', 2: 'sofa'}


def test_classes():
    preds = {
        'chair': {'presence': 0.9, 'instances': [prop(up(box(H, W, 2, 10, 2, 10)), 0.8),
                                                   prop(up(box(H, W, 12, 20, 20, 30)), 0.3),
                                                   prop(up(box(H, W, 0, 2, 12, 32)), 0.7)]},
        'cabinet': {'presence': 0.6, 'instances': [prop(up(box(H, W, 12, 20, 2, 10)), 0.6)]},
        'sofa': {'presence': 0.1, 'instances': []},
        'table': {'presence': 0.05, 'instances': []},
        'lamp': {'presence': 0.9, 'instances': [prop(up(box(H, W, 0, 2, 12, 32)), 0.9)]},
    }
    r = triage_frame(INST, True, ID_NAME, preds, 'scannet', set(ID_NAME.values()))
    c = r['chair']
    assert [p['cls'] for p in c['proposals']] == ['POS', 'HARDNEG', 'DISPUTED']
    assert c['presence'] == 1 and c['pos_inst'] == [0] and c['miss'] == []
    assert c['proposals'][1]['selection_only'] is False and c['proposals'][1]['weight'] == 1.0
    cab = r['cabinet']['proposals'][0]
    assert cab['cls'] == 'HARDNEG' and cab['selection_only'] and cab['weight'] == 0.25
    assert r['sofa']['presence'] is None and r['sofa']['why'] == 'miss' and r['sofa']['miss'] == [2]
    assert r['table']['presence'] == 0 and r['table']['why'] == 'absent'
    assert r['lamp']['presence'] is None and r['lamp']['why'] == 'disputed_absent'


def test_low_iou_and_low_joint_are_distill():
    preds = {'chair': {'presence': 0.9, 'instances': [prop(up(box(H, W, 2, 10, 2, 4)), 0.9),
                                                        prop(up(box(H, W, 2, 10, 2, 10)), 0.4)]}}
    r = triage_frame(INST, True, ID_NAME, preds, 'scannet', set())
    assert [p['cls'] for p in r['chair']['proposals']] == ['DISTILL', 'DISTILL']
    assert r['chair']['presence'] is None and r['chair']['miss'] == [0]


def test_arkit_absence_only_for_annotated_classes_and_invalid_frames():
    preds = {'pillow': {'presence': 0.01, 'instances': []}, 'stove': {'presence': 0.01, 'instances': []}}
    r = triage_frame(INST, True, ID_NAME, preds, 'arkitscenes', set())
    assert r['pillow']['presence'] is None and r['pillow']['why'] == 'not_annotatable'
    assert r['stove']['presence'] == 0
    r = triage_frame(INST, False, ID_NAME, preds, 'scannet', set())
    assert all(v['presence'] is None and v['why'] == 'invalid_frame' for v in r.values())


def test_sliver_no_presence():
    inst = INST.copy()
    inst[22:23, 30:32] = 3
    r = triage_frame(inst, True, {**ID_NAME, 3: 'cup'}, {'cup': {'presence': 0.01, 'instances': []}}, 'scannet', set())
    assert r['cup']['presence'] is None and r['cup']['why'] == 'sliver'


class Z(dict):
    pass


def test_capture_level_and_size_check():
    z = {'inst': np.stack([INST, INST]), 'valid': np.array([True, True]), 'ids': np.array([0, 1, 2]),
         'labels': np.array(['chair', 'nightstand', 'sofa']), 'frame_indices': np.array([0, 5])}
    fr = lambda: {'size': [2 * H, 2 * W], 'phrases': {'chair': {'presence': 0.9, 'instances': [prop(up(box(H, W, 2, 10, 2, 10)), 0.8)]},
                                                       'table': {'presence': 0.01, 'instances': []}}}
    t = {'frame_indices': [0, 5], 'frame_slots': [0, 1], 'phrases': ['chair', 'table'], 'frames': {'0': fr(), '1': fr()}}
    lab = triage_capture(t, z, 'scannet/scene0000_00', {'chair': 'gt', 'table': 'absent'})
    assert lab['clip_presence'] == {'chair': 1, 'table': 0}
    t['frames']['1']['size'] = [H, W]
    try:
        triage_capture(t, z, 'scannet/scene0000_00', {})
        raise AssertionError('size mismatch accepted')
    except ValueError:
        pass
