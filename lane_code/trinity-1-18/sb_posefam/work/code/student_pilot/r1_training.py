"""R1 training-input contracts. These functions never serve model answers."""
from copy import deepcopy
import re
from .p3_provenance import digest, load, pinned

PARENT = '1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
STREAMS = {'pose': 64, 'vqa': 128, 'routing': 64, 'pointing': 32}
SCALE = ('pose.head.scale_branch.', 'pose.head.scale_token')


def row_check(row, stream):
    from .row_text_audit import check
    check(row, stream)
    provenance = row.get('provenance', {})
    if (row.get('response_source') in ('own', 'predicted') or
            row.get('own_valued') or provenance.get('geometry_source') in ('own', 'predicted') or
            (row.get('ground_record') or {}).get('geometry_mode') in ('own', 'predicted')):
        raise ValueError('OWN_VALUED_ROW_REFUSED')
    if stream not in ('vqa', 'routing'):
        return row
    kind = row.get('question_type', row.get('category'))
    text = row.get('target', row.get('suffix', ''))
    if kind in ('camera_object_absolute_distance', 'camera_object_abs_distance', 'camera_obj_abs_dist'):
        raise ValueError('CAMERA_OBJECT_ABSOLUTE_DISTANCE_EXCLUDED')
    if not isinstance(text, str) or '<think>' not in text or '</think>' not in text:
        raise ValueError('QUALITATIVE_TRACE_REQUIRED')
    if kind in ('room_size_estimation', 'absolute_size_room'):
        if stream == 'routing' or '<ground' in text or '<tool_response>' in text:
            raise ValueError('ROOM_PROGRAM_REFUSED')
        thought = text.split('<think>', 1)[1].split('</think>', 1)[0]
        if len(re.findall(r'\bframe\s+\d+\b', thought, re.I)) < 2 or len(thought.strip().splitlines()) < 3:
            raise ValueError('ONE_LINE_ROOM_REFUSED')
        from .trace_grammar import validate_row
        errors = validate_row({**row, 'form':'direct', 'target':text})
        if errors:
            raise ValueError('ROOM_TRACE_INVALID:'+','.join(sorted({e.rule_id for e in errors})))
    return row


def training_components(registry_pin, cfg, root=None):
    """Keep the complete registry; only an absent fusion connector is out of scope."""
    from .r2_policy import slots, record, CHOICES
    from .r2_portable import bound
    registry = load(bound(registry_pin, root))
    expected = slots()
    if set(registry) != set(expected):
        raise ValueError('Component registry differs')
    if cfg.get('geometry_connector') != 'none' or cfg.get('geometry_online'):
        raise ValueError('R1_FUSION_REFUSED')
    from .r1_components import deferred
    pending = deferred(cfg, root=root)
    result = {}
    for name, spec in expected.items():
        entry = registry[name]
        if any(entry.get(k) != spec[k] for k in ('component', 'component_class', 'phase', 'expected_schema')):
            raise ValueError('Component slot was reclassified')
        if pending is not None and name in pending:
            result[name] = pending[name]
            continue
        if name in CHOICES or name == 'heads_gf1_connector':
            continue
        result[name] = record(entry, root)
    return result


def validate(cfg):
    value = cfg['r1_training']
    if value.get('schema') != 'r1-training-v1' or value.get('s2') is not False:
        raise ValueError('R1_S2_MUST_BE_OFF')
    if cfg.get('geometry_connector') != 'none' or cfg.get('geometry_online') or cfg.get('r2_schedule'):
        raise ValueError('R1_FUSION_REFUSED')
    from .carrier_c1_sweep import recipe_for
    recipe = recipe_for(cfg)
    if recipe['steps'] != 1000 or recipe['world_size'] != 4 or recipe['global_batch'] != 288:
        raise ValueError('R1_RECIPE_DIFFERS')
    if recipe.get('scheduled_sampling', {}).get('max_own_probability') != 0:
        raise ValueError('R1_OWN_PROBABILITY_REFUSED')
    if cfg.get('h1', {}).get('faithful_own_camera_rows'):
        raise ValueError('R1_OWN_ROWS_REFUSED')
    if (cfg.get('frame_count'), cfg.get('frame_layout'), cfg.get('frame_markers')) != (32, 'duplicate', True):
        raise ValueError('R1_FRAME_LAYOUT_DIFFERS')
    card = load(pinned(value['mix']))
    scale = value.get('weight_scale')
    import math
    if (type(scale) not in (int, float) or not math.isfinite(scale) or scale < 0
            or card.get('weight_scale') != scale
            or cfg.get('camera_overrides', {}).get('weight_scale') != scale):
        raise ValueError('R1_SCALE_WEIGHT_DIFFERS')
    if cfg.get('camera_overrides') != {'weight_scale': scale, 'weight_focal': 2.0}:
        raise ValueError('R1_CAMERA_OVERRIDES_DIFFER')
    stop = value.get('stop_after_step')
    if stop is not None and (type(stop) is not int or not 1 <= stop <= 1000):
        raise ValueError('R1_STOP_STEP_INVALID')
    if recipe['milestones'] != [100, 200, 400, 600, 800, 1000]:
        raise ValueError('R1_MILESTONES_DIFFER')
    return value


