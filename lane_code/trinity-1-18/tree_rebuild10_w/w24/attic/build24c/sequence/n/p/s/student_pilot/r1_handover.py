"""Derive export continuation from the donor's authenticated run bytes."""
from collections import Counter
from .p3_provenance import digest, load, pinned

# These keys describe the handover boundary, not a trainable topology or loss.
HANDOVER_VARIABLE_KEYS = frozenset(('streams', 'mix', 'preparation', 'r2_sampling',
    'r1_training', 'init_artifact', 'output', 'preparation_output', 'admission',
    'authorization', 'milestone_gate', 'code', 'r2_identity', 'routing_vocabulary',
    'routing_opener_init'))

HANDOVER_ROW_KEYS = {
    'dev_scene_exclusions': 'N preparation rechecks the held-out scene exclusions.',
    'remove_files': 'N preparation and reader reapply pinned row removals.',
    'scene_division': 'N preparation rebinds the admitted train scenes.',
    'extent_receipt': 'N routing intake rebinds numeric row evidence.',
    'scene_coverage': 'N preparation rechecks scene coverage.',
    'type_mix': 'N population producer counts cells and binds the row plan.',
    's1_routing': 'N native routing builder composes a new admitted store.',
    's1_route_policy': 'N preparation authenticates the table; route_table remains compared.',
    'h1': 'N preparation rebinds row filters and bookkeeping; active own-row mode stays compared.',
    'continuation': 'P checkpoint provenance is replaced by N authenticated handover progress.',
    'milestones': 'N recipe rebinds export timing, without changing optimizer or loss.',
    'checkpoint_disk_guard': 'N disk preflight rebinds checkpoint storage accounting.',
    'r2_all_stream_exclusions': 'N preparation rechecks exclusions across every stream.',
    'r2_scene_rebuild': 'N preparation rebinds scene-filtered stream receipts.',
}
HANDOVER_VARIABLE_KEYS |= HANDOVER_ROW_KEYS.keys()


def bind_target(cfg, output):
    """Rebind authenticated continuation when native preparation changes target stores."""
    from copy import deepcopy
    from pathlib import Path
    from . import r1_training as training
    from .p3_provenance import write, file_pin
    cfg = deepcopy(cfg)
    value = cfg['r1_training']
    artifact = load(pinned(cfg['init_artifact']['artifact']))
    source, _, actual, _ = donor(cfg, artifact)
    compare_configs(source, cfg)
    target = training.target_identity(cfg)
    value.update(store_hashes=target['stores'],row_plan_sha256=digest(cfg.get('r2_sampling')))
    value['continuation_identity'] = training.target_identity(cfg)['config_identity']
    expected = training.boundary(cfg,artifact['step'])
    path = Path(output)
    write(path,dict(schema='r1-handover-map-v1',artifact_sha256=cfg['init_artifact']['artifact']['sha256'],
                    step=artifact['step'],source=actual,target={key:expected[key] for key in actual}))
    value['handover_mapping'] = file_pin(path)
    return cfg

# Only defaults actually used by the trainer are normalized. Unknown missing keys refuse.
EFFECTIVE_DEFAULTS = {
    'frame_count': 32,  # carrier_c1_run.py:811: receipt.get('frame_count',32).
    'max_pixels': None,  # carrier_c1_data.py:209: DEFAULT_PIXELS outside b7_inputs.
    'min_pixels': None,  # carrier_c1_data.py:209: DEFAULT_PIXELS outside b7_inputs.
    'geometry_connector': 'none',  # carrier_c1_run.py:813-815: geometry_online alone attaches it.
}


def metadata_load(pin, replicas):
    """A local replica changes only the path; pinned still verifies the original hash."""
    return load(pinned({**pin, 'path': replicas.get(pin['sha256'], pin['path'])}))


