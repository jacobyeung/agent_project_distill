import math
def layout_settings(cfg):
    layout, gap = cfg.get('frame_layout', 'spread'), cfg.get('frame_pair_gap_seconds')
    if layout not in ('spread', 'duplicate', 'paired'):
        raise ValueError('frame_layout must be spread, duplicate or paired')
    if layout == 'paired' and (type(gap) not in (int, float) or not math.isfinite(gap) or gap <= 0):
        raise ValueError('paired frame_layout requires positive frame_pair_gap_seconds')
    if layout != 'paired' and gap is not None:
        raise ValueError('frame_pair_gap_seconds is only valid for paired frame_layout')
    return layout, gap

def layout_inputs(row, layout='spread', gap=None, verify_partners=False, frames=32):
    """Keep target slots in sampled-viewpoint order; expand only the RGB input.

    Paired rows supply student_input.partner_frames: one {path, sha256,
    recording_id, frame_index, timestamp} per anchor, in the same recording_id.
    """
    layout_settings(dict(frame_layout=layout, frame_pair_gap_seconds=gap))
    inputs = row['student_input']
    count = len(inputs['frames'])
    if type(frames) is not int or frames not in (32, 64):
        raise ValueError('frames must be 32 or 64')
    if frames == 64 and (layout != 'spread' or count != 64):
        raise ValueError('frames=64 requires exactly 64 spread anchors')
    if layout == 'spread' and (not 1 <= count <= frames or
            any(len(inputs[k]) != count for k in ('frame_indices', 'timestamps'))):
        raise ValueError(f'Spread requires at most {frames} aligned sampled viewpoints')
    if layout == 'spread':
        return inputs
    if not 1 <= count <= 32 or any(len(inputs[k]) != count for k in ('frame_indices', 'timestamps')):
        raise ValueError('C1 layouts require at most 32 aligned sampled viewpoints')
    fps, total = inputs['fps'], inputs['total_num_frames']
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError('C1 layouts require a positive source fps')
    partners = inputs.get('partner_frames', [])
    if layout == 'paired' and (len(partners) != count or not inputs.get('recording_id')):
        raise ValueError('paired frame_layout requires prepared partner_frames and recording_id for every viewpoint')
    frames, indices, timestamps = [], [], []
    for i, frame in enumerate(inputs['frames']):
        index, timestamp = inputs['frame_indices'][i], inputs['timestamps'][i]
        if type(index) is not int or not 0 <= index < total or not math.isclose(timestamp, index / fps, abs_tol=1e-6):
            raise ValueError('C1 layouts require true source indices/timestamps')
        partner, partner_index, partner_time = frame, index, timestamp
        if layout == 'paired':
            partner = partners[i]
            partner_index, partner_time = partner.get('frame_index'), partner.get('timestamp')
            if (partner.get('recording_id') != inputs['recording_id']
                    or type(partner_index) is not int or not index < partner_index < total
                    or type(partner_time) not in (int, float)
                    or not math.isclose(partner_time, partner_index / fps, abs_tol=1e-6)
                    or not math.isclose(partner_time - timestamp, gap, rel_tol=0, abs_tol=1e-6)
                    or not partner.get('path') or not partner.get('sha256')):
                raise ValueError('paired partner must be pinned in the same recording at the configured gap')
            if verify_partners:
                pinned({k: partner[k] for k in ('path', 'sha256')})
        frames.extend((frame, partner))
        indices.extend((index, partner_index))
        timestamps.extend((timestamp, partner_time))
    return {**inputs, 'frames': frames, 'frame_indices': indices, 'timestamps': timestamps}
