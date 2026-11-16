"""Validate opt-in anchor counts without adding defaults to bound cells."""


def frame_count(cell):
    frames = cell.get('frames', 32)
    if type(frames) is not int or frames not in (32, 64):
        raise ValueError('Cell frames must be 32 or 64')
    if 'frame_set' in cell and (cell['frame_set'] != 'nested' or frames != 64):
        raise ValueError('Cell frame_set must be nested with frames=64')
    if frames == 64 and set(cell['benchmarks']) == {'revsi'} and 'frame_set' not in cell:
        if cell['layout'] != 'spread':
            raise ValueError('ReVSI at 64 frames requires spread (its own 64-frame tier video)')
        return frames
    if frames == 64 and (cell['layout'] != 'spread' or not cell['benchmarks']
                         or not set(cell['benchmarks']) <= {'vsi500_slice', 'vsi500', 'devrows', 'official5130'}):
        raise ValueError('frames=64 requires spread with only vsi500_slice, vsi500, devrows or official5130; pointing, ReVSI, duplicate and paired layouts are unsupported')
    return frames


def check_layout(row, layout):
    """Require the journal's explicit layout to match its bound cell."""
    if 'layout' not in row or row['layout'] != layout:
        raise ValueError('Journal layout differs from its bound cell: '+row['key'])


def check_pinned_frames(row, task, layout):
    """Use the bound layout and exact ordered expansion of pinned anchors."""
    if task['benchmark'] == 'revsi' and row.get('status') == 'complete':
        source = task['source_frame_indices']
        expected = [i for i in source for _ in range(2)] if layout == 'duplicate' else source
        if row['media']['metadata']['frames_indices'] != expected:
            raise ValueError('Journal ReVSI frames differ from the pinned tier: '+row['key'])

REVSI_PINNED_ADMISSION = True