def stream_identity(receipt, name):
    """Bind a composite stream to its ordered sources, division and layout."""
    import re
    def check(pin):
        if (not isinstance(pin, dict) or set(pin) != {'path', 'sha256'}
                or not isinstance(pin['path'], str) or not pin['path']
                or not re.fullmatch('[0-9a-f]{64}', str(pin['sha256']))):
            raise ValueError('P_EXPORT_TARGET_STORE_INVALID:'+name)
    if receipt.get('schema') == 'c1-pose-mix-v1':
        from .c1_pose_mix import validate_spec
        validate_spec(receipt)
        if name != 'pose' or set(receipt) - {'schema', 'sources', 'division'}:
            raise ValueError('P_EXPORT_TARGET_STORE_INVALID:'+name)
        if 'division' in receipt:
            check(receipt['division'])
        for source in receipt['sources']:
            for key in (('receipt',) if source['kind'] == 'rows' else ('clips_plan', 'dense_plan', 'teacher', 'model')):
                check(source[key])
        return digest(pin_values(receipt))
    check(receipt.get('database'))
    return receipt['database']['sha256']


def prepared_stream_identity(receipt, stream, name):
    """Authenticate the prepared mix without opening its row databases."""
    identity = stream_identity(receipt, name)
    if receipt.get('schema') != 'c1-pose-mix-v1':
        if stream.get('database') != receipt.get('database'):
            raise ValueError('P_EXPORT_STORE_RECEIPT_MISMATCH:'+name)
        return identity, receipt['count']
    value = stream.get('scene_source', stream)
    if (value.get('kind') != 'mix' or len(value.get('sources', [])) != len(receipt['sources'])
            or value.get('division') != receipt.get('division')):
        raise ValueError('P_EXPORT_STORE_RECEIPT_MISMATCH:'+name)
    limits = []
    for source, part in zip(receipt['sources'], value['sources']):
        keys = ('kind', 'receipt', 'frame_prefix') if source['kind'] == 'rows' else tuple(source)
        if any(part.get(k) != source[k] for k in keys):
            raise ValueError('P_EXPORT_STORE_RECEIPT_MISMATCH:'+name)
        if source['kind'] == 'rows':
            child = load(pinned(source['receipt']))
            if child.get('database') != part.get('database'):
                raise ValueError('P_EXPORT_STORE_RECEIPT_MISMATCH:'+name)
            limits.append(child['count'])
        else:
            limits.append(source['count'])
    order = load(pinned(value['order']))
    if (len(order) != value['count'] or len({tuple(v) for v in order}) != len(order)
            or any(len(v) != 2 or any(type(i) is not int for i in v)
                   or not 0 <= v[0] < len(limits) or not 0 <= v[1] < limits[v[0]] for v in order)
            or any(sum(v[0] == k for v in order) != part['count'] for k, part in enumerate(value['sources']))):
        raise ValueError('P_EXPORT_INDEX_COUNT_MISMATCH:'+name)
    if stream is not value:
        selected = load(pinned(stream['order']))
        if (len(selected) != stream['count'] or len({tuple(v) for v in selected}) != len(selected)
                or not {tuple(v) for v in selected} <= {tuple(v) for v in order}):
            raise ValueError('P_EXPORT_INDEX_COUNT_MISMATCH:'+name)
    return identity, stream['count']


def effective_camera(cfg, candidates, replicas):
    """Preparation stores the source camera settings before runtime overrides."""
    pose = cfg.get('streams', {}).get('pose', {}).get('sha256')
    for pin in ([cfg['preparation']] if cfg.get('preparation') else []) + list(candidates):
        receipt = metadata_load(pin, replicas)
        if (receipt.get('schema') == 'c1-preparation-v1' and pose is not None
                and receipt.get('streams', {}).get('pose', {}).get('receipt', {}).get('sha256') == pose):
            return {**receipt['camera'], **cfg.get('camera_overrides', {})}
    raise ValueError('P_EXPORT_CAMERA_METADATA_UNVERIFIED')


