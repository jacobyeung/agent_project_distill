"""Read-only checkpoint bridge for disposable measurements across a source reseal."""


def preflight(run, cfg, commit, pin, source_config=None):
    current = dict(config_sha256=run.identity(cfg), preparation=cfg['preparation'],
                   trainer_commit=commit, world_size=run.recipe_for(cfg)['world_size'])
    if not pin:
        return current
    saved = run.load(run.pinned(pin))
    if saved.get('schema') != 'c1-checkpoint-v1':
        raise ValueError('RESUME_PIN must pin a native completed checkpoint manifest')
    old = saved['binding']
    if old == current:
        return current
    if source_config is None:
        raise ValueError('RESUME_PIN binding differs: supply RESUME_CONFIG for the production '
                         'checkpoint, use a checkpoint under the same sealed patched config, '
                         'or run without RESUME_PIN')
    source = run.load(source_config)
    expected = dict(config_sha256=run.identity(source), preparation=source['preparation'],
                    trainer_commit=run.load(run.pinned(source['code']))['commit'],
                    world_size=run.recipe_for(source)['world_size'])
    if old != expected or old['world_size'] != current['world_size']:
        raise ValueError('Production checkpoint/config/world binding differs')
    # Only source provenance may change. identity already excludes admission,
    # authorization, preparation and R1 host/review receipts in the native trainer.
    if run.identity(dict(cfg, code=source['code'])) != run.identity(source):
        raise ValueError('Resume bridge refuses training configuration changes')
    def data_receipt(config):
        value = dict(run.load(run.pinned(config['preparation'])))
        for key in ('config_sha256', 'trainer_commit', 'source_seal'):
            value.pop(key, None)
        if 'r1_training' in value:
            value['r1_training'] = {k:v for k,v in value['r1_training'].items()
                                    if k not in ('host_receipt', 'review')}
        return value
    if data_receipt(source) != data_receipt(cfg):
        raise ValueError('Resume bridge refuses prepared data changes')
    # Native restore still validates schema, layout, every shard pin, buffers and
    # RNG. Its checkpoint binding remains exactly the original production binding.
    # Native authenticate and allocation admission still validate the new tree.
    return old
