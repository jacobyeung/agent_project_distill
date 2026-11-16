"""Official Qwen3.5 video branch (run_eval.py prepare_q35_visual, frame_source video_32): PyAV decode of every
frame for the true count and timestamps, floor-uniform indices k*(N-1)//(n-1), rgb24 arrays. Copied verbatim
apart from indentation and the return shape; this is the path behind f17's official 63.79."""
import numpy as np


def _sample_floor_uniform_indices(total, num_frames):
    if total < num_frames:
        raise ValueError(f"Video has only {total} decoded frames, need {num_frames}")
    if num_frames == 1:
        return [0]
    return [k * (total - 1) // (num_frames - 1) for k in range(num_frames)]


def sample_video(task, args):
    import av
    num_target = int(args.max_frames_num)
    timestamps, sizes = [], []
    with av.open(str(task["video_path"])) as container:
        if not container.streams.video:
            raise ValueError(f"Source {task['video_path']} has no video stream")
        stream = container.streams.video[0]
        fps_rate = stream.average_rate
        if fps_rate is None:
            raise ValueError(f"Source {task['video_path']} has no original FPS")
        fps = float(fps_rate)
        for frame in container.decode(stream):
            if frame.pts is None or frame.time_base is None:
                raise ValueError(f"Decoded frame in {task['video_path']} lacks PTS/time_base")
            timestamps.append(float(frame.pts * frame.time_base))
            sizes.append((frame.width, frame.height))
    total_num_frames = len(timestamps)
    indices = _sample_floor_uniform_indices(total_num_frames, num_target)
    selected_set = set(indices)
    frames_by_idx = {}
    with av.open(str(task["video_path"])) as container:
        for ordinal, frame in enumerate(container.decode(video=0)):
            if ordinal not in selected_set:
                continue
            frames_by_idx[ordinal] = frame.to_ndarray(format="rgb24")
    arrays = np.stack([frames_by_idx[i] for i in indices], axis=0)
    return arrays, indices, fps, total_num_frames
