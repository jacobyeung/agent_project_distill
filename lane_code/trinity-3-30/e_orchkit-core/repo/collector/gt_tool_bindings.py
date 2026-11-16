"""Literal training-GT routes over the donor's scene-only perception primitives."""
from __future__ import annotations
import hashlib
import json
import os
import time
from functools import wraps
from pathlib import Path
import numpy as np
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from gt_errors import UnmappedGroundingLabel
from gt_scene_assets import data_path
from gt_training_r1313 import grounding_provider, load_selected_dense, segment_frame_request, segment_video_request

GT_TOOL_NAMES = ('find_frames_with_object', 'predict_2d_bounding_box', 'predict_2d_points',
                 'predict_2d_segmentation_masks', 'predict_2d_segmentation_masks_video')


def observation(function):
    @wraps(function)
    def measured(*args, **kwargs):
        start = time.monotonic_ns()
        try:
            result = function(*args, **kwargs)
        except UnmappedGroundingLabel as error:
            result = error.refusal
        config = kwargs.get('config') or {}
        sink = config.get('configurable', {}).get('trace_list')
        if sink is not None:
            sink.append({'event': 'gt_perception', 'tool': function.__name__,
                         'provider': 'authenticated_training_scene_gt',
                         'scene_receipt_sha256': os.environ['R1313_SCENE_RECEIPT_SHA256'],
                         'status': 'refused' if isinstance(result, dict) and result.get('error') else 'ok',
                         'started_monotonic_ns': start, 'ended_monotonic_ns': time.monotonic_ns(),
                         'response': json.dumps(result, sort_keys=True, allow_nan=False)})
        return result
    return measured


def check_frame(frame_index):
    if type(frame_index) is not int or not 1 <= frame_index <= 32:
        raise ValueError('frame_index must be a 1-based selected RGB slot in 1..32')


def mask_dir(scene, label, frames):
    key = hashlib.sha256(json.dumps([scene, label, frames], separators=(',', ':')).encode()).hexdigest()
    return data_path(os.environ['REQ73_RUN_OUTPUT_ROOT']) / 'runtime' / 'gt_masks' / key


def enrich(instances, scene, frame_index):
    provider = grounding_provider()
    height, width = provider.geometry.calibration['raster_hw'].tolist()
    for item in instances:
        mask = np.load(data_path(item['mask_handle']), allow_pickle=False)
        if mask.dtype != np.bool_ or mask.shape != (height, width):
            raise ValueError('GT mask differs from the authenticated geometry/RGB canvas')
        edges = [bool(mask[0].any()), bool(mask[-1].any()), bool(mask[:, 0].any()), bool(mask[:, -1].any())]
        item.update(mask_dense_handle=item['mask_handle'], mask_dense_shape=[height, width],
                    mask_edges_touched=sum(edges),
                    mask_truncation_warning='visible mask touches a vertical image boundary' if any(edges[:2]) else None)
    return instances


@tool
@observation
def find_frames_with_object(scene_id: str, object_label: str, config: RunnableConfig, num_frames: str = '5') -> list:
    """Find selected frames with visible annotated instances, without a VLM.

    Args:
        scene_id: Qualified source scene ID from the question header.
        object_label: Object category or a label from an unmapped-label refusal.
        num_frames: Count or 'all'; donor selection always preserves first/last visible slots, even for '1'.
    Returns:
        Sorted 1-based slots in 1..32, [] when not visible, or a typed label refusal.
    """
    return grounding_provider().find_frames(scene_id, object_label, num_frames)


@tool
@observation
def predict_2d_bounding_box(scene_id: str, frame_index: int, object_label: str, config: RunnableConfig) -> list:
    """Return the donor's visible-instance GT boxes, with source-world occlusion.

    Args:
        scene_id: Qualified source scene ID from the question header.
        frame_index: 1-based selected slot in 1..32, as returned by frame search.
        object_label: Object category or a label from an unmapped-label refusal.
    Returns:
        Boxes [xmin,ymin,xmax,ymax] normalized by image width/height; [] if not visible.
    """
    check_frame(frame_index)
    return grounding_provider().boxes(scene_id, frame_index, object_label)


