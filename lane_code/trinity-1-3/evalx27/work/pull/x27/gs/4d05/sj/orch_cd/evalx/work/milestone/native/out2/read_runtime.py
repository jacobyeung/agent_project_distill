from copy import deepcopy
from pathlib import Path

from common import checked, load, local, sha, install_tree


FIELDS = ('carrier_placement', 'training_mode', 'depth_enabled', 'recipe',
          'skip_unsupervised_lm', 'depth_fov_source', 'depth_init',
          'tool_mode_flag', 'ground_target_filter')


def metadata(pin):
    path = local(pin['path'])
    if path.suffix != '.json' or path.stat().st_size > 16*1024**2:
        raise ValueError('Inference admission accepts small JSON metadata only')
    return load(checked(pin))


def prepared(config_pin, artifact_pin, data_pin):
    install_tree()
    from student_pilot import carrier_c1_run as trainer
    from student_pilot import source_seal, trace_version
    from student_pilot.s1_route_policy import validate as route_policy
    cfg = metadata(config_pin)
    artifact = metadata(artifact_pin)
    data = metadata(data_pin)
    if any(name in data and type(data[name]) is not bool
           for name in ('production_authorized', 'gpu_first_step_pending')):
        raise ValueError('Preparation flags must be booleans; they do not authorize a GPU read')
    if (data.get('schema') != 's1-in-job-data-v1' or data.get('status') != 'PREPARED'
            or data.get('synthetic', False) is not False
            or data.get('rehearsal') is not False or data.get('real_frames_verified') is not True
            or data.get('config') != config_pin or data.get('preparation') != cfg.get('preparation')):
        raise ValueError('The mirrored production data receipt does not bind this prepared configuration')
    trainer.validate(cfg)
    commit = trainer.authenticate(cfg)
    receipt = metadata(cfg['preparation'])
    identity = trainer.identity(cfg)
    if (receipt.get('schema') != 'c1-preparation-v1'
            or receipt.get('config_sha256') != identity or artifact.get('config_sha256') != identity
            or receipt.get('trainer_commit') != commit or artifact.get('base_identity') != cfg['base_identity']):
        raise ValueError('Derived configuration, preparation or export identity differs')
    if set(cfg.get('streams', {})) != {'pose', 'pointing', 'routing', 'vqa'}:
        raise ValueError('The no-MDG reader requires the four production streams')
    if any('mdg' in value or 'geometry_online' in value for value in (cfg, receipt, artifact)):
        raise ValueError('MDG or online-geometry restoration needs its own reader')
    if (cfg.get('training_mode'), cfg.get('frame_layout'), cfg.get('trace_program_version'),
            cfg.get('depth_enabled'), cfg.get('depth_fov_source')) != ('final', 'duplicate', '3.14', True, 'pose_head'):
        raise ValueError('Production native architecture/layout differs')
    if {name: value['receipt'] for name, value in receipt['streams'].items()} != cfg['streams']:
        raise ValueError('Prepared stream identities differ')
    if any(receipt.get(name) != cfg.get(name) for name in FIELDS):
        raise ValueError('Prepared architecture or inference policy differs')
    if trainer.data.layout_settings(receipt) != trainer.data.layout_settings(cfg):
        raise ValueError('Prepared frame layout differs')
    if receipt.get('s1_route_policy') != route_policy(cfg):
        raise ValueError('Prepared frozen route policy differs')
    for name in ('dev_scene_exclusions', 'benchmark_scene_exclusions'):
        if receipt.get(name) != cfg.get(name):
            raise ValueError('Prepared scene-exclusion identity differs')
    seal = metadata(cfg['code'])
    source_seal.check_binding(receipt.get('source_seal'), seal, identity)
    source_seal.check_export(receipt, artifact)
    trace_version.resolve(receipt, cfg)
    trace_version.resolve(artifact, receipt)
    result = deepcopy(receipt)
    result.update(align=cfg.get('align'), init_artifact=cfg.get('init_artifact'),
                  frame_markers=cfg.get('frame_markers', False),
                  pointing_weights=cfg.get('pointing_weights'),
                  camera={**receipt['camera'], **cfg.get('camera_overrides', {})})
    return cfg, result, metadata(receipt['model'])


def load_model(config_pin, artifact_pin, data_pin, *, device, selected_trainer):
    install_tree()
    import torch
    from evalpath import runtime
    from student_pilot import carrier_c1_run as trainer
    if torch.device(device).type != 'cuda':
        raise ValueError('Production native restoration requires the assigned GPU')
    cfg, receipt, manifest = prepared(config_pin, artifact_pin, data_pin)
    trainer_pin = runtime.verify_trainer(selected_trainer, cfg.get('code'))
    processor = trainer.processor_for_receipt(manifest, receipt)
    init_spec = runtime.check_init_spec(receipt, artifact_pin)
    loading = {key: value for key, value in receipt.items() if key != 'init_artifact'}
    model = trainer.load_model(manifest, loading, processor, evaluation=True)
    artifact = trainer.load_artifact(model, artifact_pin)
    if artifact['base_identity'] != cfg['base_identity'] or artifact['config_sha256'] != trainer.identity(cfg):
        raise ValueError('Loaded checkpoint identity differs')
    if not hasattr(processor, '_routing_tokens') or model.trace_program_version != '3.14':
        raise ValueError('Production native processor/trace restoration differs')
    model.to(device).eval().requires_grad_(False)
    info = dict(kind='routed', artifact=artifact_pin, step=artifact.get('step'), init_spec=init_spec,
                trainer=trainer_pin, config=config_pin, data_receipt=data_pin,
                preparation=cfg['preparation'], read_runtime_sha256=sha(__file__),
                training_data_admission='Not repeated: the reader authenticates mirrored production metadata',
                training_databases_opened=False,
                preparation_flags_authorize_read=False,
                authorization_file_check='The launcher requires scoped ORCH authorization and a pinned production export/done record')
    return model, processor, info
