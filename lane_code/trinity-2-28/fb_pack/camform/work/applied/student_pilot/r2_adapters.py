"""Metadata joins for native sealed event rows and frames_pending direct rows."""
from copy import deepcopy
import re
from .p3_provenance import digest


def normalize(raw, frame_map=None):
    row = deepcopy(raw)
    native = row.get('routing', {})
    if (row.get('category') == 'routing_trace' and not row.get('events')
            and native.get('question_type') in ('camera_displacement','camera_movement_direction','camera_rotation')):
        # Unpack the native camera layout through its existing byte-equal replay
        # check before applying the same event intake as other routing slices.
        from .s1_routing import legacy_replay
        legacy_replay(row)
        inputs = row['student_input']
        row = dict(native, schema='derivgen-row-v2', infrastructure_only=False,
            qid=row['qid'], dataset=row['dataset'], scene=row['scene'], target=row['target'],
            student_input=inputs, question=inputs['question'], options=inputs.get('options', []),
            answer_form='routed', response_heads=['pose'],
            provenance=dict(canonical=native['canonical'], alias=row['dataset']+'/'+row['scene'],
                physical_group=native.get('physical_group'), source_row_sha256=native['source_row_sha256'],
                frame_indices=inputs['frame_indices']))
    if 'suffix' in row and not row.get('ground_record'):
        # Raw pool files retain the exact printed calls/responses. Pack those
        # byte spans; neither replay geometry nor synthesize a tool quantity.
        from .ground_rows import pack
        events=[]
        for match in re.finditer(r'(<[a-z][a-z_0-9]*\b[^>\n]*>)\n(<tool_response>[\s\S]*?</tool_response>)',row['suffix']):
            call,response=match.groups()
            audit={}
            if row.get('simulated_misses') and 'not seen' in response.lower():
                audit=dict(simulated=True,status='not seen')
            events.append(dict(call=call,response=response,audit=audit))
        if not events or len(events)!=row['suffix'].count('<tool_response>'):
            raise ValueError('Raw pool response is not paired with a printed call')
        provenance={**row.get('provenance',{}),'canonical':row['canonical'],
                    'source_row_sha256':digest(raw),'frame_indices':row['frame_indices']}
        record={**row,'events':events}
        row=pack(record,provenance)
        row['frame_indices']=record['frame_indices']
        if record.get('mask_source')==record.get('geometry_source')=='gt' and record.get('gt_authority')!='selector':
            row['response_source']='ground_truth'
    provenance = row.get('provenance', {})
    if not row.get('dataset') or not row.get('scene'):
        from .carrier_c1_routing import alias_of
        key = provenance.get('alias') or alias_of(provenance['canonical'])
        row['dataset'], row['scene'] = key.split('/', 1)
    pending = row.get('frames_pending') or provenance.get('frames_pending')
    inputs = row.get('student_input', {})
    row.setdefault('question', inputs.get('question'))
    row.setdefault('options', inputs.get('options', []))
    if row.get('schema') == 'derivgen-row-v2' and not row.get('events') and row.get('ground_record', {}).get('events'):
        from .ground_rows import pack
        record = dict(row['ground_record'], suffix=row['target'])
        packed = pack(record, provenance)
        if packed['target'] != row['target'] or packed['tool_output_spans'] != row['tool_output_spans']:
            raise ValueError('Published event target or response spans differ')
        row['events'] = packed['events']
        if ('r2_source_sha256' not in raw and record.get('mask_source') == record.get('geometry_source') == 'gt'
                and record.get('gt_authority') != 'selector'):
            row.setdefault('response_source', 'ground_truth')
    if pending is not None and (pending.get('d') != row['dataset'] or pending.get('s') != row['scene']
                                or pending.get('i') != inputs.get('frame_indices')):
        raise ValueError('Wrong scene or indices in pending RGB lineage')
    if not inputs.get('frames'):
        if hasattr(frame_map, 'resolve'):
            rgb, authority = frame_map.resolve(row)
            rgb['frames'] = [dict(pin, source_index=i) for i, pin in zip(rgb['frame_indices'], rgb['frames'])]
            frame_map = {row['qid']: rgb}
            row['r2_frame_join'] = authority
        if frame_map is None or row['qid'] not in frame_map:
            raise ValueError('needs frame metadata: supply the pinned frame_map join before intake')
        rgb = deepcopy(frame_map[row['qid']])
        indices = [pin['source_index'] for pin in rgb['frames']]
        expected = inputs.get('frame_indices', row.get('frame_indices', provenance.get('frame_indices')))
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
