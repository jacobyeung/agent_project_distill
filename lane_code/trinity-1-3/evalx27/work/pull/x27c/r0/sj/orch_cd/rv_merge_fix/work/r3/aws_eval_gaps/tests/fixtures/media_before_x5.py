"""Official PyAV anchors and explicit consecutive temporal pairs."""
import fcntl
import json
import math
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from evalpath.items import digest
from evalpath.sampling import sample_video


def frame_list(indices, fps, total, layout):
    if layout not in ('spread', 'duplicate', 'P0.5', 'P0.2'):
        raise ValueError('Unknown layout')
    if not math.isfinite(fps) or fps <= 0 or len(indices) != 32:
        raise ValueError('Require 32 anchors and positive source FPS')
    if layout == 'spread':
        return list(indices), []
    if layout == 'duplicate':
        return [i for i in indices for _ in range(2)], []
    gap = float(layout[1:])
    step = max(1, int(round(gap*fps)))
    pairs, fallbacks = [], []
    for i in indices:
        j = i+step
        if j >= total:
            j = i-step
            fallbacks.append(i)
        if not 0 <= j < total:
            raise ValueError('Recording too short for requested pair gap')
        pairs.extend((i, j))
    return pairs, fallbacks


def load(task, layout, cache):
    """One cache fill per video/layout across workers; retain exact RGB arrays."""
    video = Path(task['video_path'])
    stat = video.stat()
    key = digest(dict(path=str(video), bytes=stat.st_size, mtime=stat.st_mtime_ns,
                      sha256=task.get('video_sha256'), layout=layout,source_indices=task.get('source_frame_indices')))
    directory = Path(cache)/key
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'0.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        receipt, pixels = directory/'0.json', directory/'0.npy'
        if not receipt.exists():
            from evalpath.items import sha256
            if task.get('video_sha256') and sha256(video) != task['video_sha256']:
                raise ValueError('Video pin differs')
            anchors, indices, fps, total = sample_video(task, SimpleNamespace(max_frames_num=32))
            if task['benchmark'] == 'revsi' and total != 32:
                raise ValueError('ReVSI requires its own exact 32-frame video')
            if task['benchmark']=='revsi' and layout.startswith('P'):
                raise ValueError('ReVSI temporal partners require a separately pinned source recording')
            expanded, fallback = frame_list(indices, fps, total, layout)
            by_index = dict(zip(indices, anchors))
            missing = set(expanded)-set(indices)
            if missing:
                import av
                with av.open(str(video)) as container:
                    for ordinal, frame in enumerate(container.decode(video=0)):
                        if ordinal in missing:
                            by_index[ordinal] = frame.to_ndarray(format='rgb24')
            arrays = np.stack([by_index[i] for i in expanded])
            np.save(pixels, arrays, allow_pickle=False)
            metadata = dict(fps=fps, frames_indices=expanded, total_num_frames=total,
                            height=int(arrays.shape[1]), width=int(arrays.shape[2]))
            if task['benchmark']=='revsi':
                source=task['source_frame_indices']
                if len(source)!=32 or source!=sorted(source) or source[0]!=0:
                    raise ValueError('Invalid official ReVSI source indices')
                # ReVSI preserves source duration in its 32-frame MP4. Recover the
                # original FPS from the exact source count and the compact rate.
                original_total=source[-1]+1
                metadata.update(fps=fps*original_total/32,total_num_frames=original_total,
                                frames_indices=[source[i] for i in expanded])
            receipt.write_text(json.dumps(dict(metadata=metadata, anchor_indices=indices,
                end_fallback_anchors=fallback, requested_gap=float(layout[1:]) if layout.startswith('P') else None,
                realized_gaps=[(expanded[k+1]-expanded[k])/fps for k in range(0,len(expanded),2)],
                source_frame_indices=task.get('source_frame_indices'), pixel_sha256=sha256(pixels)))+'\n')
        audit = json.loads(receipt.read_text())
        # Local cache corruption must not silently change parity inputs.
        from evalpath.items import sha256
        if sha256(pixels) != audit['pixel_sha256']:
            raise ValueError('Pixel cache differs')
        return np.load(pixels, allow_pickle=False), audit


def kwargs(count):
    return dict(size={'shortest_edge':count*128*128, 'longest_edge':count*384*384},
                do_sample_frames=False)
