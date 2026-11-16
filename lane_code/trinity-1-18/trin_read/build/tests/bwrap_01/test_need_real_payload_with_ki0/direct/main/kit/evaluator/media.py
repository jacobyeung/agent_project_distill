"""Official PyAV anchors and explicit consecutive temporal pairs."""
from functools import lru_cache
import hashlib
import io
import json
import math
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from evalpath.items import digest, sha256
from evalpath.sampling import sample_video, _sample_floor_uniform_indices
from nested_sampling import sample_nested_video
from cells import frame_count


def frame_list(indices, fps, total, layout, frames=32):
    if layout not in ('spread', 'duplicate', 'P0.5', 'P0.2'):
        raise ValueError('Unknown layout')
    if type(frames) is not int or frames not in (32,64) or (frames==64 and layout!='spread'):
        raise ValueError('64 anchors require explicit frames=64 and spread layout')
    if not math.isfinite(fps) or fps <= 0 or len(indices) != frames:
        raise ValueError(f'Require {frames} anchors and positive source FPS')
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


def decode(task, layout, frames=32, frame_set=None):
    """Original official decode entry point, used only by the CPU frame stage."""
    selection = {'frame_set':frame_set} if frame_set is not None else {}
    frame_count(dict(frames=frames,layout=layout,benchmarks=[task['benchmark']],**selection))
    if task['benchmark']=='pointing':
        return decode_pointing(task,layout)
    if task['benchmark']=='pointing_video':
        if layout!='duplicate':raise ValueError('Pointing video requires duplicate layout')
        anchors,audit=decode_pointing(task,'spread')
        arrays=np.repeat(anchors,2,axis=0)
        indices=[i for i in task['source_frame_indices'] for _ in range(2)]
        return arrays,{**audit,'metadata':{**audit['metadata'],'frames_indices':indices},
                       'realized_gaps':[0.]*32,'pixel_sha256':pixel_digest(arrays)}
    video = Path(task['video_path'])
    if task.get('video_sha256') and sha256(video) != task['video_sha256']:
        raise ValueError('Video pin differs')
    if frame_set == 'nested':
        anchors, indices, fps, total = sample_nested_video(task)
    else:
        anchors, indices, fps, total = sample_video(task, SimpleNamespace(max_frames_num=frames))
    tier = task.get('revsi_tier', 32)
    if task['benchmark'] == 'revsi' and (total != tier or frames != tier):
        raise ValueError(f'ReVSI requires its own exact {tier}-frame video read at {tier} frames')
    if task['benchmark']=='revsi' and layout.startswith('P'):
        raise ValueError('ReVSI temporal partners require a separately pinned source recording')
    expanded, fallback = frame_list(indices, fps, total, layout, frames)
    by_index = dict(zip(indices, anchors))
    missing = set(expanded)-set(indices)
    if missing:
        import av
        with av.open(str(video)) as container:
            for ordinal, frame in enumerate(container.decode(video=0)):
                if ordinal in missing:
                    by_index[ordinal] = frame.to_ndarray(format='rgb24')
    arrays = np.stack([by_index[i] for i in expanded])
    metadata = dict(fps=fps, frames_indices=expanded, total_num_frames=total,
                    height=int(arrays.shape[1]), width=int(arrays.shape[2]))
    if task['benchmark']=='revsi':
        source=task['source_frame_indices']
        if len(source)!=tier or source!=sorted(source) or source[0]!=0:
            raise ValueError('Invalid official ReVSI source indices')
        # Recover source FPS from the compact video, exactly as in direct decoding.
        original_total=source[-1]+1
        metadata.update(fps=fps*original_total/tier,total_num_frames=original_total,
                        frames_indices=[source[i] for i in expanded])
    audit=dict(metadata=metadata, anchor_indices=indices,
        end_fallback_anchors=fallback, requested_gap=float(layout[1:]) if layout.startswith('P') else None,
        realized_gaps=[(expanded[k+1]-expanded[k])/fps for k in range(0,len(expanded),2)],
        source_frame_indices=task.get('source_frame_indices'), pixel_sha256=pixel_digest(arrays))
    if frame_set == 'nested':
        # Slots are zero-based positions in the sorted 64-frame input.
        audit.update(frame_set=frame_set,anchor_slots=[indices.index(i) for i in _sample_floor_uniform_indices(total,32)])
    return arrays,audit


