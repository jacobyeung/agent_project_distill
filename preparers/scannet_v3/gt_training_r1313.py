"""Fixed GT geometry/mask implementation; its only authority is a training-scene receipt."""
from __future__ import annotations
import threading
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
import numpy as np
from donor_grounding import REQ113GTGroundingProvider, GTGroundingError
from donor_geometry import Renderer
from frame_alignment import canonical_geometry
from gt_errors import UnmappedGroundingLabel
from gt_scene_assets import load_arrays, validate_dense, validate_scene, verify
from training_assets import load_scene


def donor_pin(spec):
    return dict(spec, bytes=spec['size_bytes'])


class TrainingGeometry:
    def __init__(self, receipt):
        self.receipt = receipt
        self.scene_id = receipt['runtime_scene_id']
        self.calibration = load_arrays(receipt['calibration'])
        self.row = {'dataset': 'scannetpp', 'instances': donor_pin(receipt['instances']),
                    'frames': [{'slot': index} for index in range(32)]}

    def _verify_scene(self, scene):
        if scene != self.scene_id:
            raise ValueError('scene is outside this authenticated training receipt')
        verify(self.receipt['instances'])
        return self.row

    def _pose(self, frame):
        return self.calibration['camera_poses'][frame['slot']].astype(np.float64)


class TrainingGrounding(REQ113GTGroundingProvider):
    def __init__(self, receipt):
        self.geometry = TrainingGeometry(receipt)
        scene = receipt['runtime_scene_id']
        self.scenes = {scene: self.geometry.row}
        self.grounding_assets = {scene: {'mesh': donor_pin(receipt['instance_mesh']),
                                       'annotations': donor_pin(receipt['annotations'])}}
        self._cache_masks = 256
        self._lock = threading.RLock()
        self._inventories = {}
        self._meshes = OrderedDict()
        self._cameras = OrderedDict()
        self._masks = OrderedDict()
        self._zbuffers = OrderedDict()

    def _camera(self, scene, frame_index):
        self.geometry._verify_scene(scene)
        if type(frame_index) is not int or not 1 <= frame_index <= 32:
            raise GTGroundingError('frame_index must be a 1-based selected RGB slot in 1..32')
        data = self.geometry.calibration
        height, width = data['raster_hw'].tolist()
        slot = frame_index - 1
        return data['camera_poses'][slot].astype(np.float64), data['intrinsics'][slot].astype(np.float64), height, width


@lru_cache(maxsize=2)
def _grounding(receipt_path, receipt_sha):
    from gt_scene_assets import read_json, sha
    if sha(receipt_path) != receipt_sha:
        raise ValueError('training scene receipt drift')
    return TrainingGrounding(validate_scene(read_json(receipt_path)))


def grounding_provider():
    import os
    load_scene()
    return _grounding(os.environ['R1313_SCENE_RECEIPT'], os.environ['R1313_SCENE_RECEIPT_SHA256'])


@lru_cache(maxsize=2)
def load_selected_dense(scene, point_cloud_source=None):
    receipt = load_scene()
    if scene != receipt['runtime_scene_id']:
        raise ValueError('unknown qualified training source scene')
    if point_cloud_source not in (None, 'g3t_scaled'):
        raise ValueError('r1313 binds GT geometry only; g3t_scaled is the compatibility alias, not a predicted fallback')
    data = validate_dense(load_arrays(receipt['dense']), receipt['frames'])
    data = canonical_geometry(data, receipt['gravity_up'])
    data['point_cloud_source'] = 'g3t_scaled'
    data['point_cloud_summary'] = 'authenticated training GT; meters; first-camera origin, +Z gravity up, +Y initial horizontal view, +X right; official K and GT-only support'
    for value in data.values():
        if isinstance(value, np.ndarray):
            value.flags.writeable = False
    return data


def segment_frame_request(scene_id, frame_index, label, mask_dir, score_thresh=0.3):
    try:
        return grounding_provider().segment_frame(scene_id, int(frame_index), label, Path(mask_dir))
    except UnmappedGroundingLabel as error:
        return error.refusal


def segment_video_request(scene_id, frame_indices, label, mask_dir, score_thresh=0.3, timeout=240.0):
    try:
        return grounding_provider().segment_video(scene_id, label, [int(i) for i in frame_indices], Path(mask_dir))
    except UnmappedGroundingLabel as error:
        return error.refusal