def pin_values(value):
    """A file identity is its digest; non-pin dictionaries retain every key."""
    if isinstance(value, dict):
        if set(value) == {'path', 'sha256'}:
            import re
            if re.fullmatch('[0-9a-f]{64}', str(value['sha256'])):
                return {'sha256': value['sha256']}
        return {k: pin_values(v) for k, v in value.items()}
    if isinstance(value, list):
        return [pin_values(v) for v in value]
    return value


def compare_configs(source, target, *, metadata=(), replicas=None):
    """Unknown and nested config differences refuse before a mapping can apply."""
    # P's policy initialized P from its parent; N must preserve P's trained rows.
    if (target.get('init_artifact') or 'routing_opener_init' in target) and target.get('routing_opener_init', 'reset') != 'keep':
        raise ValueError('P_EXPORT_ROUTING_OPENER_KEEP_REQUIRED:routing_opener_init')
    replicas = replicas or {}
    target_optimizer = optimizer_contract(target, replicas=replicas)
    for key, setting in optimizer_contract(source, replicas=replicas).items():
        if pin_values(setting) != pin_values(target_optimizer[key]):
            raise ValueError('P_EXPORT_LR_SCHEDULE_MISMATCH:'+key)
    candidates = tuple(metadata) + tuple(c['preparation'] for c in (source, target) if c.get('preparation'))
    keys = set(source) | set(target)
    if candidates:
        keys.add('camera_overrides')
    for key in sorted(keys):
        if key == 'h1':
            # These are the only audited H1 row/bookkeeping settings. Future knobs refuse.
            known = {'faithful_own_camera_rows', 'camera_types', 'routing_pose_targets',
                     'r0_rooms', 'metrics', 'stop_after_step'}
            a, b = source.get(key, {}), target.get(key, {})
            if ((set(a) | set(b)) - known or
                    a.get('faithful_own_camera_rows', False) != b.get('faithful_own_camera_rows', False)):
                raise ValueError('P_EXPORT_CONFIG_DIFFERENCE:h1')
        if key in HANDOVER_VARIABLE_KEYS:
            continue
        if (key not in source or key not in target) and key not in EFFECTIVE_DEFAULTS and key != 'camera_overrides':
            raise ValueError('P_EXPORT_CONFIG_DIFFERENCE:'+key)
        a, b = source.get(key, EFFECTIVE_DEFAULTS.get(key)), target.get(key, EFFECTIVE_DEFAULTS.get(key))
        if key == 'camera_overrides':
            a, b = source.get(key, {}), target.get(key, {})  # carrier_c1_run.py:716.
        if key == 'camera_overrides' and (a != b or candidates):
            a, b = (effective_camera(c, candidates, replicas) for c in (source, target))
        if key == 'recipe':
            # Stream mixture and export timing are rebound; every loss/schedule knob stays.
            a = {k:v for k,v in (a or {}).items() if k not in ('mix', 'milestones')}
            b = {k:v for k,v in (b or {}).items() if k not in ('mix', 'milestones')}
        if pin_values(a) != pin_values(b):
            raise ValueError('P_EXPORT_CONFIG_DIFFERENCE:'+key)


