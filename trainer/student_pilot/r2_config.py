"""Two arms share a source identity and differ by one connector selection."""
from copy import deepcopy
from pathlib import Path
from .p3_provenance import load, pinned, file_pin
from .r2_contract import INIT, CONTRACT
from .r2_grammar import SHARED_SHA256
from .r2_withheld import SHA256 as WITHHELD_SHA256

SITE = dict(site='Orchard', parent_job=169097, partition='advanced', nodes=1, gpus_per_node=4, world=4)


def configure(parent, geometry_connector, *, dense_manifest=None, stage=1):
    if geometry_connector not in ('none','gf1') or stage not in (1,2):
        raise ValueError('Unknown connector or stage')
    if parent.get('camera_connector') or parent.get('camera_overrides', {}).get('g3t_prior', {}).get('carrier_connector'):
        raise ValueError('Camera connector is forbidden in both configurations')
    cfg = deepcopy({k:v for k,v in parent.items() if k != 'mdg'})
    from launch_r2.parent import layout_config
    cfg.update(layout_config(cfg, {}, 'four'))
    cfg.update(dev_scene_exclusions=file_pin(Path(__file__).with_name('r2_dev_merged.json')),
               r2_all_stream_exclusions=True, r2_scene_rebuild=None, scene_coverage=None)
    cfg['geometry_connector'] = geometry_connector
    cfg['routing_opener_init'] = 'keep'
    cfg['stream_layout'] = 'four'
    cfg['camera_connector'] = False
    cfg['target_site'] = SITE
    cfg['world_size'] = 4
    cfg['steps'] = 1000
    from .r2_mix import table
    cfg['stream_rows_per_step'] = table()['quotas']
    cfg['mix'] = list(cfg['stream_rows_per_step'])
    cfg['route_table'] = {**parent.get('route_table', {}), 'room_size_estimation':'direct',
                          'absolute_size_room':'direct', 'route_planning':'direct'}
    cfg['r2_identity'] = dict(init=INIT, grammar_sha256=SHARED_SHA256, withheld_rooms_sha256=WITHHELD_SHA256,
        claim_scope=['VSI-Bench','VSTI','ReVSI'], scores=['all','without_venue_381879'],
        lineage_status='overlap_outside_claim_scope', open_question='2026-11-13',
        external_frozen=['geometry_tower','segmenter','base_model_pretraining'], qualification_rooms_bind=False)
    if geometry_connector == 'gf1':
        if not dense_manifest:
            raise ValueError('A2 requires a dense manifest')
        dense = load(pinned(dense_manifest))
        if dense.get('schema') != 'r2-dense-manifest-v1' or dense.get('reconstruct_then_subsample') is not True or not dense.get('clips'):
            raise ValueError('Dense manifest must bind reconstruction before subsampling')
        cfg['r2_dense_manifest'] = dense_manifest
        cfg['r2_schedule'] = [dict(stage=1, steps=400), dict(stage=2, steps=600)]
        cfg['steps'] = 400 if stage == 1 else 600
        cfg['r2_stage'] = dict(stage=stage, trainable='gf1' if stage == 1 else 'full',
                               learning_rate=cfg['recipe']['learning_rate'] if stage == 1 else cfg['recipe']['lm_learning_rate'],
                               init='zero' if stage == 1 else 'warm')
    else:
        if parent.get('geometry_online'):
            raise ValueError('A0 cannot carry a geometry encoder')
        cfg['r2_stage'] = dict(stage=stage, trainable='full', learning_rate=cfg['recipe']['learning_rate'])
    return refresh_recipe(cfg)


def refresh_recipe(cfg):
    from .carrier_c1_sweep import recipe_for
    from .checkpoint_space import plan
    cfg['milestones'] = sorted({m for m in cfg['milestones'] if m <= cfg['steps']} | {cfg['steps']})
    cfg['recipe'] = recipe_for(cfg)
    cfg['checkpoint_disk_guard'] = plan(cfg['recipe'])
    return cfg


def bind_mix(cfg, mix):
    from .r2_mix import validate_table
    validate_table(mix)
    cfg['stream_rows_per_step'] = mix['quotas']
    if mix['fallback']:
        cfg['reference_world_size'] = cfg['world_size']
    return refresh_recipe(cfg)


def apply_native(cfg, geometry=None):
    """Bind the chosen arm to the existing CarrierC1 forward and optimizer settings."""
    from . import gf1
    value = deepcopy(cfg)
    if value.get('camera_connector'):
        raise ValueError('Camera connector is forbidden')
    if value['geometry_connector'] == 'gf1':
        if not geometry:
            raise ValueError('A2 requires frozen tower assets')
        stage = value['r2_stage']
        settings = dict(geometry.get('gf1', {}), stage=stage['stage'], gf1_init=stage['init'])
        settings = {k:v for k,v in settings.items() if k != 'learning_rate'}
        if stage['stage'] == 1:
            settings['learning_rate'] = stage['learning_rate']
        value['geometry_online'] = {**geometry, 'mode':'frozen', 'gf1':gf1.normalize(settings)}
    return refresh_recipe(value)
