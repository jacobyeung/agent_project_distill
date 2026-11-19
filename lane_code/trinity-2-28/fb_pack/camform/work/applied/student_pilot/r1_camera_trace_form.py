"""Pinned, value-preserving camera prose edits for base routing composition."""
from copy import deepcopy
import re
from .p3_provenance import file_pin, load, pinned

# Copied verbatim from fbp_cam/work/common.py, used by fbp_cam/work/build.py.
ROT_OLD='wrapped to (-180, 180], with positive turn meaning left and a half turn reported as +180 degrees.'
ROT_NEW='wrapped to the shortest signed turn, with positive turn meaning left and a half turn reported as positive.'
NEG=re.compile(r'(-d[xyz]) = [+-]?\d+(?:\.\d+)? m(?=[;.])')

def rewrite_text(s):
 ids=[]
 if ROT_OLD in s:s=s.replace(ROT_OLD,ROT_NEW);ids.append('CAM-ROT-WORDS-v1')
 if s.startswith('Scoring each option by the matching component:'):
  s,n=NEG.subn(r'\1',s)
  if n:ids.append('CAM-DIR-SYMBOL-v1')
 return s,ids

POLICY = {'schema': 'r1-camera-trace-form-v1', 'rule_ids': ['CAM-ROT-WORDS-v1', 'CAM-DIR-SYMBOL-v1'], 'input_sha256': {'fbp_cam/work/build.py': '39e8c067e319566ca31202b49c58470a147f4e556fc94ebeb86625c7d6b5544d', 'fbp_cam/work/common.py': '4535d0f1371268cd3590b477eea75f806c0156ff5b58b824261ee352b7d01712'}}

TYPES = ('camera_rotation', 'camera_movement_direction')
FIELD = 'camera_trace_form'


def rewrite_row(row):
    """Return a new row only when a camera plan/prose event matches a rule."""
    if row.get('routing', {}).get('question_type') not in TYPES:
        return row, []
    edits = []
    for i, event in enumerate(row['routing']['events']):
        if event['kind'] in ('plan', 'canonical_text'):
            text, ids = rewrite_text(event['text'])
            if ids:
                edits.append((i, text, ids))
    if not edits:
        return row, []
    from .carrier_c1_routing import render
    before, before_spans = render(row['routing']['events'], row['routing']['answer'])
    stored = row['routing']['tool_output_spans']
    if (before != row['target'] or
            [(s['start'], s['end'], s['call_id']) for s in stored] !=
            [(s['start'], s['end'], s['call_id']) for s in before_spans]):
        raise ValueError('R1_CAMERA_TRACE_SOURCE_DIFFERS:'+row['qid'])
    new = deepcopy(row)
    applied = set()
    for i, text, ids in edits:
        new['routing']['events'][i]['text'] = text
        applied.update(ids)
    new['target'], spans = render(new['routing']['events'], new['routing']['answer'])
    for stored, span in zip(new['routing']['tool_output_spans'], spans, strict=True):
        stored.update(start=span['start'], end=span['end'])
    # c1_row may also carry a top-level copy of the same span metadata.
    if 'tool_output_spans' in new:
        if row['tool_output_spans'] != row['routing']['tool_output_spans']:
            raise ValueError('R1_CAMERA_TRACE_SPANS_DIFFER:'+row['qid'])
        for stored, span in zip(new['tool_output_spans'], spans, strict=True):
            stored.update(start=span['start'], end=span['end'])
    return new, sorted(applied)


class CameraTraceForm:
    """Authenticate the opt-in policy and count only successfully stored base rows."""
    def __init__(self, pin):
        if load(pinned(pin)) != POLICY:
            raise ValueError('R1_CAMERA_TRACE_POLICY_DIFFERS')
        self.pin = pin
        self.admitted = dict.fromkeys(TYPES, 0)
        self.rewritten = dict.fromkeys(TYPES, 0)
        self.rules = dict.fromkeys(POLICY['rule_ids'], 0)

    def record(self, row, ids):
        kind = row.get('routing', {}).get('question_type')
        if kind in TYPES:
            self.admitted[kind] += 1
            self.rewritten[kind] += bool(ids)
        for rule in ids:
            self.rules[rule] += 1

    def receipt(self, base):
        implementation = file_pin(__file__)
        return dict(schema=POLICY['schema'], policy=self.pin,
                    rule_ids=POLICY['rule_ids'], implementation=implementation,
                    input_sha256={**POLICY['input_sha256'],
                        self.pin['path']:self.pin['sha256'],
                        implementation['path']:implementation['sha256'],
                        base['database']['path']:base['database']['sha256']},
                    admitted_base_rows_by_type=self.admitted,
                    rewritten_base_rows_by_type=self.rewritten,
                    rewritten_base_rows=sum(self.rewritten.values()),
                    rewritten_base_rows_by_rule=self.rules)