def donor_meta_model(cfg):
    """Construct P's native topology from authenticated P metadata, without weights."""
    import torch
    from pathlib import Path
    from transformers import Qwen3_5Config, Qwen3_5ForConditionalGeneration
    from .carrier_c1 import CarrierC1
    from .carrier_c1_sweep import recipe_for
    receipt = load(pinned(cfg['preparation']))
    try:
        manifest = load(pinned(receipt['model']))
        model_config = load(pinned(dict(path=str(Path(manifest['root'])/'config.json'),
                                       sha256=manifest['files']['config.json'])))
        camera = {**receipt['camera'], **cfg.get('camera_overrides', {})}
        depth = receipt['depth']
    except (KeyError, OSError, ValueError) as error:
        raise ValueError('P_EXPORT_TOPOLOGY_METADATA_UNVERIFIED') from error
    if cfg.get('geometry_online') or cfg.get('mdg'):
        raise ValueError('P_EXPORT_TOPOLOGY_UNSUPPORTED')
    with torch.device('meta'):
        config = Qwen3_5Config(**model_config)
        for item in (config, config.text_config, config.vision_config):
            item._attn_implementation = 'sdpa'
        model = CarrierC1(Qwen3_5ForConditionalGeneration(config), camera, depth, 0,
            cfg['carrier_placement'], cfg['training_mode'], cfg.get('depth_enabled', True),
            recipe_for(cfg), cfg.get('skip_unsupervised_lm'), cfg.get('frame_layout', 'spread'),
            cfg.get('depth_fov_source', 'private'), frame_count=cfg.get('frame_count', 32),
            heading_plane_min=cfg.get('heading_plane_min', .3))
        if cfg.get('align'):
            from .c1r_align import attach
            attach(model, cfg['align'], training=True)
        if cfg.get('depth_init'):
            # Native load_depth_stage1 changes only this requires_grad topology.
            pinned(cfg['depth_init'])
            model.auxiliary_heads.depth.model.visual.requires_grad_(False)
    return model


def export_identity(cfg):
    value = {k: v for k, v in cfg.items() if k not in
             ('preparation', 'admission', 'authorization', 'milestone_gate')}
    if 'readout' in value:
        value['readout'] = {k: v for k, v in value['readout'].items() if k != 'contiguous_clips'}
    if value.get('frame_layout') == 'spread':
        value.pop('frame_layout')
    return digest(value)


def sealed_identity(cfg):
    """Continuation identity includes the preparation omitted by the sealed export."""
    return digest(dict(config_sha256=export_identity(cfg), preparation=cfg.get('preparation')))


def optimizer_contract(cfg, *, replicas=None):
    """All configurable optimizer inputs on the sealed carrier training path."""
    from .carrier_c1_sweep import recipe_for
    recipe = recipe_for(cfg)
    result = {key: recipe.get(key) for key in
              ('steps', 'warmup_ratio', 'learning_rate', 'lm_learning_rate',
               'encoder_learning_rate', 'geometry_learning_rate', 'weight_decay')}
    result.update(lm_lr_scale=cfg.get('lm_lr_scale', 1.0),
                  pose_lr_scale=cfg.get('pose_lr_scale', 1.0))
    # Extension dictionaries select groups, rates, ramps and alignment schedules.
    # R1 forbids geometry extensions; compare them before any mapping regardless.
    for key in ('mdg', 'geometry_online'):
        result[key] = cfg.get(key)
    # AdamW betas and the MDG LoRA decay are constants in the sealed producer.
    result['betas'] = (0.9, 0.999)
    result['mdg_lora_weight_decay'] = 0.0
    result['depth_init'] = cfg.get('depth_init')
    result['head_init'] = head_init(cfg, replicas=replicas)
    return result


def head_init(cfg, *, replicas=None):
    """Read the pinned initialization artifact, not an operator's summary."""
    spec = cfg.get('init_artifact')
    if not spec:
        return None
    try:
        return metadata_load(spec['artifact'], replicas or {}).get('head_init') or None
    except (OSError, KeyError, ValueError) as error:
        raise ValueError('P_EXPORT_HEAD_INIT_UNVERIFIED') from error


def trainable_group_table(cfg, model):
    """Use the trainer's group builder and live parameter topology without copies."""
    from .carrier_c1 import parameter_groups, RECIPE
    from .carrier_c1_run import gx_recipe, inherited_head_names
    names = {id(p): name for name, p in model.named_parameters()}
    groups = parameter_groups(model, inherited=inherited_head_names(cfg.get('init_artifact') or {},
        head_init(cfg) or {}), pose_lr_scale=cfg.get('pose_lr_scale', 1.0),
        lm_lr_scale=cfg.get('lm_lr_scale', 1.0), **gx_recipe(model))
    table = []
    for group in groups:
        members = sorted((names[id(p)], p.numel()) for p in group['params'])
        table.append(dict(name=group['name'], members=members, tensors=len(members),
            parameters=sum(count for _, count in members), initial_lr=group['initial_lr'],
            weight_decay=group.get('weight_decay', RECIPE['weight_decay'])))
    frozen = sorted(name for name, p in model.named_parameters() if not p.requires_grad)
    modules = sorted(name for name, module in model.named_modules()
        if any(True for _ in module.parameters()) and not any(p.requires_grad for p in module.parameters()))
    return dict(groups=table, frozen_parameters=frozen, frozen_modules=modules)


