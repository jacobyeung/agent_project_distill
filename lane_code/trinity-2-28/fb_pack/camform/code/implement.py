from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];cam=ROOT.parent/'ro/orch_n30/fb_pack/cam/work';new=ROOT/'work/new'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
common=(cam/'common.py').read_text();rules=common[common.index('ROT_OLD='):common.index('\ndef form(')]
policy=dict(schema='r1-camera-trace-form-v1',rule_ids=['CAM-ROT-WORDS-v1','CAM-DIR-SYMBOL-v1'],input_sha256={'fbp_cam/work/build.py':sha(cam/'build.py'),'fbp_cam/work/common.py':sha(cam/'common.py')})
(new/'configs/r1_camera_trace_form_v1.json').write_text(json.dumps(policy,indent=2)+'\n')
header='''"""Pinned, value-preserving camera prose edits for base routing composition."""
from copy import deepcopy
import re
from .p3_provenance import file_pin, load, pinned

# Copied verbatim from fbp_cam/work/common.py, used by fbp_cam/work/build.py.
'''
body='''
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
'''
(new/'student_pilot/r1_camera_trace_form.py').write_text(header+rules+'\nPOLICY = '+repr(policy)+'\n'+body)
p=new/'student_pilot/r1_routing.py';s=p.read_text()
s=s.replace("    filters = Filters(cfg, base['division'])", "    camera_form = None\n    if 'camera_trace_form' in cfg['r1_training']:\n        from .r1_camera_trace_form import CameraTraceForm, rewrite_row\n        camera_form = CameraTraceForm(cfg['r1_training']['camera_trace_form'])\n    filters = Filters(cfg, base['division'])")
s=s.replace("        db.execute('INSERT OR REPLACE INTO rows VALUES(?,?,?)'", "        camera_rules = []\n        if camera_form is not None and origin == 'base':\n            row, camera_rules = rewrite_row(row)\n        db.execute('INSERT OR REPLACE INTO rows VALUES(?,?,?)'")
s=s.replace("        counts[origin] += 1", "        if camera_form is not None and origin == 'base':\n            camera_form.record(row, camera_rules)\n        counts[origin] += 1")
s=s.replace("    write(output/'receipt.json', result)","    if camera_form is not None:\n        result['camera_trace_form'] = camera_form.receipt(base)\n    write(output/'receipt.json', result)")
p.write_text(s)
(ROOT/'STATUS.md').write_text('Stage 2: Implemented an opt-in pinned camera_trace_form policy at base-row composition. The helper copies both fbp_cam rules exactly, re-renders changed events, updates response offsets, preserves other fields, rejects inconsistent source targets/spans, and counts admitted rewrites in the receipt. The absent-field path adds no receipt fields. Validation is underway.\n')
print(json.dumps(policy,indent=2))
