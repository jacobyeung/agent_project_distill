"""Metadata joins for native sealed event rows and frames_pending direct rows."""
from copy import deepcopy
from .p3_provenance import digest


def normalize(raw, frame_map=None):
    row = deepcopy(raw)
    provenance = row.get('provenance', {})
    if not row.get('dataset') or not row.get('scene'):
        from .carrier_c1_routing import alias_of
        key = provenance.get('alias') or alias_of(provenance['canonical'])
        row['dataset'], row['scene'] = key.split('/', 1)
    pending = row.get('frames_pending') or provenance.get('frames_pending')
    inputs = row.get('student_input', {})
    if pending is not None and (pending.get('d') != row['dataset'] or pending.get('s') != row['scene']
                                or pending.get('i') != inputs.get('frame_indices')):
        raise ValueError('Wrong scene or indices in pending RGB lineage')
    if not inputs.get('frames'):
        if frame_map is None or row['qid'] not in frame_map:
            raise ValueError('needs frame metadata: supply the pinned frame_map join before intake')
        rgb = deepcopy(frame_map[row['qid']])
        indices = [pin['source_index'] for pin in rgb['frames']]
        expected = inputs.get('frame_indices', provenance.get('frame_indices'))
        if indices != expected:
            raise ValueError('Frame map differs from source ordinals')
        rgb['frames'] = [dict(path=p['path'], sha256=p['sha256']) for p in rgb['frames']]
        row['student_input'] = dict(rgb, frame_indices=indices, timestamps=[i/rgb['fps'] for i in indices],
                                    question=row['question'], options=row.get('options') or [])
    if row.get('events'):
        from .carrier_c1_routing import check_row, render
        check_row(row)
        # Sealed camera rows have bare answers. Add only the required delimiter;
        # the event sequence, response bytes and numerical answer are unchanged.
        if not row['target'].rstrip().endswith('</answer>'):
            row['answer'] = '<answer>'+str(row['answer'])+'</answer>'
            row['target'], row['tool_output_spans'] = render(row['events'], row['answer'])
    row['r2_source_sha256'] = digest(raw)
    return row