def verify_trainable_groups(cfg, model):
    """Gate P continuation before wrapping or optimizer creation; never alter weights."""
    value = cfg.get('r1_training') or {}
    if not value.get('p_run'):
        return None
    artifact = load(pinned(cfg['init_artifact']['artifact']))
    source, _, _, _ = donor(cfg, artifact)
    compare_configs(source, cfg)
    tables = dict(source=trainable_group_table(source, donor_meta_model(source)),
                  target=trainable_group_table(cfg, model))
    if tables['source'] != tables['target']:
        raise ValueError('P_EXPORT_TRAINABLE_GROUP_MISMATCH')
    return tables


def donor(cfg, artifact):
    value = cfg['r1_training']
    if 'persisted_files' in value:
        from .r1_persisted import verify, scope, init_policy
        result = verify(value.get('handover_receipt'), value.get('p_run', {}),
                        cfg['init_artifact']['artifact'], value['persisted_files'], proof_mode=value.get('proof_mode'),init_policy=init_policy(value))
        with scope(result['paths']):
            if artifact != load(pinned(cfg['init_artifact']['artifact'])):
                raise ValueError('P_EXPORT_HANDOVER_ARTIFACT_MISMATCH')
            return _donor(cfg, artifact)
    return _donor(cfg, artifact)


def _donor(cfg, artifact):
    """Read P's config, binding.json and preparation receipt, never a progress assertion."""
    value = cfg['r1_training']
    pins = value.get('p_run', {})
    from .r1_persisted import export_only, init_policy
    receipt = None
    if value.get('handover_receipt'):
        try:
            receipt = load(pinned(value['handover_receipt']))
        except (OSError, ValueError) as error:
            raise ValueError('P_EXPORT_HANDOVER_RECEIPT_UNVERIFIED') from error
    only = export_only(receipt, value.get('proof_mode'), init_policy=init_policy(value)) if receipt is not None else False
    for key, filename in (('config', 'config.json'), ('binding', 'binding.json'),
                          ('preparation', 'preparation/receipt.json'), ('checkpoint', 'complete.json')):
        if only and key == 'checkpoint':
            continue
        if not pins.get(key):
            raise ValueError('P_EXPORT_RUN_FILE_REQUIRED:'+filename)
    source = load(pinned(pins['config']))
    identity = export_identity(source)
    if identity != artifact.get('config_sha256') or identity != value.get('donor_config_sha256'):
        raise ValueError('P_EXPORT_CONFIG_MISMATCH')
    preparation = load(pinned(pins['preparation']))
    bound = load(pinned(pins['binding']))
    complete = {} if only else load(pinned(pins['checkpoint']))
    if not only and (complete.get('schema') != 'c1-checkpoint-v1' or complete.get('step') != artifact.get('step')
            or complete.get('binding') != bound):
        raise ValueError('P_EXPORT_CHECKPOINT_BINDING_MISMATCH')
    if (source.get('preparation') != pins['preparation'] or bound.get('preparation') != pins['preparation']
            or bound.get('config_sha256') != identity or preparation.get('config_sha256') != identity
            or preparation.get('schema') != 'c1-preparation-v1'):
        raise ValueError('P_EXPORT_RUN_BINDING_MISMATCH')
    from .carrier_c1_sweep import recipe_for
    recipe = recipe_for(source)
    if (preparation.get('recipe') != source.get('recipe')
            or bound.get('world_size') != recipe['world_size']
            or preparation.get('training_mode') != source.get('training_mode', 'mixed')):
        raise ValueError('P_EXPORT_RECIPE_MISMATCH')
    stores, counts, indices = {}, {}, {}
    for name, stream in preparation['streams'].items():
        receipt_pin = source['streams'][name]
        receipt = load(pinned(receipt_pin))
        if stream.get('receipt') != receipt_pin:
            raise ValueError('P_EXPORT_STORE_RECEIPT_MISMATCH:'+name)
        stores[name], source_count = prepared_stream_identity(receipt, stream, name)
        counts[name] = stream['count']
        if receipt.get('schema') == 'c1-pose-mix-v1':
            indices[name] = stream['order']['sha256']
        if stream.get('indices'):
            # P writes these post-filter row indices; no database or frames are copied.
            rows = load(pinned(stream['indices']))
            if (len(rows) != counts[name] or len(set(rows)) != len(rows)
                    or any(type(i) is not int or not 0 <= i < source_count for i in rows)):
                raise ValueError('P_EXPORT_INDEX_COUNT_MISMATCH:'+name)
            indices[name] = stream['indices']['sha256']
        elif counts[name] != source_count:
            raise ValueError('P_EXPORT_RUN_FILE_REQUIRED:'+name+'_indices.json')
    if 'persisted_files' in value or only:
        from .r1_persisted import verify
        verify(value.get('handover_receipt'), pins, cfg['init_artifact']['artifact'], value.get('persisted_files', {}),
               proof_mode=value.get('proof_mode'),init_policy=init_policy(value))
    else:
        from launch_r1.p_handover_receipt import verify_receipt
        verify_receipt(value.get('handover_receipt'), pins, cfg['init_artifact']['artifact'])
    # Sealed run_steps calls mixed_indices without a seed argument: its default is 17.
    plan = dict(schema='sealed-c1-row-plan-v1', seed=17, counts=list(counts.items()),
                indices=indices, training_mode=source.get('training_mode', 'mixed'),
                mix=recipe['mix'], world=recipe['world_size'], offset=source.get('row_start_step', 0))
    return source, recipe, dict(config_identity=sealed_identity(source), stores=stores, row_plan_sha256=digest(plan)), plan


