"""Next-leg row membership and initialization; no optimizer state crosses epochs."""
from copy import deepcopy
import json
import math
from pathlib import PurePosixPath
import re
from .p3_provenance import digest, load, pinned
from .r2_grammar import PROGRAM_TYPES, validate_direct, validate_program
from .r2_units import ROOM, asked_unit

CONTRACT = 'next-leg-r2-v1'
def init_identity(value):
    if not isinstance(value, dict) or not re.fullmatch('[0-9a-f]{64}', str(value.get('artifact_sha256', ''))):
        raise ValueError('Missing pinned init identity')
    if any(not value.get(k) for k in ('parent_run', 'parent_kit', 'parent_source_seal', 'parent_configuration_prefix')) or type(value.get('step')) is not int or value['step'] < 0:
        raise ValueError('Incomplete pinned init lineage')
    if not re.fullmatch('[0-9a-f]{64}', str(value['parent_source_seal'])):
        raise ValueError('Incomplete pinned init lineage')
    return deepcopy(value)


def selected_init(pin):
    if not pin:
        raise ValueError('Missing pinned init selection')
    value = load(pinned(pin))
    if value.get('schema') != 'r2-init-selection-v1':
        raise ValueError('Invalid init selection')
    return init_identity(value.get('identity'))


def bound_init(cfg):
    value = cfg.get('r2', {}).get('init', cfg.get('r2_identity', {}).get('init'))
    return init_identity(value)


def check_init(spec, metadata):
    init = init_identity(spec.get('init'))
    if spec.get('contract') != CONTRACT:
        raise ValueError('Next-leg init identity differs from the accepted export')
    if spec.get('mode') != 'warm_start' or not spec.get('run_id') or spec['run_id'] == init['parent_run']:
        raise ValueError('Changed code or mixture requires a new warm-start run')
    for key in ('code_sha256', 'mixture_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', str(spec.get(key, ''))):
            raise ValueError('New run needs full code and mixture identities')
    if metadata.get('artifact_sha256') != init['artifact_sha256']:
        raise ValueError('EXPORT_ARTIFACT.json does not bind the accepted artifact sha256')
    # Only the parent configuration prefix survives. Do not invent the rest.
    for key in ('parent_run', 'parent_kit', 'step', 'parent_source_seal'):
        if key in metadata and metadata[key] != init[key]:
            raise ValueError('Export metadata contradicts ' + key)
    if 'parent_configuration' in metadata and not metadata['parent_configuration'].startswith(init['parent_configuration_prefix']):
        raise ValueError('Export parent configuration prefix differs')
    return deepcopy(spec)


def preparation(cfg):
    from .r2_scene_bindings import verify as verify_scenes
    verify_scenes(cfg)
    if 'geometry_connector' in cfg:
        from pathlib import Path
        from .r2_policy import preparation as policy_preparation
        policy_preparation(cfg['r2_build2'], Path.cwd())
        from .r2_openers import preparation as opener_preparation
        opener_preparation(cfg)
        if not cfg.get('r2_sampling'):
            raise ValueError('Missing bound r2_sampling table')
    spec = cfg.get('r2')
    if cfg.get('r2_membership') and spec is None:
        raise ValueError('Next-leg membership requires the init and new-run binding')
    if spec is not None:
        check_init(spec, load(pinned(spec['export_metadata'])))
        lineage_init(cfg.get('init_artifact', {}).get('artifact', {}), init=bound_init(cfg))
        if load(pinned(cfg['code'])).get('tree_sha256') != spec['code_sha256']:
            raise ValueError('New run code identity differs')
        if digest({key: cfg.get(key) for key in ('recipe', 'streams', 'route_table')}) != spec['mixture_sha256']:
            raise ValueError('New run mixture identity differs')
        Admission(cfg['r2_membership'])
    return spec


