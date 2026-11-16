"""Validate opt-in anchor counts without adding defaults to bound cells."""

FRAME_COUNTS = (32, 64, 96, 128, 160, 192)
VISUAL_TOKENS_PER_FRAME = 130
GENERATION_CAP = 16384
PROMPT_ALLOWANCE = 2048
CONTEXT_LIMIT = 49152


def validate_token_budget(cell, context_limit=CONTEXT_LIMIT):
    """Reserve visual tokens, generation tokens, and the text prompt allowance."""
    required = cell.get('frames', 32) * VISUAL_TOKENS_PER_FRAME + GENERATION_CAP + PROMPT_ALLOWANCE
    if required > context_limit:
        raise ValueError(f'Cell token budget needs {required} tokens, exceeds context limit {context_limit}')
    return required


def frame_count(cell):
    frames = cell.get('frames', 32)
    cell.setdefault('layout', 'duplicate' if frames == 32 else 'spread')
    if type(frames) is not int or frames not in FRAME_COUNTS:
        raise ValueError('Cell frames must be 32 or 64, or nested 96, 128, 160 or 192')
    if 'frame_set' in cell and not ((cell['frame_set'] == 'nested' and frames > 32 and frames != 96) or (cell['frame_set'] == 'uniform' and frames == 96)):
        if frames in (32, 64):
            raise ValueError('Cell frame_set must be nested with frames=64')
        raise ValueError(f'Cell frame_set must be nested with frames={frames}')
    if 'vstifull' in cell['benchmarks'] and (frames != 32 or cell['layout'] not in ('spread','duplicate') or cell.get('question_frames') or cell.get('valid_slots') or cell.get('anchor_labels')):
        raise ValueError('Official VSTI requires unchanged 32 frames with duplicate or spread layout')
    if frames == 64 and set(cell['benchmarks']) == {'revsi'} and 'frame_set' not in cell:
        if cell['layout'] != 'spread':
            raise ValueError('ReVSI at 64 frames requires spread')
        validate_token_budget(cell)
        return frames
    if frames > 32 and ((cell['layout'] != 'spread' and not (frames == 64 and cell['layout'] == 'duplicate' and cell['benchmarks'] == ['devrows'])) or not cell['benchmarks']
                         or not set(cell['benchmarks']) <= {'vsi500_slice', 'vsi500', 'devrows', 'official5130'}):
        raise ValueError(f'frames={frames} requires spread with only vsi500_slice, vsi500, devrows or official5130; pointing, ReVSI, duplicate and paired layouts are unsupported')
    # Retain the existing 64-frame floor-uniform option.
    if frames > 64 and cell.get('frame_set') != ('uniform' if frames == 96 else 'nested'):
        raise ValueError(f'frames={frames} requires frame_set nested')
    validate_token_budget(cell)
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