def progress(cfg, artifact):
    from .r1_training import boundary
    from .carrier_c1_data import mixed_indices
    from .carrier_c1_sweep import recipe_for
    source, recipe, actual, plan = donor(cfg, artifact)
    compare_configs(source, cfg)
    expected = boundary(cfg, artifact.get('step'))
    # The sealed sampler has no cell-plan extension. Unknown variants must record their own plan.
    if source.get('r2_sampling') or source.get('r1_training') or plan['offset']:
        raise ValueError('P_EXPORT_SAMPLER_UNSUPPORTED:run must write an authenticated sampler implementation')
    positions = Counter()
    next_plan = None
    for index, rows in enumerate(mixed_indices(dict(plan['counts']), expected['step']+1,
            seed=plan['seed'], training_mode=plan['training_mode'], mix=plan['mix'], world=plan['world'])):
        if index == expected['step']:
            next_plan = rows
        else:
            for name, values in rows:
                positions[name] += len(values)
    if dict(positions) != expected['sampler_positions']:
        raise ValueError('P_EXPORT_SAMPLER_POSITION_MISMATCH')
    target = {k: expected[k] for k in actual}
    if actual != target:
        pin = cfg['r1_training'].get('handover_mapping')
        if not pin:
            raise ValueError('P_EXPORT_PROGRESS_MISMATCH:explicit sha-bound handover_mapping required')
        mapping = load(pinned(pin))
        if mapping != dict(schema='r1-handover-map-v1', artifact_sha256=cfg['init_artifact']['artifact']['sha256'],
                           step=expected['step'], source=actual, target=target):
            raise ValueError('P_EXPORT_MAPPING_MISMATCH')
    return dict(expected, donor=actual, donor_row_plan=plan, sampler_positions=dict(positions),
                donor_next_plan_sha256=digest(next_plan))