def lineage_init(pin, *, init):
    init = init_identity(init)
    if pin.get('sha256') == init['artifact_sha256']:
        return
    try:
        artifact = load(pinned(pin))
        if (artifact.get('schema') != 'carrier-c1-artifact-v1' or artifact.get('r2_identity', {}).get('init') != init
                or not isinstance(artifact.get('source_seal'),dict)):
            raise ValueError('Foreign lineage')
        from .source_seal import check_export
        check_export({'source_seal':artifact['training_source_seal']},artifact)
    except (ValueError, KeyError, OSError) as error:
        raise ValueError('Trainer init artifact differs from next-leg binding') from error


def expand_frames(inputs):
    result = deepcopy(inputs)
    prefix = result.pop('frame_prefix', None)
    if prefix is not None:
        from pathlib import PurePosixPath
        result['frames'] = [{**pin, 'path': str(PurePosixPath(prefix) / pin['path'])} for pin in result['frames']]
    return result


def frame_metadata(inputs):
    frames, indices = inputs.get('frames'), inputs.get('frame_indices')
    if (not isinstance(frames, list) or len(frames) != 32 or not isinstance(indices, list)
            or len(indices) != 32 or any(type(i) is not int or i < 0 for i in indices)
            or indices != sorted(set(indices)) or indices[0] != 0):
        raise ValueError('Expected ordered native frame pins and source ordinals')
    fps, total = inputs.get('fps'), inputs.get('total_num_frames')
    if (type(fps) not in (int, float) or not math.isfinite(fps) or fps <= 0
            or type(total) is not int or total <= indices[-1]):
        raise ValueError('Invalid row clock or source bounds')
    if inputs.get('timestamps') != [i/fps for i in indices]:
        raise ValueError('Row timestamps differ from its own clock')
    for pin in frames:
        if (not isinstance(pin, dict) or not isinstance(pin.get('path'), str)
                or not PurePosixPath(pin['path']).is_absolute() or '..' in PurePosixPath(pin['path']).parts
                or not re.fullmatch('[0-9a-f]{64}', str(pin.get('sha256', '')))):
            raise ValueError('Missing or malformed RGB pin')


def validate(row, stream, expected=None, require_frames=False):
    if expected is not None and digest(row) != expected:
        raise ValueError('Stale pin or wrong scene: row differs from membership')
    if not row.get('qid') or not row.get('dataset') or not row.get('scene'):
        raise ValueError('Row identity or scene is missing')
    inputs = expand_frames(row['student_input'])
    frame_metadata(inputs)
    if stream in ('vqa', 'routing'):
        kind = row.get('question_type', row.get('routing', {}).get('question_type'))
        if kind == 'route_planning' and stream != 'vqa':
            raise ValueError('D0 route-planning rows enter VQA only')
        if not isinstance(kind, str) or not kind:
            raise ValueError('Language row needs a question type')
        if row.get('events'):
            if stream != 'routing':
                raise ValueError('Programs enter only the masked routing event path')
            validate_program(row)
        else:
            if kind in PROGRAM_TYPES or row.get('tool_output_spans') or row.get('routing'):
                raise ValueError('Program-type row offered as direct')
            answer = validate_direct(row['target'], inputs['question'], len(inputs['frames']))
            if kind in ROOM:
                prose = row['target'].split('</think>', 1)[0]
                if re.search(r'converting|conversion|Step: compute|\d+(?:\.\d+)?\s*(?:square|sq\.?|m\^?2|ft\^?2)', prose, re.I):
                    raise ValueError('Direct room trace must remain qualitative without area or conversion')
            if answer.removeprefix('<answer>').removesuffix('</answer>') != str(row['answer']):
                raise ValueError('Answer differs from target')
            if kind in (*ROOM, 'object_size_estimation', 'camera_object_abs_distance', 'object_counting'):
                numeric = answer.removeprefix('<answer>').removesuffix('</answer>')
                if not re.fullmatch(r'\d+(?:\.\d+)?', numeric):
                    raise ValueError('Numeric direct type needs a numeric final answer')
            unit = row.get('answer_unit')
            if unit and kind in ROOM:
                if unit != asked_unit(dict(question_type=kind, student_input=inputs)):
                    raise ValueError('Wrong-unit target')
            if unit and unit not in {'m': ('m', 'meters', 'metres'), 'cm': ('cm', 'centimeters', 'centimetres'),
                                     'ft': ('ft', 'feet'), 'in': ('in', 'inch', 'inches'), 'ft2': ('square feet', 'square foot', 'sq ft'), 'm2': ('square meters', 'square metres')}:
                raise ValueError('Unknown answer unit')
            spellings = {'m': ('meters', 'metres'), 'cm': ('centimeters', 'centimetres'),
                         'ft': ('feet',), 'in': ('inch', 'inches'), 'ft2': ('square feet', 'square foot', 'sq ft'), 'm2': ('square meters', 'square metres')}
            if unit and not any(re.search(r'\b'+re.escape(s)+r'\b', inputs['question'], re.I) for s in (spellings[unit] if unit == 'in' else (*spellings[unit], unit))):
                raise ValueError('Wrong-unit target')
    elif stream not in ('pose', 'pointing'):
        raise ValueError('Unknown native stream')
    if require_frames:
        from .r2_frames import verify_frame
        for pin in inputs['frames']:
            verify_frame(pin)
    return inputs