def target_identity(cfg):
    """Derive the target from config contents and SHA-verified stream receipts."""
    canonical = deepcopy({k:v for k,v in cfg.items() if k not in ('preparation','admission','authorization','milestone_gate')})
    canonical['r1_training'] = {k: v for k, v in canonical['r1_training'].items()
        if k not in ('continuation_identity', 'store_hashes', 'handover_mapping', 'host_receipt', 'review')}
    stores = {}
    from .r1_handover import stream_identity
    for name, pin in cfg['streams'].items():
        receipt = load(pinned(pin))
        stores[name] = stream_identity(receipt, name)
    return dict(config_identity=digest(canonical), stores=stores)


def boundary(cfg, step):
    """Export-side progress, including each stream's absolute sampling position."""
    value = cfg['r1_training']
    if any(not re.fullmatch('[0-9a-f]{64}',str(value.get(k) or ''))
           for k in ('continuation_identity','row_plan_sha256')):
        raise ValueError('R1_CONTINUATION_IDENTITIES_REQUIRED')
    if type(step) is not int or not 0 <= step <= 1000:
        raise ValueError('R1_PROGRESS_STEP_INVALID')
    target = target_identity(cfg)
    if value['continuation_identity'] != target['config_identity']:
        raise ValueError('P_EXPORT_TARGET_CONFIG_MISMATCH')
    if value.get('store_hashes') != target['stores']:
        raise ValueError('P_EXPORT_TARGET_STORES_MISMATCH')
    return dict(schema='r1-progress-v1', step=step, schedule_step=step,
                config_identity=target['config_identity'],
                stores=target['stores'], row_plan_sha256=value['row_plan_sha256'],
                sampler_positions={s: step*n for s, n in STREAMS.items()})


def start(cfg):
    value = cfg.get('r1_training') or {}
    if 'persisted_files' in value:
        from .r1_persisted import verify, scope
        result = verify(value.get('handover_receipt'),value.get('p_run',{}),
                        cfg['init_artifact']['artifact'],value['persisted_files'],proof_mode=value.get('proof_mode'))
        with scope(result['paths']):
            return _start(cfg)
    return _start(cfg)


def _start(cfg):
    """A parent starts a new schedule; an R1 export must prove continuation."""
    spec = cfg['init_artifact']['artifact']
    artifact = load(pinned(spec))
    if artifact.get('schema') != 'carrier-c1-artifact-v1':
        raise ValueError('R1_EXPORT_FORMAT_DIFFERS')
    if spec['sha256'] == PARENT:
        if artifact.get('step') != 544:
            raise ValueError('R1_PARENT_STEP_DIFFERS')
        return 0
    from .r1_handover import progress
    return progress(cfg, artifact)['step']


def scale_init(live, selected, *, enabled=False):
    """Only a wholly absent scale branch keeps the seeded model initialization."""
    if not enabled:
        return set()
    names = {k for k in live if k.startswith(SCALE)}
    present = names & set(selected)
    if present and present != names:
        raise ValueError('PARTIAL_SCALE_HEAD_REFUSED')
    return names if not present else set()


def store_parameter(pin):
    value = load(pinned(pin))
    if (value.get('schema') != 'c1-stream-v1' or value.get('stream') != 'vqa'
            or type(value.get('count')) is not int or value['count'] <= 0
            or not re.fullmatch('[0-9a-f]{64}', value.get('database', {}).get('sha256', ''))):
        raise ValueError('VQA_RECEIPT_INVALID')
    return dict(receipt=pin, database=value['database'], count=value['count'])


def configure_store(cfg, receipt_pin):
    """One receipt parameter supplies every derived VQA identity."""
    binding = store_parameter(receipt_pin)
    cfg = deepcopy(cfg)
    cfg['streams']['vqa'] = binding['receipt']
    cfg['r1_training']['store_parameter'] = binding['receipt']
    cfg['r1_training']['store_hashes']['vqa'] = binding['database']['sha256']
    return cfg
