"""Use the accepted evaluator functions for anchors and temporal layout."""
from types import SimpleNamespace
import numpy as np
from .paths import evaluator, module, REVSI
from .io import sha
from offkit.frames import bind_frames

def sample(path, binding):
    evaluator()
    from evalpath.sampling import sample_video
    media = module('_native_media', REVSI/'reader/evaluator/media.py')
    count, layout = binding['count'], binding['layout']
    anchors, indices, fps, total = sample_video(dict(video_path=str(path)), SimpleNamespace(max_frames_num=count))
    expanded, fallbacks = media.frame_list(indices, fps, total, layout, frames=count)
    by_index = dict(zip(indices, anchors))
    return np.stack([by_index[i] for i in expanded]), dict(indices=indices, expanded=expanded,
        fps=fps, total=total, fallbacks=fallbacks, count=count, layout=layout, video_sha256=sha(path))

def dense(path):
    evaluator()
    from evalpath.sampling import sample_video
    arrays, indices, fps, total = sample_video(dict(video_path=str(path)), SimpleNamespace(max_frames_num=64))
    return arrays, dict(indices=indices, fps=fps, total=total, count=64, video_sha256=sha(path))


def selected(path,indices):
    """Decode the registered original indices exactly once without interpolation."""
    import av
    if indices!=sorted(set(indices)) or any(type(i)!=int or i<0 for i in indices):
        raise ValueError('registered indices must increase')
    wanted=set(indices);images={}
    with av.open(str(path)) as video:
        for i,frame in enumerate(video.decode(video=0)):
            if i in wanted:images[i]=frame.to_ndarray(format='rgb24')
            if i>=indices[-1]:break
    if set(images)!=wanted:raise ValueError('original video lacks registered frames')
    return [images[i] for i in indices]