def perception(row, stream, target):
    if stream == 'pose':
        import torch
        from .decoupled_v import target_tensors
        values = target_tensors(target, all_frames=True)
        if (values['aux_camera_target'].shape != (1, 32, 9)
                or any(not torch.isfinite(value).all() for value in values.values())):
            raise ValueError('Invalid native pose target')
    elif stream == 'pointing':
        value = json.loads(row['target'].split('</think>')[-1].strip())
        point = value.get('point_2d')
        if set(value) != {'point_2d'} or (point is not None and
                (not isinstance(point, list) or len(point) != 2 or any(type(v) is not int or not 0 <= v <= 1000 for v in point))):
            raise ValueError('Invalid native pointing target')


class Admission:
    def __init__(self, pin):
        from .r2_withheld import Withheld
        self.withheld = Withheld()
        self.manifest = load(pinned(pin))
        if self.manifest.get('contract') != CONTRACT:
            raise ValueError('Wrong membership contract')

    def check(self, row, stream, target=None):
        expected = self.manifest['rows'].get(row['qid'])
        if expected is None or expected != digest(dict(row=row, target=target, stream=stream)):
            raise ValueError('Row missing or changed in sealed membership')
        if self.withheld.touches(row, {}):
            raise ValueError('Native reader refuses a withheld room')
        from .r2_frames import verify_frame
        inputs = row['student_input']
        for pin in inputs.get('geometry_dense', inputs)['frames']:
            verify_frame(pin)
        return row


def event_row(row):
    """Reviewed R2 ground events, including failed-call continuations, use native spans."""
    from .ground_rows import render_ground, validate as validate_ground
    record = row.get('ground_record', {})
    if (row.get('schema') != 'derivgen-row-v2' or row.get('infrastructure_only') is not False
            or row.get('response_source') != 'ground_truth'
            or record.get('mask_source') != 'gt' or record.get('geometry_source') != 'gt'
            or record.get('gt_authority') == 'selector'
            or not re.fullmatch('[0-9a-f]{64}', row.get('provenance', {}).get('source_row_sha256', ''))):
        raise ValueError('R2 program lacks its event schema or response lineage')
    validate_ground(row)
    target, spans, _ = render_ground(row['events'], row['answer'])
    if target != row['target'] or spans != row['tool_output_spans']:
        raise ValueError('R2 events differ from target or response spans')
    failed = False
    for event in row['events']:
        if failed and event['kind'] == 'ground_call':
            raise ValueError('R2 fallback calls again after a failed response')
        if event['kind'] == 'ground_response' and re.search(r'not seen|failed|no linked candidate', event['text'], re.I):
            failed = True
    if failed and not re.search(r'\b(?:in frame|frame)\s+[1-9]\d*\b', target.split('</tool_response>')[-1], re.I):
        raise ValueError('Failed response needs a located direct continuation')
    return target, spans