def decode_pointing(task,layout):
    import av
    if layout!='spread':raise ValueError('Pointing requires spread layout')
    indices=task['source_frame_indices']
    if len(indices)!=32 or indices!=sorted(indices):raise ValueError('Require kit 32-frame selection')
    got={};want=set(indices)
    with av.open(task['video_path']) as container:
        stream=container.streams.video[0]
        stream.thread_type='AUTO'
        for n,frame in enumerate(container.decode(stream)):
            if n in want:got[n]=frame.to_ndarray(format='rgb24')
            if n>=indices[-1]:break
    missing=sorted(want-set(got))
    if missing:raise ValueError('Pointing frames not decoded: '+str(missing))
    arrays=np.stack([got[i] for i in indices])
    metadata=dict(fps=task['fps'],frames_indices=indices,total_num_frames=task['total_num_frames'],
                  height=arrays.shape[1],width=arrays.shape[2])
    return arrays,dict(metadata=metadata,anchor_indices=indices,end_fallback_anchors=[],requested_gap=None,
                       realized_gaps=[],source_frame_indices=indices,pixel_sha256=pixel_digest(arrays))


def pixel_digest(arrays):
    # Preserve the original .npy digest without writing a second pixel cache.
    raw=io.BytesIO()
    np.save(raw,arrays,allow_pickle=False)
    return hashlib.sha256(raw.getbuffer()).hexdigest()


def identity(task,layout,frames=32,frame_set=None):
    value=dict(benchmark=task['benchmark'],video_path=task['video_path'],
                video_sha256=task.get('video_sha256'),source_frame_indices=task.get('source_frame_indices'),
                layout=layout)
    if task['benchmark'] in ('pointing','pointing_video'):value.update(fps=task['fps'],total_num_frames=task['total_num_frames'])
    if frames!=32:value['frames']=frames
    if frame_set is not None:value['frame_set']=frame_set
    return value


def item_key(task,layout,frames=32,frame_set=None):
    value=[task['benchmark'],task['example_id'],layout]
    if frames!=32:value.append(frames)
    if frame_set is not None:value.append(frame_set)
    return digest(value)


def cache_path(cache,name):
    path=Path(cache)/name
    if Path(name).is_absolute() or not path.resolve().is_relative_to(Path(cache).resolve()):
        raise ValueError('Frame path escapes cache')
    return path


@lru_cache(maxsize=8)
def frame_index(cache,expected):
    path=Path(cache)/'0.json'
    raw=path.read_bytes()
    if not expected or hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('Frame index pin differs')
    return json.loads(raw)


def load(task,layout,cache,index_sha256,frames=32,frame_set=None):
    """Worker entry point: authenticated PNGs only; never import PyAV or open video."""
    from PIL import Image
    selection = {'frame_set':frame_set} if frame_set is not None else {}
    frame_count(dict(frames=frames,layout=layout,benchmarks=[task['benchmark']],**selection))
    index=frame_index(str(cache),index_sha256)
    pin=index['items'][item_key(task,layout,frames,frame_set)]
    raw=cache_path(cache,pin['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pin['sha256']:
        raise ValueError('Frame receipt pin differs')
    receipt=json.loads(raw)
    if receipt['identity']!=identity(task,layout,frames,frame_set):
        raise ValueError('Frame receipt identity differs')
    if 'error' in receipt:
        raise ValueError('CPU frame stage: '+receipt['error'])
    audit=receipt['audit']
    if task['benchmark']=='pointing':
        selected=task['source_index']
        if task['source_frame_indices'][task['frame']-1]!=selected:
            raise ValueError('Pointing selected frame differs')
        selected_frames=[p for p in receipt['frames'] if p['index']==selected]
        if not selected_frames:raise ValueError('Pointing frame missing in receipt')
        receipt['frames']=selected_frames[:1]
        audit={**audit,'metadata':{**audit['metadata'],'frames_indices':[selected]},
               'pixel_sha256':selected_frames[0]['pixel_sha256']}
    by_path={};hashes={}
    for pin in receipt['frames']:
        name=pin['path']
        if name not in by_path:
            raw=cache_path(cache,name).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=pin['sha256']:
                raise ValueError('PNG pin differs')
            hashes[name]=pin['sha256']
            with Image.open(io.BytesIO(raw)) as image:
                if image.mode!='RGB' or image.format!='PNG':raise ValueError('Require lossless RGB PNG')
                by_path[name]=np.array(image)
        elif pin['sha256']!=hashes[name]:
            raise ValueError('Repeated PNG pin differs')
    arrays=np.stack([by_path[p['path']] for p in receipt['frames']])
    if pixel_digest(arrays)!=audit['pixel_sha256']:
        raise ValueError('Pixel cache differs')
    if list(arrays.shape)!=[len(audit['metadata']['frames_indices']),audit['metadata']['height'],
                            audit['metadata']['width'],3]:
        raise ValueError('PNG dimensions differ')
    if frames==64 and (len(arrays)!=64 or len(audit['anchor_indices'])!=64):
        raise ValueError('Require exactly 64 staged anchors')
    return arrays,{**audit,'frame_receipt':index['items'][item_key(task,layout,frames,frame_set)]}


def kwargs(count):
    return dict(size={'shortest_edge':count*128*128, 'longest_edge':count*384*384},
                do_sample_frames=False)
