from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np
from arkit_source import DATASET, match_timestamp, parse_intrinsic, parse_trajectory, timestamp, timestamped_files, timeline_rows, timeline_sha
from gt_scene_assets import pin, read_json, verify

MAP_SCHEMA = 'r1313-arkit-frame-map-v1'
MIN_CORRELATION = 0.99
MAX_MAE = 8.0
MAP_KEYS = {'schema', 'dataset', 'scene_name', 'video', 'source_frames_receipt', 'source_stream',
            'mapping_basis', 'mapping_authority', 'source_timeline_sha256', 'source_frame_count', 'resize', 'frames'}


def selected_camera_alignment(sequence, scene, frames_path, correspondence_path):
    sequence = Path(sequence)
    frames_pin, correspondence_pin = pin(frames_path), pin(correspondence_path)
    frames = read_json(verify(frames_pin))
    mapping = read_json(verify(correspondence_pin))
    if frames.get('dataset') != DATASET or frames.get('scene_name') != scene:
        raise ValueError('frame receipt does not bind the requested ARKitScenes source')
    selected = frames.get('frames', [])
    if len(selected) != 32 or [item.get('stem') for item in selected] != frames.get('selected_frames'):
        raise ValueError('exactly32 selected RGB frames and stems are required')
    ordinals = [item.get('ordinal') for item in selected]
    if any(type(ordinal) is not int for ordinal in ordinals) or sorted(set(ordinals)) != ordinals or ordinals[0] < 0:
        raise ValueError('selected VSI ordinals must be unique, nonnegative, and increasing')
    if set(mapping) != MAP_KEYS or mapping.get('schema') != MAP_SCHEMA or (mapping.get('dataset'), mapping.get('scene_name')) != (DATASET, scene):
        raise ValueError('correspondence schema or source identity mismatch')
    if mapping['source_frames_receipt'] != frames_pin:
        raise ValueError('correspondence does not bind the exact frame receipt')
    video = verify(frames['video'])
    if mapping['video'] != pin(video):
        raise ValueError('correspondence does not bind the exact VSI video')
    authority = verify(mapping['mapping_authority'])
    if not authority.stat().st_size or mapping['source_stream'] != 'lowres_wide':
        raise ValueError('explicit export authority and lowres_wide source stream are required')
    if mapping['mapping_basis'] not in ('equal_ordinal_export', 'explicit_timestamp_map'):
        raise ValueError('unsupported source correspondence basis')
    source = timestamped_files(sequence / 'lowres_wide', scene, '.png')
    if mapping['source_timeline_sha256'] != timeline_sha(source) or mapping['source_frame_count'] != len(source):
        raise ValueError('source RGB timeline census drift')
    joins = mapping['frames']
    if not isinstance(joins, list) or len(joins) != 32 or any(set(row) != {'vsi_ordinal', 'source_ordinal', 'source_timestamp'} for row in joins):
        raise ValueError('correspondence must contain exactly32 explicit ordinal/timestamp joins')
    source_ordinals = [row['source_ordinal'] for row in joins]
    if any(type(value) is not int for value in source_ordinals) or sorted(set(source_ordinals)) != source_ordinals or source_ordinals[0] < 0 or source_ordinals[-1] >= len(source):
        raise ValueError('source joins must be unique increasing ordinals inside the RGB census')
    if any(type(row['vsi_ordinal']) is not int for row in joins):
        raise ValueError('VSI correspondence ordinals must be integers, not booleans or floats')
    if [row['vsi_ordinal'] for row in joins] != ordinals:
        raise ValueError('correspondence and selected VSI ordinals differ')
    trajectory_path = sequence / 'lowres_wide.traj'
    trajectory_pin = pin(trajectory_path)
    poses_by_time = parse_trajectory(trajectory_path)
    intrinsics_by_time = timestamped_files(sequence / 'lowres_wide_intrinsics', scene, '.pincam')
    raw_pins = {'lowres_wide.traj': trajectory_pin}
    video_capture = cv2.VideoCapture(str(video))
    try:
        if not video_capture.isOpened():
            raise ValueError('VSI video cannot be decoded')
        count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = float(video_capture.get(cv2.CAP_PROP_FPS))
        if count != frames['video'].get('decoded_frame_count') or count <= ordinals[-1] or not np.isfinite(fps) or fps <= 0 or not np.isclose(fps, frames['video'].get('fps', -1), atol=1e-6, rtol=0):
            raise ValueError('VSI video count or timebase does not match the frame receipt')
        if mapping['mapping_basis'] == 'equal_ordinal_export' and (count != len(source) or source_ordinals != ordinals):
            raise ValueError('equal-ordinal export requires identical full counts and ordinals')
        poses, intrinsics, rows, rgb = [], [], [], []
        raster_hw = None
        for slot, (item, join) in enumerate(zip(selected, joins)):
            ordinal = item['ordinal']
            if item['stem'] != f'frame_{ordinal:06d}':
                raise ValueError('selected frame stem does not encode its VSI ordinal')
            official_frame = source[join['source_ordinal']]
            if join['source_timestamp'] != official_frame['timestamp']:
                raise ValueError('source ordinal and literal timestamp disagree')
            wanted = timestamp(join['source_timestamp'])
            pose_row = match_timestamp(poses_by_time, wanted, 'pose')
            intrinsic_row = match_timestamp(intrinsics_by_time, wanted, 'intrinsics')
            source_pin, intrinsic_pin = pin(official_frame['path']), pin(intrinsic_row['path'])
            original = cv2.imread(str(verify(source_pin, prepared=False)), cv2.IMREAD_UNCHANGED)
            selected_rgb = cv2.imread(str(verify(item)), cv2.IMREAD_UNCHANGED)
            if any(image is None or image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3 for image in (original, selected_rgb)):
                raise ValueError('selected source/VSI PNG must be decodable uint8 three-channel RGB')
            if not video_capture.set(cv2.CAP_PROP_POS_FRAMES, ordinal):
                raise ValueError('VSI video ordinal seek failed')
            ok, decoded = video_capture.read()
            if not ok or abs(video_capture.get(cv2.CAP_PROP_POS_FRAMES) - ordinal - 1) > 0.1 or not np.array_equal(decoded, selected_rgb):
                raise ValueError('authenticated selected PNG differs from its VSI video ordinal')
            source_k, source_hw = parse_intrinsic(verify(intrinsic_pin, prepared=False))
            if original.shape[:2] != source_hw or source_hw != (192, 256):
                raise ValueError('lowres_wide PNG/pincam canvas must agree at256x192')
            sh, sw = source_hw
            vh, vw = selected_rgb.shape[:2]
            if vw * sh != vh * sw or min(vh, vw) <= 0:
                raise ValueError('only aspect-preserving source RGB resize is supported')
            resize = mapping['resize']
            if resize == 'identity' and (vh, vw) == source_hw:
                resized = original
            elif resize == 'area' and vh <= sh and vw <= sw:
                resized = cv2.resize(original, (vw, vh), interpolation=cv2.INTER_AREA)
            elif resize == 'linear' and vh >= sh and vw >= sw:
                resized = cv2.resize(original, (vw, vh), interpolation=cv2.INTER_LINEAR)
            else:
                raise ValueError('source resize declaration is incompatible with the selected canvas')
            if raster_hw is not None and raster_hw != (vh, vw):
                raise ValueError('selected RGB canvases differ')
            if any(np.std(image.reshape(-1, 3).astype(np.float64), axis=0).max() < 1e-6 for image in (resized, selected_rgb)):
                raise ValueError('source RGB correlation is undefined for a spatially constant image')
            correlation = float(np.corrcoef(resized.reshape(-1), selected_rgb.reshape(-1))[0, 1])
            mae = float(np.abs(resized.astype(np.float64) - selected_rgb).mean())
            if not np.isfinite(correlation) or correlation < MIN_CORRELATION or mae > MAX_MAE:
                raise ValueError(f'source/VSI frame correlation or MAE failed at slot {slot + 1}: correlation={correlation:.6f}, mae={mae:.3f}')
            scale = np.diag([vw / sw, vh / sh, 1.0])
            target_k = scale @ source_k
            pose = pose_row['pose']
            rows.append({'slot_1based': slot + 1, 'ordinal': ordinal, 'stem': item['stem'],
                         'vsi_timestamp_sec': ordinal / fps, 'source_ordinal': join['source_ordinal'],
                         'source_timestamp': join['source_timestamp'], 'source_rgb': source_pin,
                         'source_intrinsics_file': intrinsic_pin, 'pose_line_1based': pose_row['line_1based'],
                         'pose_timestamp': pose_row['timestamp'], 'intrinsics_timestamp': intrinsic_row['timestamp'],
                         'pose_timestamp_delta_sec': float(pose_row['time'] - wanted),
                         'intrinsics_timestamp_delta_sec': float(intrinsic_row['time'] - wanted),
                         'world_to_camera_axis_angle_translation': pose_row['world_to_camera_axis_angle_translation'],
                         'raw_source_canvas_wh': [sw, sh], 'vsi_canvas_wh': [vw, vh], 'target_canvas_wh': [vw, vh],
                         'source_intrinsic': source_k.tolist(), 'source_to_vsi': scale.tolist(),
                         'vsi_to_target_resize_crop': np.eye(3).tolist(), 'crop_xyxy': [0, 0, vw, vh],
                         'target_intrinsic': target_k.tolist(), 'aligned_pose': pose.tolist(),
                         'raw_to_vsi_correlation': correlation, 'raw_to_vsi_mae': mae,
                         'selected_png_matches_vsi_decode': True, 'selected_rgb_sha256': item['sha256']})
            poses.append(pose)
            intrinsics.append(target_k)
            rgb.append(selected_rgb)
            raster_hw = (vh, vw)
            raw_pins[str(official_frame['path'].relative_to(sequence))] = source_pin
            raw_pins[str(intrinsic_row['path'].relative_to(sequence))] = intrinsic_pin
        evidence = {'source_frames_receipt': frames_pin, 'correspondence': correspondence_pin,
                    'mapping_authority': mapping['mapping_authority'], 'mapping_basis': mapping['mapping_basis'],
                    'source_timeline_sha256': timeline_sha(source), 'source_timeline': timeline_rows(source),
                    'resize': mapping['resize'], 'correlation_minimum': MIN_CORRELATION, 'mae_maximum': MAX_MAE,
                    'timestamp_tolerance_sec': 0.001}
        return frames, np.asarray(poses, dtype=np.float32), np.asarray(intrinsics, dtype=np.float32), raster_hw, rows, rgb, raw_pins, evidence
    finally:
        video_capture.release()
