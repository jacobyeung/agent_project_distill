from collections import Counter, defaultdict
import re

import numpy as np
from scipy import ndimage

from trace_format.instance_policy314 import mask_floor, min_mask_px
from .row_removals import Removals


SCHEMA = "s1-ground-target-filter-v1"


def mask_quality(mask):
    mask = np.asarray(mask)
    if mask.dtype != np.bool_ or mask.ndim != 2 or min(mask.shape) < 1:
        raise ValueError("Target quality requires a two-dimensional boolean mask")
    area = int(mask.sum())
    components, _ = ndimage.label(mask)
    sizes = np.bincount(components.ravel())[1:]
    largest = int(sizes.max()) if len(sizes) else 0
    fraction = largest/area if area else 0.
    floor = mask_floor(mask.shape)
    reason = ("area_below_runtime_floor" if area < floor else
              "fragmented_mask" if fraction < .6 else None)
    return dict(accepted=reason is None, reason=reason, area=area, min_mask_px=floor,
                largest_component=largest, largest_component_fraction=fraction, connectivity=4)


def canonical_scene(row):
    scene = row.get('canonical') or row.get('provenance', {}).get('canonical') or row['scene']
    if '/' in scene:
        dataset, scene = scene.split('/', 1)
    else:
        dataset = row.get('dataset')
        if dataset is None and re.fullmatch(r'scene\d{4}_\d{2}', scene):
            dataset = 'scannet'
    dataset = {'d1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes'}.get(dataset, dataset)
    if dataset not in ('scannet', 'scannetpp', 'arkitscenes') or not scene or '/' in scene:
        raise ValueError("Grounding target removal requires a canonical physical scene")
    return f'{dataset}/{scene}'


def ignored_targets(source):
    values = source.get('ignored_targets', []) if isinstance(source, dict) else []
    if any(len(pair) != 2 or any(type(value) is not int for value in pair)
           or not 0 <= pair[0] < 32 or pair[1] < 0 for pair in values):
        raise ValueError("Invalid ignored grounding targets")
    return {tuple(pair) for pair in values}


def pointing_key(row):
    point = row['pointing']
    return point.get('row_key') or f"{canonical_scene(row)}|{point['frame']-1}|{point['instance_id']}"


class TargetFilter:
    def __init__(self, remove_files=(), *, shape_filter=False):
        if type(shape_filter) is not bool:
            raise ValueError("ground_target_filter must be boolean")
        self.removals = Removals(remove_files)
        self.shape_filter = shape_filter
        self.by_source = defaultdict(Counter)
        self.dropped_keys = set()
        self.extent_caught = set()

    def settings(self):
        return dict(schema=SCHEMA, removals=self.removals.files, shape_filter=self.shape_filter,
                    reference_min_mask_px=min_mask_px, reference_shape=[240, 320],
                    min_largest_component_fraction=.6, connectivity=4)

    def keep(self, mask, row_key, source):
        quality = mask_quality(mask) if self.shape_filter else None
        retained = self.removals.keep(dict(row_key=row_key))
        shape_bad = quality is not None and not quality['accepted']
        counts = self.by_source[str(source)]
        counts['targets_checked'] += 1
        counts['removed_by_list'] += int(not retained)
        counts['removed_by_shape'] += int(shape_bad)
        counts['targets_dropped'] += int(not retained or shape_bad)
        if shape_bad:
            counts[quality['reason']] += 1
            if row_key in self.removals.extent_only:
                self.extent_caught.add(row_key)
                counts['extent_only_shape_rejections'] += 1
        if not retained or shape_bad:
            self.dropped_keys.add(row_key)
        return retained and not shape_bad, quality

    def clip(self, source):
        from .grounding_targets import _raster
        _, _, inst, used, aggregation, _ = _raster(source)
        scene = canonical_scene(source)
        ignored = []
        for frame in np.flatnonzero(used):
            for instance in np.unique(inst[frame]):
                instance, frame = int(instance), int(frame)
                if instance < 0:
                    continue
                if instance not in aggregation:
                    raise ValueError("Target instance lacks a label")
                key = f'{scene}|{frame}|{instance}'
                keep, _ = self.keep(inst[frame] == instance, key,
                                    source.get('source_index', source.get('dataset', scene.split('/')[0])))
                if not keep:
                    ignored.append([frame, instance])
        return {**source, 'ignored_targets': ignored, 'ground_target_filter': self.settings()}

    def report(self):
        return dict(settings=self.settings(), removals=self.removals.report(),
                    by_source={key: dict(value) for key, value in self.by_source.items()},
                    unique_dropped_row_keys=len(self.dropped_keys),
                    extent_only_candidates=len(self.removals.extent_only),
                    extent_only_caught_by_shape=len(self.extent_caught))
