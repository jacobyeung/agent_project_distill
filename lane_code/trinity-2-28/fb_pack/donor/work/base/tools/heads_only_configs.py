"""Build A0/A1 heads-only configs from pinned f17 and CPDM inputs, without loading weights.

Run with --request REQUEST.json --output NEW_DIRECTORY. The request schema is documented
in b1_notes/NOTES.md. Paths and lowercase SHA-256 pins are mandatory; no production paths
or missing-input placeholders are inferred. Run 2 requires already migrated prior heads
(tools.migrate_camtoken_init) and a pinned geometry projector, which remains frozen.
The output spec binds row sources separately, as the existing arm-config tools do.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from student_pilot import camera_config, full_ft, geometry_input
from student_pilot.common import canonical_bytes, sha256
from student_pilot.ddp_config import normalize_training_config, run_control_from_config


MILESTONES = [200, 400, 800, 1600]


def checked_pin(value):
    pin = full_ft._pin(value, 'heads-only input')
    if sha256(pin['path']) != pin['sha256']:
        raise ValueError('Heads-only input differs from its SHA-256: ' + pin['path'])
    return pin


def read_pinned(value):
    pin = full_ft._pin(value, 'heads-only input')
    raw = Path(pin['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('Heads-only input differs from its SHA-256: ' + pin['path'])
    return json.loads(raw)


def make_config(cpdm, export, heads, row_count, max_steps, world_size, freeze_modules, run2=None, frame_count=None):
    """Reuse CPDM's camera losses and native normalizers; the caller authenticates all input pins."""
    if type(row_count) is not int or row_count < 1 or type(max_steps) is not int or max_steps < MILESTONES[-1]:
        raise ValueError('Positive row count and max_steps >= 1600 are required for the four milestones')
    config = {key: copy.deepcopy(value) for key, value in cpdm.items()
              if key not in ('full_ft', 'geometry', 'headcall', 'auxiliary', 'init_adapter', 'unfreeze_vision_blocks',
                             'vision_learning_rate', 'head_learning_rate', 'group_parameters', 'trainable_parameters',
                             'frozen_group_parameters')}
    camera = camera_config.normalize(cpdm['camera'])
    if camera_config.g3t_prior_enabled(camera):
        raise ValueError('Run 1 requires CPDM camera losses without a G3T prior')
    camera.update(freeze_modules=list(freeze_modules), head_only_steps=0, gate=None, lm_gate=None)
    if frame_count is not None:
        from student_pilot.pose_samples import DEFAULT_PIXELS
        if run2 is not None:
            raise ValueError('Long-window arms do not support the fixed RGB32 G3T store')
        if frame_count not in (64, 96):
            raise ValueError('Long-window arms require 64 or 96 frames')
        if camera['point_depth'] and 'point_depth' not in freeze_modules:
            raise ValueError('Long-window arms require frozen point_depth with empty targets')
        camera['max_groups'] = 48
        config['frames'] = {'count': frame_count, 'pixels_per_frame': list(DEFAULT_PIXELS)}
    block = {'train': {group: False for group in full_ft.TRAIN_GROUPS},
             'init': {'kind': 'full_export', **export}, 'init_modules': {'heads': heads},
             'learning_rates': {'heads': 1e-4}}
    if run2 is not None:
        camera['g3t_prior'] = camera_config.normalize_g3t_prior(run2.get('g3t_prior', True))
        if not camera_config.g3t_prior_enabled(camera):
            raise ValueError('Run 2 requires an enabled G3T prior')
        camera['freeze_modules'] = sorted(set(camera['freeze_modules']) | {'geometry'})
        config['geometry'] = geometry_input.normalize(run2['geometry'])
        if 'camera_manifest' not in config['geometry']['store']:
            raise ValueError('Run 2 requires the pinned G3T camera manifest')
        block['init_modules'] = {'heads': run2['heads'], 'geometry': run2['geometry_weights']}
    camera = camera_config.normalize(camera)
    if not camera_config.enabled(camera):
        raise ValueError('Heads-only training requires enabled CPDM camera losses')
    if 'point_depth' in camera['freeze_modules'] and not camera['point_depth']:
        raise ValueError('Cannot freeze absent point_depth weights')
    # Supply enough epochs to reach the cap. The frozen-export trainer schedules cosine over that cap.
    config.update(full_ft=full_ft.normalize(block), camera=camera, world_size=world_size,
                  effective_batch_size=64, epochs=math.ceil(max_steps / math.ceil(row_count / 64)),
                  max_steps=max_steps, learning_rate=1e-4, warmup_ratio=0.03, schedule='cosine',
                  weight_decay=0.0, checkpoint_every_steps=200, checkpoint_milestones=list(MILESTONES))
    normalize_training_config(config, 'qwen35')
    run_control_from_config(config)
    camera_config.from_training_config(config)
    return config


