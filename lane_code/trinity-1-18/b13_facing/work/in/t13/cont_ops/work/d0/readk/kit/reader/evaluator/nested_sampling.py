"""Opt-in nested selection with the official two-pass count and RGB decode contract."""
import numpy as np
from evalpath.sampling import _sample_floor_uniform_indices


def nested_indices(total):
    """Bisect the largest gap, breaking ties by its earliest source index."""
    if total < 64:
        raise ValueError(f'Video has only {total} decoded frames, need 64 for nested bisection')
    indices = _sample_floor_uniform_indices(total, 32)
    while len(indices) < 64:
        slot = max(range(len(indices) - 1), key=lambda i: indices[i+1] - indices[i])
        a, b = indices[slot:slot+2]
        if b - a < 2:
            raise ValueError('Nested bisection cannot reach 64 unique frames')
        indices.insert(slot+1, (a+b)//2)
    return indices


def sample_nested_video(task):
    import av
    total = 0
    with av.open(str(task['video_path'])) as container:
        if not container.streams.video:
            raise ValueError(f"Source {task['video_path']} has no video stream")
        stream = container.streams.video[0]
        if stream.average_rate is None:
            raise ValueError(f"Source {task['video_path']} has no original FPS")
        fps = float(stream.average_rate)
        for frame in container.decode(stream):
            if frame.pts is None or frame.time_base is None:
                raise ValueError(f"Decoded frame in {task['video_path']} lacks PTS/time_base")
            total += 1
    indices = nested_indices(total)
    selected = set(indices)
    by_index = {}
    with av.open(str(task['video_path'])) as container:
        for ordinal, frame in enumerate(container.decode(video=0)):
            if ordinal in selected:
                by_index[ordinal] = frame.to_ndarray(format='rgb24')
    return np.stack([by_index[i] for i in indices]), indices, fps, total
