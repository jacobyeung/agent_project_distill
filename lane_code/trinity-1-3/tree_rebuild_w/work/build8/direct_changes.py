"""Refuse legacy answer-only training rows at producer and suffix boundaries."""
from pathlib import Path
T=Path(__file__).resolve().parents[2]/'work/tree_r1'
p=T/'student_pilot/carrier_c1_routing.py';s=p.read_text()
a=s.index('def direct_row(raw):');b=s.index('\n\ndef build_routing_stream',a)
s=s[:a]+'''def require_training_think(target):
    """Legacy training targets must contain an explicit reasoning body."""
    if (not isinstance(target, str) or not target.startswith(THINK)
            or '</think>' not in target
            or not target[len(THINK):target.index('</think>')].strip()):
        raise ValueError('LEGACY_DIRECT_SOURCE_EMPTY_THINK_REFUSED')


def direct_row(raw):
    """Pack a concrete direct trace while preserving its exact target bytes."""
    target = raw.get('target')
    require_training_think(target)
    inputs = dict(raw['student_input'])
    count = len(inputs['frames'])
    if count not in (32, 64) or len(inputs['frame_indices']) != count:
        raise ValueError('Direct rows require 32 or 64 pinned native frames')
    from .r2_grammar import validate_direct
    answer = validate_direct(target, inputs['question'], count)
    if answer != str(raw['answer']):
        raise ValueError('Direct trace answer differs from its declared answer')
    suffix = '\\n</think>\\n\\n' + answer
    if not target.endswith(suffix):
        raise ValueError('Direct trace target does not match the training renderer')
    body = target[len(THINK):-len(suffix)]
    inputs['timestamps'] = [k / inputs['fps'] for k in inputs['frame_indices']]
    dataset, scene = (alias_of(raw['canonical']) if 'canonical' in raw
                      else raw['dataset'] + '/' + raw['scene']).split('/', 1)
    events = [dict(kind='canonical_text', text=body)]
    return dict(qid=raw['qid'], dataset=dataset, scene=scene, category='routing_trace', student_input=inputs,
                target=target, routing=dict(qid=raw['qid'], question_type=raw['question_type'], form='direct_trace',
                                            canonical=raw.get('canonical'),
                                            events=events, answer=raw['answer'], gt_answer=raw['answer'],
                                            tool_output_spans=[], category='direct', head_layout='n/a'))
'''+s[b:]
s=s.replace("    from .batches import training_text\n    inputs = row['student_input']", "    require_training_think(target)\n    from .batches import training_text\n    inputs = row['student_input']")
s=s.replace("    stored = [(s['start'], s['end'], s['call_id']) for s in row['tool_output_spans']]", "    require_training_think(target)\n    stored = [(s['start'], s['end'], s['call_id']) for s in row['tool_output_spans']]")
s=s.replace('# DIRECT types enter only as answer-only rows (--direct-source), never as reasoning rows.', '# This legacy policy admits direct traces through --direct-source.')
p.write_text(s)
p=T/'tests/test_carrier_c1_routing.py';s=p.read_text()
s=s.replace("target=R.THINK + '\\n</think>\\n\\nB',", "target=R.THINK + 'Locate: the sofa is seen in frame 1.\\nLocate: the table is seen in frame 2.\\nRelate: the table is longer than the sofa.\\n</think>\\n\\nB',")
p.write_text(s)
