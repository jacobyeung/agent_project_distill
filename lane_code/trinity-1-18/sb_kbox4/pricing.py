"""CPU GT-mask pricing primitives using the copied reader and deployed Session."""
import re
import numpy as np
from box_math import fusion_box, first_seen


def lift_frames(name, masks, geo, G):
    """Compute each frame's own bestspread points, retaining its original area."""
    out = dict(name=name, seen=False, frames=[], visible=[], areas={}, points={})
    for f, mask in enumerate(np.asarray(masks, bool), 1):
        if not mask.any() or not geo.has(f):
            continue
        out['visible'].append(f)
        out['areas'][str(f)] = float(mask.mean())
        P, Pc, sp = (np.asarray(x, np.float64) for x in geo.lift(f, G.mask_pixels(mask), mode='center'))
        keep = np.isfinite(P).all(1) & np.isfinite(Pc).all(1) & (Pc[:, 2] > 0)
        if keep.any():
            P, sp = P[keep], sp[keep]
            out['frames'].append(f)
            out['points'][str(f)] = P[sp <= np.median(sp)]
    if out['frames']:
        out['seen'] = True
        out['best'] = min(out['frames'], key=lambda f: (-out['areas'][str(f)], f))
    return out


def session_distance(row, geo, lifted, G, rule='best1', plain=False):
    from trace_format.ground_v313 import Session
    from trace_format.box_v313 import in_f1
    from student_pilot import ground_lifting
    raw_boxes = {}
    class Provider:
        provider_id = 'box_ladder_' + rule + ('_plain' if plain else '')
        def __call__(self, name, obj, geometry, best):
            if 'boxes' in obj:
                if rule not in obj['boxes']:
                    obj['boxes'][rule] = fusion_box(obj['points'], obj['best'], rule, G.min_area_box)
                raw = obj['boxes'][rule]
            elif plain:
                raw = G.min_area_box(np.concatenate(list(obj['points'].values())))
            else:
                raw = fusion_box(obj['points'], obj['best'], rule, G.min_area_box)
            raw_boxes[name] = raw
            return in_f1(geometry, raw['centroid'], raw['axesLengths'], raw['normalizedAxes'])
    class S(Session):
        def __init__(self):
            super().__init__(ground_lifting, geo, None, instances=lambda name: (),
                program_version='3.14', multi_instance=True, geometry_mode='sensor', box_provider=Provider())
        def _instances(self, name):
            obj = lifted[name]
            return [dict(obj, instance_id=str(row['gt_instances'].get(name, name)),
                         first=min(obj['frames']))] if obj['seen'] else []
    s = S()
    for name in row['operands']:
        s.execute(f'<ground obj="{name}" mode="box">')
    a, b = row['operands']
    response = s.execute(f'<gap a="{a}" b="{b}" rule="box_grid_5cm">')
    match = re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m', response)
    printed = {name: s.box_registry.records[labels[0]]['value'] for name, labels in s.box_registry.bindings.items() if len(labels) == 1}
    return (float(match[1]) if match else None), (None if match else response), raw_boxes, printed


def object_diagnostics(masks, obj, printed_box=None, gt_box=None):
    result = dict(frames=list(obj['frames']), **first_seen(masks, obj['frames']))
    result['printed_longest_edge'] = float(max(printed_box['lengths'])) if printed_box else None
    result['size_ratio'] = None
    result['size_mra'] = None
    result['size_status'] = 'MISSING: per-instance full-extent GT boxes not loaded'
    if gt_box is not None and gt_box['status'] in ('half', 'full'):
        from box_math import mra
        longest = float(max(gt_box['box']['axesLengths'])) * (2 if gt_box['status']=='half' else 1)
        result['gt_longest_edge'] = longest
        result['size_ratio'] = result['printed_longest_edge']/longest if result['printed_longest_edge'] is not None else None
        result['size_mra'] = mra(result['printed_longest_edge'],longest)
        result['size_status'] = 'OK'
    return result