@tool
@observation
def predict_2d_points(scene_id: str, frame_index: int, query: str, config: RunnableConfig,
                      point_cloud_source: str = 'g3t_scaled') -> list:
    """Return visible-instance box centers from the donor, lifted through GT geometry.

    Args:
        scene_id: Qualified source scene ID from the question header.
        frame_index: 1-based selected slot in 1..32.
        query: Annotated object category; arbitrary landmarks/edges are not supported.
        point_cloud_source: 'g3t_scaled' is the sole compatibility alias for authenticated GT, not a predicted source.
    Returns:
        Instance IDs, labels, pixel_norm [x,y], and world [X,Y,Z] in meters; +Z up, +Y initial view, camera0 origin. An invalid pixel uses the nearest GT-valid pixel, matching the carrier lookup.
    """
    check_frame(frame_index)
    rows = grounding_provider().points(scene_id, frame_index, query)
    dense = load_selected_dense(scene_id, point_cloud_source)
    mask = dense['mask'][frame_index - 1]
    height, width = mask.shape
    result = []
    for row in rows:
        x, y = row['pixel_norm']
        px, py = min(width - 1, max(0, int(x * width))), min(height - 1, max(0, int(y * height)))
        if not mask[py, px]:
            ys, xs = np.where(mask)
            nearest = np.argmin((ys - py) ** 2 + (xs - px) ** 2)
            py, px = int(ys[nearest]), int(xs[nearest])
        point = dense['pts3d_world'][frame_index - 1, py, px]
        result.append(dict(row, world=[round(float(v), 4) for v in point], point_cloud_source='g3t_scaled'))
    return result


@tool
@observation
def predict_2d_segmentation_masks(scene_id: str, frame_index: int, object_label: str,
                                  config: RunnableConfig = None) -> list:
    """Project annotated training instances with the donor's occlusion-tested GT masks; no SAM3.

    Args:
        scene_id: Qualified source scene ID from the question header.
        frame_index: 1-based selected slot in 1..32.
        object_label: Object category or a label from an unmapped-label refusal.
    Returns:
        Visible instance IDs, score=1 (annotation indicator), normalized/pixel boxes, area, and immutable boolean mask handles. mask_dense_handle uses the same [H,W] canvas as GT points and selected RGB; dimensions are explicit in mask_dense_shape.
    """
    check_frame(frame_index)
    payload = grounding_provider().segment_frame(scene_id, frame_index, object_label, mask_dir(scene_id, object_label, [frame_index]))
    return enrich(payload['instances'], scene_id, frame_index)


@tool
@observation
def predict_2d_segmentation_masks_video(scene_id: str, object_label: str, frame_indices: list[int],
                                        config: RunnableConfig = None) -> dict:
    """Project donor GT masks across selected frames; annotation IDs persist across frames.

    Args:
        scene_id: Qualified source scene ID from the question header.
        object_label: Object category or a label from an unmapped-label refusal.
        frame_indices: Nonempty unique 1-based selected slots in 1..32.
    Returns:
        frames maps slots to masks in the single-frame schema; frame_size=[W,H], visible-ID union/peak counts, and per-ID visibility frequencies describe only requested frames.
    """
    if not frame_indices or len(set(frame_indices)) != len(frame_indices):
        raise ValueError('frame_indices must be nonempty and unique')
    for frame in frame_indices:
        check_frame(frame)
    payload = grounding_provider().segment_video(scene_id, object_label, frame_indices, mask_dir(scene_id, object_label, frame_indices))
    persistence = {}
    for frame, instances in payload['frames'].items():
        enrich(instances, scene_id, frame)
        for instance in instances:
            iid = instance['instance_id']
            persistence[iid] = persistence.get(iid, 0) + 1
    payload.update(instance_persistence=persistence, n_unique_instances=len(persistence),
                   max_instances_in_any_frame=max(map(len, payload['frames'].values()), default=0),
                   n_significant_instances=sum(count >= 3 for count in persistence.values()))
    return payload


def dense_lookup(scene_id, point_cloud_source=None):
    return load_selected_dense(scene_id, point_cloud_source)


def bind_gt_tools(module):
    module._load_dense = dense_lookup
    module._load_ransac_dense = dense_lookup
    module._run_sam3_request = segment_frame_request
    module._run_sam3_video_request = segment_video_request
    for name in GT_TOOL_NAMES:
        setattr(module, name, globals()[name])
    module._POINT_CLOUD_SOURCES = {'g3t_scaled': {'dense_dir': str(data_path(os.environ['R1313_SCENE_RECEIPT']).parent),
        'summary': 'authenticated training GT; official aligned cameras; meters, +Z up, +Y initial view'}}


def assert_bindings(module, tools):
    by_name = {item.name: item for item in tools}
    if any(by_name.get(name) is not globals()[name] for name in GT_TOOL_NAMES):
        raise RuntimeError('GT perception route drift before native tool binding')
    if module._load_dense is not dense_lookup or module._load_ransac_dense is not dense_lookup:
        raise RuntimeError('GT geometry route drift before native tool binding')
