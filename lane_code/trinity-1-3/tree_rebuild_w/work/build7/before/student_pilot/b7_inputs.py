"""Launch input contracts. These checks never select or modify model answers."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re

SCHEMA = 'kit-inputs-v7'
SEALED_STORES = ('524b14f9', '9a7f3310')
READ_ORDER = ['ReVSI official999', 'VSI-Bench']


def pin(value, *, init=False, verify=False):
    if (not isinstance(value, dict) or not value.get('artifact_id') or
            not re.fullmatch('[0-9a-f]{64}', str(value.get('sha256', '')))):
        raise ValueError('unpinned_input')
    location = value.get('location', '')
    if not isinstance(location, str) or not location.startswith(('/', 'gs://', '~/')):
        raise ValueError('missing_real_location')
    if location == '/tmp' or location.startswith('/tmp/') or '/tmp/' in location:
        raise ValueError('temporary_input_source')
    if init and value.get('selected_by') != 'NEXT_LEG_INIT_RULE_20261116':
        raise ValueError('init_selection_rule_unbound')
    if verify:
        if location.startswith('gs://'):
            raise ValueError('stage_pinned_object_before_local_verification')
        with Path(location).expanduser().open('rb') as f:
            if hashlib.file_digest(f, 'sha256').hexdigest() != value['sha256']:
                raise ValueError('input_sha_mismatch')
    return value


def layout(value):
    result = {k:value.get(k) for k in ('max_pixels', 'min_pixels', 'frame_count', 'frame_layout', 'frame_markers')}
    if any(type(result[k]) is not int or result[k] <= 0 for k in ('max_pixels', 'min_pixels')):
        raise ValueError('processor_resolution_pin_missing')
    if result['min_pixels'] > result['max_pixels']:
        raise ValueError('processor_resolution_range')
    if result['frame_count'] not in (32, 64) or type(result['frame_count']) is not int:
        raise ValueError('frame_count_must_be_32_or_64')
    if result['frame_layout'] != 'duplicate' or result['frame_markers'] is not True:
        raise ValueError('training_frame_layout_mismatch')
    return result


def reader_layout(training, reader):
    if layout(training) != layout(reader):
        raise ValueError('reader_training_layout_mismatch')
    return layout(training)


def claim_reader(receipt=None):
    if not receipt:
        return 'harness_served'
    from .p3_provenance import pinned, load
    value = load(pinned(receipt))
    clauses = value.get('clauses', {})
    if value.get('test') != 'EAT-1' or set(clauses) != {'A1','A2','A3','A4','A5'} or any(v != 'PASS' for v in clauses.values()):
        raise ValueError('passing_EAT1_receipt_required')
    return 'model_served'


def row_stores(value, arm, verify=False):
    required = {'d0_v5', 'a0'} | ({'a2'} if arm == 'a2' else set())
    if not isinstance(value, dict) or set(value) != {'vqa','routing'}:
        raise ValueError('rows_lane_store_bindings_missing')
    for stream, entries in value.items():
        if not isinstance(entries, list) or {e.get('family') for e in entries} != required:
            raise ValueError('rows_lane_family_binding_missing:'+stream)
        for entry in entries:
            pin(entry, verify=verify)
            if any(entry['sha256'].startswith(s) or entry['artifact_id'].startswith(s) for s in SEALED_STORES):
                raise ValueError('sealed_row_store_refused:'+stream)
            if entry['family'] == 'd0_v5' and not (entry['sha256'].startswith('4af43b40') or entry['artifact_id'].startswith('4af43b40')):
                raise ValueError('d0_v5_identity_mismatch')
    return value


def blockers(value, arm):
    result = []
    for name, action in (
        ('init_selection_pending', lambda: pin(value.get('init'), init=True)),
        ('rows_lane_store_bindings_missing', lambda: row_stores(value.get('row_stores'), arm)),
        ('processor_resolution_pin_missing', lambda: layout(value)),
    ):
        try: action()
        except (ValueError, TypeError): result.append(name)
    if arm == 'a2':
        try: pin(value.get('dense_manifest'))
        except (ValueError, TypeError): result.append('gf1_real_dense_manifest_missing')
    return result


def validate(value, arm, verify=False):
    if value.get('schema') != SCHEMA or value.get('training_objective') != 'sft':
        raise ValueError('concrete_trace_sft_required')
    missing = blockers(value, arm)
    if missing: raise ValueError(','.join(missing))
    weight = value.get('weight_scale')
    if type(weight) not in (float,int) or not math.isfinite(weight) or weight <= 0:
        raise ValueError('positive_weight_scale_required')
    if type(value.get('minority_count')) is not int or value['minority_count'] <= 0:
        raise ValueError('positive_minority_count_required')
    pin(value['init'], init=True, verify=verify)
    row_stores(value['row_stores'], arm, verify=verify)
    if arm == 'a2': pin(value['dense_manifest'], verify=verify)
    return value


def configure(cfg, value, arm):
    value = deepcopy(value)
    cfg['b7_inputs'] = value
    cfg.update({k:value.get(k) for k in ('max_pixels','min_pixels','frame_count')})
    cfg.update(frame_layout='duplicate', frame_markers=True, all_frames=True,
               training_objective='sft', claim_reader=claim_reader(value.get('eat1_receipt')),
               read_order=READ_ORDER, room_claim=False)
    cfg['camera_overrides'] = {**cfg.get('camera_overrides', {}), 'weight_scale':value['weight_scale']}
    cfg['b7_blockers'] = blockers(value, arm)
    cfg['r2_identity']['claim_scope'] = ['ReVSI','VSI-Bench','VSTI']
    for stream in ('vqa','routing'):
        entries = (value.get('row_stores') or {}).get(stream)
        cfg['streams'][stream] = {'required_parameter':stream+'_row_stores', 'bindings':entries}
    return cfg


def module_trainability(model, cfg):
    """Record actual optimizer membership, including frozen parameters, by module."""
    from .carrier_c1 import parameter_groups
    groups = parameter_groups(model, model.recipe, inherited=getattr(model, 'inherited_pose_names', ()),
        pose_lr_scale=cfg.get('pose_lr_scale',1.), lm_lr_scale=cfg.get('lm_lr_scale',1.))
    rates = {id(p):g['lr'] for g in groups for p in g['params']}
    result = {k:[] for k in ('base_vit','merger','private_vit','pose_head','depth_head','lm','other')}
    for name,p in model.named_parameters():
        kind = ('private_vit' if name.startswith('auxiliary_heads.depth.model.visual.') else
                'depth_head' if name.startswith('auxiliary_heads.depth.') else
                'pose_head' if name.startswith('auxiliary_heads.pose.') else
                'merger' if name.startswith('model.visual.') and 'merger' in name else
                'base_vit' if name.startswith('model.visual.') else
                'other' if name.startswith('auxiliary_heads.') else 'lm')
        if p.requires_grad != (id(p) in rates): raise ValueError('optimizer_trainable_membership_mismatch')
        result[kind].append(dict(name=name, trainable=p.requires_grad, learning_rate=rates.get(id(p),0.)))
    return result


def assert_modules(model, cfg, expected):
    actual = module_trainability(model, cfg)
    if actual != expected: raise ValueError('trainable_module_pin_mismatch')
    return actual