def build(request):
    if (not isinstance(request, dict) or request.get('schema') != 'heads-only-build-v1'
            or set(request) - {'schema', 'cpdm_config', 'f17', 'rows', 'run2', 'max_steps', 'world_size', 'freeze_modules'}):
        raise ValueError('Unknown heads-only build request')
    cpdm = read_pinned(request['cpdm_config'])
    f17 = request['f17']
    if set(f17) != {'full_weights', 'heads'}:
        raise ValueError('f17 requires full_weights and heads pins')
    manifest = read_pinned(f17['full_weights'])
    if Path(f17['full_weights']['path']).name != full_ft.EXPORT_MANIFEST or manifest.get('schema') != full_ft.EXPORT_SCHEMA:
        raise ValueError('f17 full_weights must pin a native full_weights.json export')
    checked_pin(f17['heads'])
    camera = camera_config.normalize(cpdm['camera'])
    checked_pin(camera['supervision'])
    rows = request['rows']
    if not {'A0', 'A1'} <= set(rows) <= {'A0', 'A1', 'A64', 'A96'} or rows['A0'].get('name') != 'POSE32_V2':
        raise ValueError('Rows require A0=POSE32_V2 and a second pinned A1 source; optional arms are A64 and A96')
    for arm, source in rows.items():
        if set(source) != {'name', 'count', 'source'} or not isinstance(source['name'], str) or not source['name']:
            raise ValueError('A row source requires name, count, and source pin')
        checked_pin(source['source'])
    if rows['A0']['source']['sha256'] == rows['A1']['source']['sha256']:
        raise ValueError('A1 requires a second row source')
    prior = request['run2']
    if set(prior) - {'geometry_config', 'geometry_weights', 'heads', 'g3t_prior'}:
        raise ValueError('Unknown Run 2 inputs')
    geometry = geometry_input.normalize(read_pinned(prior['geometry_config']))
    for path_key, sha_key in (('manifest', 'manifest_sha256'), ('camera_manifest', 'camera_manifest_sha256')):
        checked_pin({'path': geometry['store'][path_key], 'sha256': geometry['store'][sha_key]})
    checked_pin(prior['geometry_weights'])
    checked_pin(prior['heads'])
    prior_config = {**prior, 'geometry': geometry}
    configs = {}
    for arm, source in rows.items():
        # The pinned G3T feature/camera store has a separate fixed RGB32 contract.
        # Long-window arms train the frozen VLM camera heads without that store.
        runs = (('RUN1', None),) if arm in ('A64', 'A96') else (('RUN1', None), ('RUN2', prior_config))
        for run, extra in runs:
            configs[f'{arm}_{run}'] = make_config(cpdm, f17['full_weights'], f17['heads'], source['count'],
                request.get('max_steps', 1600), request.get('world_size', 8), request.get('freeze_modules', []), extra,
                {'A64': 64, 'A96': 96}.get(arm))
    return configs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    raw = args.request.read_bytes()
    request = json.loads(raw)
    configs = build(request)
    args.output.mkdir(parents=True, exist_ok=False)
    files = {}
    for name, config in configs.items():
        payload = canonical_bytes(config)
        filename = name + '.json'
        with (args.output / filename).open('xb') as handle:
            handle.write(payload)
        files[name] = {'path': filename, 'sha256': hashlib.sha256(payload).hexdigest(),
                       'rows': request['rows'][name.split('_')[0]]}
    spec = {'schema': 'heads-only-configs-v1', 'inputs': request,
            'request': {'path': str(args.request), 'sha256': hashlib.sha256(raw).hexdigest()}, 'configs': files,
            'checkpoints': MILESTONES, 'scheduler': 'warmup_0.03_cosine_to_max_steps',
            'note': 'Build only; native preparation and launch controls still apply.'}
    with (args.output / 'BUILD.json').open('xb') as handle:
        handle.write(canonical_bytes(spec))


if __name__ == '__main__':
    main()
