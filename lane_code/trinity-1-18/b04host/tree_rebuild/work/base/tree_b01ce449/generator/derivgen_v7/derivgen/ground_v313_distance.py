"""Box-distance integration for the v5 review builder; directions use its legacy path."""
import numpy as np

from . import box_v313 as boxes
from .ground_v313 import Session, GTInstances
from .ground_v312 import RowRefusal, replay


def prepare(item, clip, rule=boxes.RULE, multi_instance=False):
    """v3.14 (multi_instance=True): every instance of an operand name enters, as one entry per instance; the
    benchmark label is the minimum over instance pairs. v3.13 keeps the single-instance requirement."""
    from .ground_v312_io import operands
    from .ground_v312_quality import normalized
    item['trace_revision'] = '3.13' if rule == boxes.RULE and not multi_instance else '3.14'
    item['target_distance_rule'] = rule
    item['independent_ordered_boxes'] = []
    for name in operands(item):
        ids = [int(i) for i, label in zip(clip.geo.ids, clip.geo.labels)
               if normalized(label) == normalized(name)]
        if not ids or (len(ids) != 1 and not multi_instance) or len(ids) > boxes.MAX_INSTANCES:
            raise RowRefusal('single_instance_required' if not multi_instance else 'instance_count_unsupported')
        for iid in ids:
            raw = clip.geo.obb[iid]
            item['independent_ordered_boxes'].append(dict(
                name=name, instance_id=iid,
                **{k: np.asarray(raw[k], dtype=np.float64).tolist()
                   for k in ('centroid', 'axesLengths', 'normalizedAxes')}))


def make_session(backend, clip, misses, provider, multi_instance=False, instances=None):
    return Session(backend, clip.geo, clip.masks, instances=instances or GTInstances(clip),
                   simulated_misses=misses, box_provider=provider, multi_instance=multi_instance)


def replay_exact(row, session):
    replay(row, session)
    if row['events'] != session.events:
        raise RowRefusal('replay_audit_mismatch')
    return boxes.replay_audit(row['events'])


def agrees(answer, gt):
    return (str(answer) == boxes.number(float(gt), 2)
            and abs(float(answer)-float(gt)) <= .05*abs(float(gt)))
