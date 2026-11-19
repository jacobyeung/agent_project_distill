"""Build dense RGB membership before the forward reconstructs and subsamples geometry."""
from copy import deepcopy
from .dense_eval import nested_indices
from .p3_provenance import digest
from .r2_contract import expand_frames


def build_training(row, count=64):
    result = deepcopy(row)
    sparse = result['student_input'] = expand_frames(row['student_input'])
    source = sparse.pop('dense_source', None)
    if source is None:
        from .r2_frames import NeedsFrameHost
        raise NeedsFrameHost('needs the frame host: dense source manifest is missing for ' + row['qid'])
    wanted = nested_indices(sparse['total_num_frames'], sparse['frame_indices'], count)
    frames = {}
    for pin in source['frames']:
        ordinal = pin['source_index']
        if ordinal in frames and frames[ordinal]['sha256'] != pin['sha256']:
            raise ValueError('Conflicting dense content at source ordinal')
        frames[ordinal] = dict(path=pin['path'], sha256=pin['sha256'])
    for ordinal, pin in zip(sparse['frame_indices'], sparse['frames'], strict=True):
        if ordinal not in frames or frames[ordinal]['sha256'] != pin['sha256']:
            raise ValueError('Sparse RGB differs from dense content')
        # Preserve each row's logical path; content identity never includes it.
        frames[ordinal] = pin
    if not set(wanted) <= frames.keys():
        from .r2_frames import NeedsFrameHost
        raise NeedsFrameHost('needs the frame host: dense source lacks selected ordinals')
    dense = dict(frames=[frames[i] for i in wanted], frame_indices=wanted,
                 timestamps=[i/sparse['fps'] for i in wanted], fps=sparse['fps'],
                 total_num_frames=sparse['total_num_frames'])
    sparse['geometry_dense'] = dense
    clip_key = digest([(i, frames[i]['sha256']) for i in wanted])
    from .gf1 import dense_inputs
    dense_inputs(result, {'dense_frames': count})
    return result, clip_key
