"""Derive export continuation from the donor's authenticated run bytes."""
from collections import Counter
from .p3_provenance import digest, load, pinned


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


def optimizer_contract(cfg):
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
    return result


def donor(cfg, artifact):
    """Read P's config, binding.json and preparation receipt, never a progress assertion."""
    value = cfg['r1_training']
    pins = value.get('p_run', {})
    for key, filename in (('config', 'config.json'), ('binding', 'binding.json'),
                          ('preparation', 'preparation/receipt.json'), ('checkpoint', 'complete.json')):
        if not pins.get(key):
            raise ValueError('P_EXPORT_RUN_FILE_REQUIRED:'+filename)
    source = load(pinned(pins['config']))
    identity = export_identity(source)
    if identity != artifact.get('config_sha256') or identity != value.get('donor_config_sha256'):
        raise ValueError('P_EXPORT_CONFIG_MISMATCH')
    preparation = load(pinned(pins['preparation']))
    bound = load(pinned(pins['binding']))
    complete = load(pinned(pins['checkpoint']))
    if (complete.get('schema') != 'c1-checkpoint-v1' or complete.get('step') != artifact.get('step')
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
        if stream.get('receipt') != receipt_pin or stream.get('database') != receipt.get('database'):
            raise ValueError('P_EXPORT_STORE_RECEIPT_MISMATCH:'+name)
        stores[name] = receipt['database']['sha256']
        counts[name] = stream['count']
        if stream.get('indices'):
            # P writes these post-filter row indices; no database or frames are copied.
            rows = load(pinned(stream['indices']))
            if (len(rows) != counts[name] or len(set(rows)) != len(rows)
                    or any(type(i) is not int or not 0 <= i < receipt['count'] for i in rows)):
                raise ValueError('P_EXPORT_INDEX_COUNT_MISMATCH:'+name)
            indices[name] = stream['indices']['sha256']
        elif counts[name] != receipt['count']:
            raise ValueError('P_EXPORT_RUN_FILE_REQUIRED:'+name+'_indices.json')
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
    target_optimizer = optimizer_contract(cfg)
    for key, setting in optimizer_contract(source).items():
        if setting != target_optimizer[key]:
            raise ValueError('P_EXPORT_LR_SCHEDULE_MISMATCH:'+key)
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
