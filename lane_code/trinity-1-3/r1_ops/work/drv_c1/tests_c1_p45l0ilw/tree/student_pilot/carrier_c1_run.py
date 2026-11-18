"""C1 preparation, CPU dryrun, FSDP smoke/train/resume and native head probes.

This module never submits jobs or grants GPU admission. The parent supplies the
sealed source, inputs, independent review and allocation authorization.
"""
import argparse
import copy
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import random
import re
import resource
import signal
import sqlite3
import sys
import time
import traceback
import uuid

import numpy as np
import torch
import torch.distributed as dist

from . import full_ft, carrier_c1_data as data
from .carrier_c1 import CarrierC1, RECIPE, parameter_groups
from .carrier_c1_sweep import capped_steps, recipe_for, dense_pose_row
from .decoupled_v import learning_rate
from .decoupled_v_run import processor_for
from .decoupled_resume import rng_state, restore_rng, run_lock
from .p3_provenance import digest, file_pin, load, pinned, write, source_files, sha256, unique
from . import carrier_c1_routing as routing
from . import rehearsal


def identity(cfg):
    value = {k: v for k, v in cfg.items() if k not in
             ('preparation', 'admission', 'authorization', 'milestone_gate')}
    if 'readout' in value:
        value['readout'] = {k: v for k, v in value['readout'].items() if k != 'contiguous_clips'}
    if value.get('frame_layout') == 'spread':
        value.pop('frame_layout')
    return digest(value)


def readout_identity(cfg):
    return digest(dict(config_sha256=identity(cfg), readout=cfg['readout']))


def validate_route_table(table):
    if not isinstance(table, dict) or any(not isinstance(k, str) or v not in ('route', 'direct') for k, v in table.items()):
        raise ValueError('route_table maps question types to route or direct')
    return table


POSE_ONLY_LEVERS = frozenset({'init_artifact'})
POSE_ONLY_RECEIPT_KEYS = ('init_artifact', 'row_start_step')


def validate(cfg):
    if 'type_mix' in cfg:
        from .type_mix import validate as validate_type_mix
        validate_type_mix(cfg['type_mix'], cfg['recipe'])
    if 'h1' in cfg:
        from .h1 import validate as validate_h1
        validate_h1(cfg)
    if cfg.get('trace_program_version', '3.13') not in ('3.13', '3.14'):
        raise ValueError('Unsupported trace_program_version')
    data.layout_settings(cfg)
    gx = cfg.get('geometry_online')
    if 'geometry_online' in cfg:
        from .g3t_online import normalize, validate_arm
        if normalize(gx) != gx:
            raise ValueError('GX block must be normalized')
        validate_arm(gx, cfg.get('training_mode'), cfg.get('frame_layout'), cfg.get('depth_enabled', True))
    if 'skip_unsupervised_lm' in cfg and type(cfg['skip_unsupervised_lm']) is not bool:
        raise ValueError('skip_unsupervised_lm must be boolean')
    if cfg.get('schema') != 'carrier-c1-run-v1' or cfg.get('recipe') != recipe_for(cfg):
        raise ValueError('C1 requires its explicit fixed recipe')
    if 'checkpoint_disk_guard' in cfg:
        from .checkpoint_space import Budget, plan
        budget = Budget(cfg['checkpoint_disk_guard'])
        if budget.whole_leg and budget.policy != plan(cfg['recipe'], budget.policy['reserve_bytes']):
            raise ValueError('Whole-leg checkpoint disk plan differs from the recipe')
    if cfg.get('carrier_placement') not in data.PLACEMENTS:
        raise ValueError('C1 requires an explicit carrier_placement')
    if cfg.get('init') != 'base' or cfg.get('parallel') != 'fsdp' or cfg.get('all_frames') is not True:
        raise ValueError('C1 starts from BASE with full LM FSDP and all-frame carriers')
    expected = {'pose'} if cfg.get('training_mode') == 'pose_only' else {'pose', 'vqa', 'pointing'}
    if cfg.get('training_mode') == 'final':
        expected = {'pose', 'vqa', 'pointing', 'routing'}
        if cfg.get('depth_fov_source') != 'pose_head':
            raise ValueError('Final mode feeds the pose-head FoV to depth and unprojection')
    if 'mdg' in cfg:
        from .stageb_mdg import validate as validate_mdg
        validate_mdg(cfg)
        expected.add('mdg')
    if set(cfg.get('streams', {})) != expected:
        raise ValueError('Pinned streams must match training_mode exactly')
    from .pose_source_guard import refuse_a4_r_s
    refuse_a4_r_s(cfg['streams']['pose'])
    if cfg.get('training_mode') == 'pose_only' and type(cfg.get('depth_enabled')) is not bool:
        raise ValueError('Pose-only arms must explicitly select optional depth')
    if 'frame_markers' in cfg and (type(cfg['frame_markers']) is not bool
                                   or (cfg['frame_markers'] and cfg.get('frame_layout') not in ('duplicate', 'paired'))):
        raise ValueError('frame_markers must be boolean and needs a one-viewpoint-per-group layout')
    if 'route_table' in cfg:
        validate_route_table(cfg['route_table'])
    from .s1_route_policy import validate as validate_s1_route_policy
    validate_s1_route_policy(cfg, authenticate=False)
    if 'pointing_weights' in cfg and cfg['pointing_weights'] is not None and (
            not isinstance(cfg['pointing_weights'], dict) or set(cfg['pointing_weights']) != {'decision', 'row_mean'}
            or any(type(v) not in (int, float) or not v > 0 for v in cfg['pointing_weights'].values())):
        raise ValueError('pointing_weights needs positive decision and row_mean')
    if 'pose_lr_scale' in cfg and (type(cfg['pose_lr_scale']) not in (int, float) or not 0 < cfg['pose_lr_scale'] <= 1):
        raise ValueError('pose_lr_scale must be in (0, 1]')
    if 'lm_lr_scale' in cfg and (type(cfg['lm_lr_scale']) not in (int, float) or not 0 < cfg['lm_lr_scale'] <= 1):
        raise ValueError('lm_lr_scale must be in (0, 1]')
    if 'exclude_sources' in cfg and (not isinstance(cfg['exclude_sources'], dict) or any(
            not isinstance(v, list) or any(not isinstance(t, str) or not t for t in v) for v in cfg['exclude_sources'].values())):
        raise ValueError('exclude_sources maps stream names to non-empty source-tag substrings')
    if 'tool_mode_flag' in cfg:
        routing.validate_tool_mode_flag(cfg['tool_mode_flag'])
    levers = {k for k in ('align', 'init_artifact', 'camera_overrides', 'gate_stop', 'frame_markers', 'route_table',
                          'exclude_qids', 'exclude_sources', 'pose_lr_scale', 'pointing_weights', 'pose_exclusions', 'lm_lr_scale',
                          'tool_mode_flag')
              if k in cfg}
    if cfg.get('training_mode') == 'pose_only':
        # A warm-started pose-only run: init from a C1 milestone, its own horizon, a sampler offset.
        levers -= POSE_ONLY_LEVERS
        if (set(cfg) & {'steps', 'milestones', 'row_start_step'}) and cfg.get('init_artifact') is None:
            raise ValueError('Pose-only steps/milestones/row_start_step need init_artifact')
    if levers and cfg.get('training_mode') != 'final':
        raise ValueError('align/init_artifact/camera_overrides/gate_stop are final-mode levers')
    if 'row_start_step' in cfg and (type(cfg['row_start_step']) is not int or not 0 <= cfg['row_start_step'] <= 100000
                                    or cfg.get('training_mode') != 'pose_only'):
        raise ValueError('row_start_step must be an integer sampler offset in steps (pose-only)')
    if cfg.get('align') is not None:
        from .c1r_align import validate as validate_align
        validate_align(cfg['align'])
        if cfg['align']['cam']['layer'] != 'final' or cfg['align'].get('patch') is not None:
            raise ValueError('Final mode aligns final-layer carrier states only, without a patch term')
    if cfg.get('init_artifact') is not None:
        validate_init(cfg['init_artifact'])
        if cfg.get('training_mode') == 'pose_only' and cfg['init_artifact']['heads'] != ['pose']:
            raise ValueError('Pose-only init_artifact needs the pose head only')
    overrides = cfg.get('camera_overrides', {})
    if (not isinstance(overrides, dict) or set(overrides) - {'weight_focal'}
            or any(type(v) not in (int, float) or not v >= 0 for v in overrides.values())):
        raise ValueError('camera_overrides may set nonnegative weight_focal only')
    if 'gate_stop' in cfg and type(cfg['gate_stop']) is not bool:
        raise ValueError('gate_stop must be boolean')
    if 'validation' in cfg:
        value = cfg['validation']
        if (not isinstance(value, dict) or set(value) != {'rows', 'slice'} or any(
                not isinstance(v, dict) or set(v) != {'path', 'sha256'}
                or not isinstance(v['path'], str) or not Path(v['path']).is_absolute()
                or not isinstance(v['sha256'], str) or re.fullmatch('[0-9a-f]{64}', v['sha256']) is None
                for v in value.values())):
            raise ValueError('validation needs exactly {rows pin, slice pin}')

    if cfg.get('h1', {}).get('faithful_own_camera_rows') is not None:
        from .h1_faithful import validate as validate_faithful
        validate_faithful(cfg)


def warn(cfg, message):
    """Final mode records provenance/review mismatches instead of refusing (USER 11-08 1303Z)."""
    if cfg.get('training_mode') != 'final' and not cfg.get('geometry_online'):
        raise ValueError(message)
    print(json.dumps({'warning': message}), flush=True)


def authenticate(cfg):
    seal = load(pinned(cfg['code']))
    root = Path(__file__).parent.parent
    actual = {str(p.relative_to(root)): sha256(p) for p in source_files([Path(__file__)])}
    if seal.get('schema') == 'c1-sealed-source-v1':
        from .source_seal import verify
        return verify(seal, root, actual)
    if seal.get('schema') == 'c1-rehearsal-source-v1':
        if not rehearsal.enabled() or seal.get('sources') != actual or seal.get('content_sha256') != digest(actual):
            raise ValueError('Rehearsal source closure differs')
        return 'rehearsal:' + seal['content_sha256']
    if (seal.get('schema') != 'c1-clean-source-v1' or seal.get('clean') is not True
            or len(seal.get('commit', '')) != 40 or seal.get('sources') != actual):
        warn(cfg, 'Parent must seal the exact committed C1 source closure')
        return seal.get('commit') or 'unsealed:' + digest(actual)
    return seal['commit']


def milestone_gate(cfg):
    """Every m400 gate needs sparse anchors AND contiguous clips of this artifact."""
    from .carrier_c1_clip import PROTOCOL, METRICS
    gate=load(pinned(cfg['milestone_gate']))
    if (gate.get('schema')!='c1-m400-gate-v1' or gate.get('verdict')!='PASS' or not gate.get('reviewer')
            or gate.get('config_sha256')!=identity(cfg) or gate.get('step')!=400
            or gate.get('artifact')!=file_pin(Path(cfg['output'])/'m400/artifact.json')):
        raise ValueError('Parent must review the exact C1 m400 artifact')
    pose_only = cfg.get('training_mode') == 'pose_only'
    expected = {'pose'} if pose_only else {'pose','pointing','vsi500'}
    if set(gate.get('reports',{})) != expected:
        raise ValueError('All m400 gate reports required by this training mode must be present')
    for pin in gate['reports'].values():
        pinned(pin)
    m=gate['metrics']
    pose = load(pinned(gate['reports']['pose']))
    clip = pose.get('contiguous_clip') or {}
    clip_pin = cfg.get('readout', {}).get('contiguous_clips')
    if not clip_pin:
        raise ValueError('Both sparse head_acc and contiguous Sim(3) readouts are required')
    pinned(clip_pin)
    if (pose.get('schema') != 'c1-readout-v2' or pose.get('artifact') != gate['artifact']
            or pose.get('config_sha256') != identity(cfg) or pose.get('step') != 400
            or pose.get('detail', {}).get('protocol') != 'head_acc_origin_metric_v1'
            or clip.get('protocol') != PROTOCOL or clip.get('scenes') != 38
            or clip.get('clips') != 38 or clip.get('frames_per_clip') != 32 or clip.get('raw_stride') != 3
            or pose.get('contiguous_clips') != clip_pin
            or pose.get('readout_sha256') != readout_identity(cfg)
            or set(clip.get('mean', {})) != set(METRICS)
            or any(not np.isfinite(clip['mean'][k]) or clip['mean'][k] < 0 for k in METRICS)):
        raise ValueError('Both sparse head_acc and contiguous Sim(3) readouts are required')
    sparse = pose['detail']['all_frames']['all']
    statistic = {'head_acc_mean': 'mean', 'head_acc_median': 'median'}.get(m.get('pose_statistic'))
    if (statistic is None or sparse.get('scenes') != 38
            or m.get('rotation_deg') != sparse['rot_deg'][statistic]):
        raise ValueError('Gate rotation differs from the pinned head_acc report')
    if (m.get('pose_scenes')!=38
            or m.get('pose_statistic') not in ('head_acc_mean','head_acc_median')
            or not 0<=m['rotation_deg']<=39):
        raise ValueError('C1 m400 pose gate failed')
    if not pose_only and (m.get('vsi500_n')!=500 or not .677<=m['pointing_inside_fraction']<=1
            or not 0<=m['vsi500_base_accuracy']<=1 or not 0<=m['vsi500_accuracy']<=1
            or m['vsi500_accuracy']<m['vsi500_base_accuracy']-.02):
        raise ValueError('C1 m400 preservation/pose gate failed')
    return gate


def connect(pin):
    return sqlite3.connect(Path(pin['path']).as_uri()+'?mode=ro', uri=True)


def paired_prefix(cfg, receipt):
    """Validate an A1 overlay while retaining the original sampler population."""
    if receipt.get('schema') != 'c1-paired-prefix-v2':
        return None
    if (cfg.get('training_mode') != 'pose_only' or cfg.get('frame_layout') != 'paired'
            or receipt.get('frame_pair_gap_seconds') != cfg.get('frame_pair_gap_seconds')
            or receipt.get('frame_pair_gap_seconds') not in (.5, 1.)
            or receipt.get('required_steps') != 800 or receipt.get('margin_steps') != 80):
        raise ValueError('Invalid paired prefix identity')
    parent = load(pinned(receipt['parent']))
    sampler = load(pinned(receipt['sampler_preparation']))
    stream = sampler['streams']['pose']
    indices = load(pinned(receipt['dense_indices']))
    if (parent.get('schema') != 'decoupled-v-preparation-v1' or parent.get('count') != 321152
            or parent['database'] != receipt['source_database']
            or any(parent[k] != receipt[k] for k in ('settings', 'inputs', 'model'))
            or stream['receipt'] != receipt['parent'] or stream['database'] != parent['database']
            or stream['indices'] != receipt['dense_indices'] or stream['count'] != 283200
            or receipt['dense_count'] != 283200 or len(indices) != 283200
            or indices != sorted(set(indices)) or any(type(i) is not int or not 0 <= i < 321152 for i in indices)
            or sampler['training_mode'] != 'pose_only'):
        raise ValueError('Paired prefix parent or sampler differs')
    for key in ('seed', 'steps', 'global_batch', 'world_size', 'mix'):
        if receipt['recipe'][key] != cfg['recipe'][key] or sampler['recipe'][key] != cfg['recipe'][key]:
            raise ValueError('Paired prefix recipe differs')
    expected = [indices[i] for plan in data.mixed_indices({'pose': len(indices)}, 880,
        seed=cfg['recipe']['seed'], training_mode='pose_only') for _, batch in plan for i in batch]
    source_ids = receipt['source_indices']
    source_set = set(source_ids)
    if (receipt.get('sampler_indices') != expected or receipt['count'] != len(source_ids)
            or len(set(source_ids)) != len(source_ids) or not set(expected[:25600]).issubset(source_ids)
            or source_ids != [i for i in expected if i in source_set]):
        raise ValueError('Paired prefix changed fixed sampler order or coverage')
    pinned(parent['database'])
    pinned(receipt['database'])
    seen_files = set()
    with connect(parent['database']) as original, connect(receipt['database']) as overlay:
        ids = [i for i, in overlay.execute('SELECT i FROM rows ORDER BY i')]
        if ids != sorted(source_ids):
            raise ValueError('Paired prefix database coverage differs')
        for index in ids:
            before = original.execute('SELECT row,target FROM rows WHERE i=?', (index,)).fetchone()
            after = overlay.execute('SELECT row,target FROM rows WHERE i=?', (index,)).fetchone()
            if before is None:
                raise ValueError('Missing paired prefix source')
            base, target = map(json.loads, before)
            row, actual = map(json.loads, after)
            if actual != target or not dense_pose_row(base, target):
                raise ValueError('Paired prefix changed targets')
            inputs = row['student_input']
            old = base['student_input']
            if [f['sha256'] for f in inputs['frames']] != [f['sha256'] for f in old['frames']]:
                raise ValueError('Paired prefix changed anchor pixels')
            stripped = {**row, 'student_input':{**inputs, 'frames':old['frames']}}
            for k in ('recording_id', 'partner_frames'):
                stripped['student_input'].pop(k, None)
                if k in old:
                    stripped['student_input'][k] = old[k]
            if stripped != base:
                raise ValueError('Paired prefix changed source metadata')
            data.layout_inputs(row, *data.layout_settings(cfg), verify_partners=False)
            for f in inputs['frames']+inputs['partner_frames']:
                key = f['path'], f['sha256']
                if key not in seen_files:
                    pinned(dict(path=key[0], sha256=key[1]))
                    seen_files.add(key)
    # The clip job may finish after training prep. Its pin is excluded from the
    # training identity, while the sparse bank stays bound to the prefix store.
    readout = dict(cfg.get('readout') or {})
    bound_readout = dict(receipt.get('readout') or {})
    if 'contiguous_clips' not in bound_readout:
        clip_pin = readout.pop('contiguous_clips', None)
        if clip_pin is not None:
            from .carrier_c1_clip import check_clips
            with np.load(pinned(bound_readout['bank']), allow_pickle=False) as bank:
                held = list(zip(bank['dataset_tokens'].tolist(), bank['scene_tokens'].tolist()))
            clips = load(pinned(clip_pin))
            training = load(pinned(bound_readout['training_scenes']))['scenes']
            check_clips(clips, held, training)
            for row in clips['clips']:
                data.layout_inputs(row, *data.layout_settings(cfg), verify_partners=True)
    if readout != bound_readout or not {'bank', 'training_scenes', 'rows_inventory'} <= set(bound_readout):
        raise ValueError('Paired prefix needs its pinned sparse readout bank')
    return parent


def excluded_row(row, benchmark, reported, name='pose'):
    """(test-split hit, reported-overlap hit) for one row's scene keys."""
    if 'dataset' not in row or 'scene' not in row:
        raise ValueError(f'{name} rows lack dataset/scene keys for the exclusion check')
    keys = [routing.alias_key(f"{row['dataset']}/{row['scene']}"), *routing.canonical_keys(
        row.get('routing', {}).get('canonical') or row.get('canonical'),
        row.get('routing', {}).get('physical_group'))]
    return bool(routing.excluded(benchmark, *keys)), int(routing.excluded(reported, *keys))


def division_admits(stream_division, pose_division):
    """A stream division equals the pose division, or names it as parent_division with a held-out
    split that contains the parent's and no parent held-out scene among its training scenes, or is an
    ancestor of the pose division along links that keep train scenes train and held-out scenes held out."""
    if stream_division == pose_division:
        return True
    from .c1_pose_mix import ancestor_admits
    if ancestor_admits(pose_division, stream_division):
        return True
    child = load(pinned(stream_division))
    if child.get('parent_division') != pose_division:
        return False
    held = set(load(pinned(pose_division))['heldout_scenes'])
    return held <= set(child['heldout_scenes']) and not held & set(child['train_scenes'])


def routed_type(row, cfg):
    """True for a direct VQA row whose question type routes in this run (config route_table)."""
    return (cfg.get('route_table') or {}).get(row.get('question_type')) == 'route'


def row_source(row):
    provenance = row.get('provenance') if isinstance(row.get('provenance'), dict) else {}
    return str(row.get('source') or provenance.get('source') or provenance.get('stream') or '')


def held_row(row, name, qids, sources):
    """True for a row the CP1 holds name: its qid is listed for the stream (exclude_qids), or its
    source tag contains a listed substring (exclude_sources)."""
    return row.get('qid') in qids.get(name, ()) or any(tag in row_source(row) for tag in sources.get(name, ()))


AUGMENT_KEYS = {'seed', 'brightness', 'contrast', 'saturation', 'hue', 'grayscale_p', 'blur_p', 'blur_kernel', 'blur_sigma'}


def pose_row_check(cfg, row, target):
    """The structural checks training's pose encode applies, without decoding frames: the frame
    layout, the inline pose sample and the all-frame targets. Returns the masked point-depth uv span."""
    from .decoupled_v import target_tensors
    from .pose_samples import check_sample
    data.layout_inputs(row, *data.layout_settings(cfg))
    check_sample(row, max_groups=32)
    settings = row['pose_sample'].get('augment')
    if (not isinstance(settings, dict) or not AUGMENT_KEYS <= set(settings) or type(settings['seed']) is not int
            or len(settings['blur_sigma']) != 2):
        raise ValueError('Pose row augmentation settings differ from what training applies')
    tensors = target_tensors(target, all_frames=True)
    mask = tensors['aux_point_depth_mask'][0]
    if not bool(mask.any()):
        return None
    uv = tensors['aux_point_depth_uv'][0][mask]
    if not bool(torch.isfinite(uv).all()):
        raise ValueError('Point-depth uv must be finite')
    return float(uv.min()), float(uv.max())


def validation_heldout(division, slice_source=None):
    """Held-out scenes a validation slice may use: the pose division's, plus those of the slice's source
    division when it is a child of the pose division (an A3 slice under an A1 run)."""
    held = set(load(pinned(division))['heldout_scenes'])
    if isinstance(slice_source, dict) and {'path', 'sha256'} <= set(slice_source):
        child = {'path': slice_source['path'], 'sha256': slice_source['sha256']}
        if child != division and division_admits(child, division):
            held |= set(load(pinned(child))['heldout_scenes'])
    return held


def prepare_validation(cfg, division):
    """Pin held-out all-frame pose rows in database order."""
    spec = cfg['validation']
    source, selected = load(pinned(spec['rows'])), load(pinned(spec['slice']))
    scenes = selected.get('scenes')
    if (selected.get('schema') != 'cp1-pose-validation-slice-v1' or not isinstance(scenes, list)
            or not scenes or any(not isinstance(s, str) or len(s.split('/')) != 2
                                 or not all(s.split('/')) for s in scenes)
            or len(set(scenes)) != len(scenes) or selected.get('count') != len(scenes)):
        raise ValueError('Invalid CP1 pose validation slice')
    split = load(pinned(division))
    scenes = set(scenes)
    if scenes & set(split['train_scenes']) or not scenes <= validation_heldout(division, selected.get('source')):
        raise ValueError('Validation slice scenes must be heldout_scenes and absent from train_scenes')
    from .c1_pose_mix import ROWS_ONLY_SCHEMAS
    if source.get('schema') not in ROWS_ONLY_SCHEMAS:
        raise ValueError('Validation needs a rows-only A3 pose receipt')
    pinned(source['database'])
    indices, seen = [], set()
    with connect(source['database']) as conn:
        if conn.execute('SELECT count(*) FROM rows').fetchone()[0] != source['count']:
            raise ValueError('Validation database count differs from receipt')
        for index, row, target in conn.execute('SELECT i,row,target FROM rows ORDER BY i'):
            row = json.loads(row)
            scene = f"{row.get('dataset')}/{row.get('scene')}"
            if scene not in scenes:
                continue
            target = json.loads(target)
            if not dense_pose_row(row, target):
                continue
            try:
                pose_row_check(cfg, row, target)
            except Exception as exc:
                raise ValueError(f'Validation row {index} fails the training row check: {exc}') from exc
            indices.append(index)
            seen.add(scene)
    if seen != scenes:
        raise ValueError('Validation slice scene has no selected row: ' + str(sorted(scenes - seen)))
    path = Path(cfg['preparation_output'])/'validation_indices.json'
    write(path, indices)
    return dict(**spec, database=source['database'], count=len(indices), scenes=len(scenes), indices=file_pin(path))


def prepare(cfg):
    """Authenticate existing databases once; never duplicate the A1 payload."""
    from .trace_version import metadata
    version_metadata = metadata(cfg)
    validate(cfg)
    from .s1_route_policy import validate as validate_s1_route_policy
    validate_s1_route_policy(cfg)
    from .row_removals import Removals
    removals = Removals(cfg.get('remove_files', ()))
    r0_filter = None
    if cfg.get('h1', {}).get('r0_rooms') is not None:
        from .h1_r0 import Reserve
        r0_filter = Reserve(cfg['h1']['r0_rooms'])
    scene_filter = None
    if cfg.get('dev_scene_exclusions') or cfg.get('benchmark_scene_exclusions'):
        from .s1_exclusions import Exclusions
        scene_filter = Exclusions(cfg.get('dev_scene_exclusions'), cfg.get('benchmark_scene_exclusions'))

    def prepare_exclusions(row, benchmark, reported, name='pose'):
        if r0_filter is not None and r0_filter.excluded(row):
            return False, 0  # The reserve selection pass drops and counts this row.
        hit, overlap = excluded_row(row, benchmark, reported, name)
        return hit and not (scene_filter is not None and scene_filter.excluded(row)), overlap

    commit = authenticate(cfg)
    receipts = {name: load(pinned(pin)) for name, pin in cfg['streams'].items() if name != 'mdg'}
    pose = receipts['pose']
    from .pose_source_guard import refuse_a4_r_s
    refuse_a4_r_s(pose)
    final = cfg.get('training_mode') == 'final'
    benchmark = routing.load_exclusions(cfg.get('exclusions')) if final else set()
    # Pose rows also drop on `pose_exclusions` (e.g. posedata2's x4 list); other streams keep the shared list.
    pose_benchmark = benchmark | (routing.load_exclusions(cfg.get('pose_exclusions')) if final else set())
    held_qids = {k: set(v) for k, v in load(pinned(cfg['exclude_qids'])).items()} if cfg.get('exclude_qids') else {}
    held_sources = cfg.get('exclude_sources') or {}
    reported = routing.load_exclusions(cfg.get('report_exclusions')) if final else set()
    mix = None
    if pose.get('schema') == 'c1-pose-mix-v1':
        from . import c1_pose_mix
        if not final or not benchmark:
            raise ValueError('The composite pose stream is final-mode only and needs the exclusion list')
        mix, pose = c1_pose_mix.prepare(cfg['streams']['pose'], cfg['preparation_output'],
                                        pose_benchmark, reported, prepare_exclusions,
                                        check=lambda row, target: None if r0_filter is not None and r0_filter.excluded(row)
                                        else pose_row_check(cfg, row, target))
    prefix = paired_prefix(cfg, pose) if mix is None else None
    if prefix is not None:
        pose = prefix
    tiny_pose = rehearsal.enabled() and pose.get('rehearsal') is True and 0 < pose.get('count', 0) <= 128
    if ((mix is None and (pose.get('schema') != 'decoupled-v-preparation-v1' or (pose.get('count') != 321152 and not tiny_pose)))
            or pose['settings']['anchors'] != list(range(1, 33))
            or pose['settings']['temporal_grouping'] != 'fused_pairs_all_frames'):
        raise ValueError('C1 requires the admitted 321152-row all-frame A1 preparation')
    division = pose['inputs']['division']
    model = load(pinned(pose['model']))
    from .students import get_student
    spec = get_student('qwen35')
    fixture = rehearsal.fixture_manifest(model)
    if (model.get('kind') != 'base' or model['base_identity'] != cfg['base_identity']
            or (not fixture and (Path(model['root']).name != spec['snapshot'].name
                                 or model['files']['config.json'] != spec['config_sha256']))):
        raise ValueError('C1 model provenance is not the original Qwen3.5 base')
    streams = {}
    # `exclusions`: benchmark TEST-split scenes absent from public training sets (filter/refuse, KEEP).
    # `report_exclusions`: wider overlap list (e.g. v2), counted per stream for the paper, never filtered.
    if final and not benchmark:
        raise ValueError('Final mode needs the test-split scene exclusion list (KEEP contamination check)')
    for name, receipt in receipts.items():
        if name == 'pose' and mix is not None:
            streams[name] = mix
            continue
        if name == 'pose' and prefix is not None:
            streams[name] = dict(receipt=cfg['streams'][name], database=receipt['database'],
                count=receipt['dense_count'], source_count=receipt['count'], indices=receipt['dense_indices'])
            continue
        schema = routing.ROUTING_SCHEMA if name == 'routing' else 'c1-stream-v1'
        if name == 'routing' and receipt.get('scene_role', 'train') != 'train':
            raise ValueError('Training refuses a held-out routing stream')
        if name != 'pose' and (receipt.get('schema') != schema or receipt['stream'] != name
                or not division_admits(receipt['division'], division) or receipt.get('heldout_overlap') != 0
                or (name == 'pointing' and receipt.get('gt_masks_only') is not True)):
            raise ValueError('Preservation/pointing receipt or division differs')
        if name == 'pointing' and cfg.get('ground_target_filter'):
            from .ground_target_filter import TargetFilter
            expected = TargetFilter(cfg.get('remove_files', ()), shape_filter=True).settings()
            if receipt.get('target_filter', {}).get('settings') != expected:
                raise ValueError('Pointing preparation lacks the required target-filter rule')
        pinned(receipt['database'])
        with connect(receipt['database']) as conn:
            count, lo, hi = conn.execute('SELECT count(*), min(i), max(i) FROM rows').fetchone()
        if not count or receipt['count'] != count or lo != 0 or hi != count-1:
            raise ValueError('Database indices/count differ from the receipt')
        if cfg.get('frame_layout', 'spread') != 'spread':
            with connect(receipt['database']) as conn:
                for (row,) in conn.execute('SELECT row FROM rows ORDER BY i'):
                    row = json.loads(row)
                    if r0_filter is not None and r0_filter.excluded(row):
                        continue
                    if not data.single_image_row(row, name, training_mode=cfg.get('training_mode', 'mixed'),
                                                 geometry_online=cfg.get('geometry_online')):
                        data.layout_inputs(row, *data.layout_settings(cfg), verify_partners=True)
        streams[name] = dict(receipt=cfg['streams'][name], database=receipt['database'], count=count,
                             source_count=count)
        if benchmark:
            # Pose rows are filtered here; every other stream must already be clean (refuse otherwise).
            selected, hits, overlap, routed, held = [], 0, 0, 0, 0
            with connect(receipt['database']) as conn:
                for index, row, target in conn.execute('SELECT i,row,target FROM rows ORDER BY i'):
                    row = json.loads(row)
                    if r0_filter is not None and r0_filter.excluded(row):
                        selected.append(index)
                        continue
                    removals.assert_clean(row)
                    if name == 'pointing' and cfg.get('ground_target_filter') and row['pointing']['kind'] == 'gt_instance_mask':
                        from .ground_target_filter import mask_quality, pointing_key
                        point = row['pointing']
                        removals.assert_clean(dict(row_key=pointing_key(row)))
                        quality = mask_quality(data._load_mask(point['mask'], point.get('key', 'mask')))
                        if not quality['accepted'] or point.get('shape_quality') != quality:
                            raise ValueError('Pointing mask fails the required shape-quality rule')
                    if name == 'pose' and not dense_pose_row(row, json.loads(target)):
                        # 16-slot rows break per-frame carriers in duplicate/paired layouts.
                        continue
                    if name != 'pose' and held_row(row, name, held_qids, held_sources):
                        held += 1
                        continue
                    if name == 'vqa' and routed_type(row, cfg) and not cfg.get('tool_mode_flag'):
                        # A type that routes keeps only its routed traces; its direct answers would
                        # teach the opener decision a mix (route table, final mode).
                        routed += 1
                        continue
                    hit, seen = prepare_exclusions(row, pose_benchmark if name == 'pose' else benchmark, reported, name)
                    overlap += seen
                    if hit:
                        hits += 1
                    else:
                        selected.append(index)
            if hits and name != 'pose':
                raise ValueError(f'{name} stream contains {hits} benchmark-scene rows; rebuild it filtered')
            streams[name].update(benchmark_rows_dropped=hits, reported_overlap_rows=overlap)
            if name == 'pose' or routed or held:
                path = Path(cfg['preparation_output'])/f'{name}_indices.json'
                write(path, selected)
                streams[name].update(count=len(selected), indices=file_pin(path))
            if routed:
                streams[name].update(routed_type_rows_dropped=routed)
            if held:
                streams[name].update(held_rows_dropped=held)
        if cfg.get('training_mode') == 'pose_only':
            selected = []
            with connect(receipt['database']) as conn:
                for index, row, target in conn.execute('SELECT i,row,target FROM rows ORDER BY i'):
                    if dense_pose_row(json.loads(row), json.loads(target)):
                        selected.append(index)
            if len(selected) != 283200:
                raise ValueError('Pose-only requires exactly A1\'s 283200 dense all-32-frame rows')
            path = Path(cfg['preparation_output'])/'pose_indices.json'
            write(path, selected)
            streams[name].update(count=len(selected), indices=file_pin(path))
    if 'mdg' in cfg:
        from .stageb_mdg import prepare as prepare_mdg
        streams['mdg'] = prepare_mdg(cfg, benchmark, reported, scene_filter=scene_filter)
    scene_report = None
    if scene_filter is not None:
        from .s1_exclusions import apply
        streams, scene_report = apply(streams, cfg.get('dev_scene_exclusions'), cfg['preparation_output'],
                                      cfg.get('benchmark_scene_exclusions'), coverage=cfg.get('scene_coverage'))
        if any(not value['count'] for value in streams.values()):
            raise ValueError('Scene exclusions leave a required training stream empty')
    result = dict(**version_metadata, schema='c1-preparation-v1', config_sha256=identity(cfg), trainer_commit=commit,
                  streams=streams, model=pose['model'], division=division,
                  camera=pose['settings']['camera'],
                  # A Stage-1 depth init fixes the point-depth architecture to the artifact's own settings.
                  depth=(load(pinned(cfg['depth_init']))['camera']['point_depth'] if cfg.get('depth_init')
                         else pose['settings']['camera']['point_depth']),
                  carrier_placement=cfg['carrier_placement'], training_mode=cfg.get('training_mode', 'mixed'),
                  depth_enabled=cfg.get('depth_enabled', True), recipe=cfg['recipe'])
    result.update({k: cfg[k] for k in ('frame_layout', 'frame_pair_gap_seconds', 'skip_unsupervised_lm',
                                       'depth_fov_source', 'depth_init', 'exclusions', 'report_exclusions',
                                       'tool_mode_flag', 'ground_target_filter', 's1_route_policy', 'h1') if k in cfg})
    if 'mdg' in cfg:
        result['mdg'] = cfg['mdg']
    if 'validation' in cfg:
        result['validation'] = prepare_validation(cfg, division)
    if cfg.get('training_mode') == 'pose_only':
        # A warm-started pose-only run binds its init and sampler offset into the receipt.
        result.update({k: cfg[k] for k in POSE_ONLY_RECEIPT_KEYS if k in cfg})
    if cfg.get('geometry_online'):
        result.update(geometry_online=cfg['geometry_online'])
    if cfg.get('remove_files'):
        result['remove_files'] = removals.files
    if scene_report is not None:
        from .s1_exclusions import verify
        result.update(dev_scene_exclusions=cfg.get('dev_scene_exclusions'),
                      benchmark_scene_exclusions=cfg.get('benchmark_scene_exclusions'),
                      scene_filter_report=scene_report)
        verify(result, cfg)
    if cfg.get('h1', {}).get('faithful_own_camera_rows'):
        from .h1_faithful import prepare_identity
        result = prepare_identity(result, cfg)
    from .source_seal import binding
    sealed = binding(load(pinned(cfg['code'])), result['config_sha256'])
    if sealed is not None:
        result['source_seal'] = sealed
    if cfg.get('h1', {}).get('r0_rooms') is not None:
        from .h1_r0 import prepare as reserve_prepare
        result = reserve_prepare(result, cfg)
    if 'type_mix' in cfg:
        from .type_mix import prepare as prepare_type_mix
        result = prepare_type_mix(result, cfg)
    write(Path(cfg['preparation_output'])/'receipt.json', result)
    return result


def prepared(cfg, admission=False):
    validate(cfg)
    commit = authenticate(cfg)
    receipt = load(pinned(cfg['preparation']))
    if cfg.get('h1', {}).get('r0_rooms') is not None or 'h1_r0' in receipt:
        from .h1_r0 import before_admission
        receipt = before_admission(receipt, cfg)
    from .s1_route_policy import validate as validate_s1_route_policy
    if receipt.get('s1_route_policy') != validate_s1_route_policy(cfg):
        raise ValueError('Preparation frozen route table binding differs')
    from .source_seal import check_binding
    check_binding(receipt.get('source_seal'), load(pinned(cfg['code'])), receipt.get('config_sha256'))
    from .row_removals import Removals
    removals = Removals(cfg.get('remove_files', ()))
    if receipt.get('remove_files', []) != removals.files:
        raise ValueError('Preparation REMOVE-list pins differ')
    if receipt.get('ground_target_filter') != cfg.get('ground_target_filter'):
        raise ValueError('Preparation grounding target-filter rule differs')
    if receipt.get('config_sha256') != identity(cfg) or receipt.get('trainer_commit') != commit:
        # Config-only or code changes need no fresh prep when the prepared data is unchanged.
        warn(cfg, 'C1 preparation config/commit identity differs')
    if receipt.get('recipe') != cfg['recipe'] and (cfg.get('training_mode') == 'final' or cfg.get('geometry_online')):
        # Mix/schedule changes do not change the prepared streams.
        warn(cfg, 'C1 preparation recipe differs; using the config recipe')
        receipt = {**receipt, 'recipe': cfg['recipe']}
    if receipt.get('carrier_placement') != cfg['carrier_placement'] and cfg.get('training_mode') == 'final':
        # The prepared streams do not depend on placement; the model takes the config's placement.
        warn(cfg, 'C1 preparation carrier_placement differs; using the config placement')
        receipt = {**receipt, 'carrier_placement': cfg['carrier_placement']}
    from .trace_version import resolve
    resolve(receipt, cfg)
    if cfg.get('h1', {}).get('faithful_own_camera_rows'):
        from .h1_faithful import require_identity
        require_identity(receipt, cfg)
    if receipt.get('tool_mode_flag') != cfg.get('tool_mode_flag'):
        raise ValueError('C1 preparation tool_mode_flag differs from the configuration')
    if cfg.get('training_mode') == 'final':
        # Freeze-time levers change no prepared stream: the config's init, teacher projector and
        # camera loss weights win over the receipt.
        receipt = {**receipt, 'align': cfg.get('align'), 'init_artifact': cfg.get('init_artifact'),
                   'frame_markers': cfg.get('frame_markers', False),
                   'pointing_weights': cfg.get('pointing_weights'),
                   'camera': {**receipt['camera'], **cfg.get('camera_overrides', {})}}
    if 'h1' in cfg:
        receipt = {**receipt, 'h1': cfg['h1']}
    if cfg.get('geometry_online'):
        receipt = {**receipt, 'geometry_online': cfg['geometry_online'], 'init_artifact': cfg.get('init_artifact'),
                   'recipe': cfg['recipe']}
    if (receipt.get('schema') != 'c1-preparation-v1'
            or {k: v['receipt'] for k, v in receipt['streams'].items()} != cfg['streams']
            or receipt.get('carrier_placement') != cfg['carrier_placement']
            or receipt.get('training_mode') != cfg.get('training_mode', 'mixed')
            or receipt.get('depth_enabled') != cfg.get('depth_enabled', True)
            or receipt.get('recipe') != cfg['recipe']
            or (cfg.get('training_mode') == 'pose_only'
                and any(receipt.get(k) != cfg.get(k) for k in POSE_ONLY_RECEIPT_KEYS))):
        raise ValueError('C1 preparation differs from configuration/source')
    if (data.layout_settings(receipt) != data.layout_settings(cfg) or
            receipt.get('skip_unsupervised_lm') != cfg.get('skip_unsupervised_lm')
            or receipt.get('depth_fov_source') != cfg.get('depth_fov_source')
            or receipt.get('depth_init') != cfg.get('depth_init')):
        raise ValueError('C1 preparation frame layout/LM lever differs')
    if ('validation' in cfg) != ('validation' in receipt) or ('validation' in cfg and
            {k: receipt['validation'].get(k) for k in ('rows', 'slice')} != cfg['validation']):
        raise ValueError('C1 preparation validation pins differ')
    if 'validation' in receipt:
        value = receipt['validation']
        source = load(pinned(value['rows']))
        selected = load(pinned(value['slice']))
        pinned(value['database'])
        if removals.files:
            with connect(value['database']) as conn:
                for row, in conn.execute('SELECT row FROM rows'):
                    removals.assert_clean(json.loads(row))
        indices = load(pinned(value['indices']))
        from .c1_pose_mix import ROWS_ONLY_SCHEMAS
        if (source.get('schema') not in ROWS_ONLY_SCHEMAS or source['database'] != value['database']
                or len(indices) != value['count'] or not indices or any(type(i) is not int for i in indices)
                or indices != sorted(set(indices)) or value['scenes'] != len(selected['scenes'])):
            raise ValueError('C1 preparation validation rows differ')
    if receipt.get('mdg') != cfg.get('mdg'):
        raise ValueError('MDG preparation settings differ')
    for selected in receipt['streams'].values():
        value = selected.get('scene_source', selected)
        if value.get('kind') == 'mdg':
            from .stageb_mdg import verify as verify_mdg
            verify_mdg(cfg, value)
            continue
        source = load(pinned(value['receipt']))
        if value.get('kind') == 'mix':
            from .c1_pose_mix import validate_spec
            validate_spec(source)
            pinned(value['order'])
            for part in value['sources']:
                if part['kind'] == 'rows':
                    pinned(part['database'])
            continue
        if source['database'] != value['database'] or source['count'] != value.get('source_count', value['count']):
            raise ValueError('Stream receipt differs from preparation')
        if source.get('schema') == 'c1-paired-prefix-v2':
            paired_prefix(cfg, source)
            if value['count'] != source['dense_count'] or value['indices'] != source['dense_indices']:
                raise ValueError('Paired prefix sampler differs from preparation')
            continue
        if cfg.get('training_mode') == 'pose_only':
            indices = load(pinned(value['indices']))
            if (len(indices) != value['count'] or len(indices) != 283200
                    or any(type(i) is not int or not 0 <= i < source['count'] for i in indices)
                    or indices != sorted(set(indices))):
                raise ValueError('Dense row index differs from preparation')
        pinned(value['database'])
    from .s1_exclusions import verify
    verify(receipt, cfg)
    removals.verify_streams(receipt['streams'])
    model = load(pinned(receipt['model']))
    if admission:
        review = load(pinned(cfg['admission'])) if cfg.get('admission') else {}
        if (review.get('verdict') != 'PASS' or not review.get('reviewer')
                or review.get('config_sha256') != identity(cfg) or review.get('preparation') != cfg['preparation']):
            warn(cfg, 'Parent must bind independent C1 admission')
    if cfg.get('h1', {}).get('r0_rooms') is not None:
        from .h1_r0 import prepare as reserve_prepare
        receipt = reserve_prepare(receipt, cfg, phase='admission')
    if 'type_mix' in cfg or 'type_mix' in receipt:
        from .type_mix import bound as bound_type_mix
        bound_type_mix(receipt, cfg)
    return receipt, model


def load_model(manifest, receipt, processor, verify_assets=True, evaluation=False):
    from transformers import Qwen3_5ForConditionalGeneration
    from .camera_targets import carrier_id
    # Full base shards, unlike V-C, must be authenticated before LM loading.
    root = Path(manifest['root'])
    for name, sha in manifest['files'].items():
        if Path(name).name != name or (verify_assets and sha256(root/name) != sha):
            raise ValueError('Base checkpoint/processor asset changed')
    base = Qwen3_5ForConditionalGeneration.from_pretrained(root, local_files_only=True,
        trust_remote_code=False, dtype=torch.float32 if rehearsal.enabled() else torch.bfloat16,
        attn_implementation='sdpa')
    model = CarrierC1(base, receipt['camera'], receipt['depth'], carrier_id(processor.tokenizer),
                      receipt['carrier_placement'], receipt['training_mode'], receipt['depth_enabled'], receipt['recipe'],
                      receipt.get('skip_unsupervised_lm'), receipt.get('frame_layout', 'spread'),
                      receipt.get('depth_fov_source', 'private'),
                      **(dict(geometry_online=receipt['geometry_online'], geometry_runtime=dict(
                          image_mean=processor.video_processor.image_mean, image_std=processor.video_processor.image_std))
                         if receipt.get('geometry_online') else {}))
    from .trace_version import bind
    bind(model, receipt, {'trace_program_version': receipt.get('trace_program_version', '3.13')})
    if receipt['training_mode'] == 'final':
        init = receipt.get('init_artifact')
        if init:
            # LM first: the routing openers then initialize from the warm-started rows.
            model.init_report = init_from_artifact(model, init, verify=verify_assets, part='lm',
                                                  **({'evaluation': True} if evaluation else {}))
        from . import ground_tokens
        if ground_tokens.enabled(receipt):
            ground_tokens.initialize_after_warm(model, processor, getattr(model, 'init_report', None))
        else:
            routing.init_routing_embeddings(model, processor._routing_tokens)
        if receipt.get('depth_init'):
            from .carrier_c1 import load_depth_stage1
            model.depth_init_report = load_depth_stage1(model, receipt['depth_init'], verify=verify_assets)
        if receipt.get('align'):
            # C1-r teacher package: the 2H projector feeds the pose head (attach before FSDP/optimizer).
            from . import c1r_align
            c1r_align.attach(model, receipt['align'], training=True)
        if init:
            model.init_report.update(init_from_artifact(model, init, verify=verify_assets, part='heads',
                                                        **({'evaluation': True} if evaluation else {})))
    elif receipt['training_mode'] == 'pose_only' and receipt.get('init_artifact'):
        # Warm-started pose-only run: the milestone's LM and vision weights, then its pose head.
        init = receipt['init_artifact']
        model.init_report = init_from_artifact(model, init, verify=verify_assets, part='lm',
                                              **({'evaluation': True} if evaluation else {}))
        model.init_report.update(init_from_artifact(model, init, verify=verify_assets, part='heads',
                                                    **({'evaluation': True} if evaluation else {})))
    if receipt.get('geometry_online'):
        # After the warm start: the pinned G3T weights, then rms_cam from the loaded CAM embeddings.
        from .g3t_online import normalize
        gx = normalize(receipt['geometry_online'])
        config = load(pinned(gx['encoder']['config']) if verify_assets else gx['encoder']['config']['path'])
        rehearsal.validate_tower_config(config)
        encoder = model.auxiliary_heads.geometry_encoder
        report = encoder.load_pinned(gx['encoder']['weights']['path'], verify_assets)
        pose = model.auxiliary_heads.pose
        with torch.no_grad():
            rms = pose.tokens.float().square().mean(-1).sqrt()[torch.tensor([0]+[1]*31,
                                                                          device=pose.tokens.device)].median()
            if not ('gf1' in gx and getattr(model, 'init_report', {}).get('gf1_camera_loaded')):
                pose.cam_token_connector.rms_cam.copy_((rms * gx['connector']['rms_scale']).reshape(1))
        model.gx_report = dict(encoder=report, rms_cam=float(pose.cam_token_connector.rms_cam.item()),
                              mode=gx['mode'], trainable_params=sum(p.numel() for p in encoder.parameters()
                                                                   if p.requires_grad))
        print(json.dumps({'gx': model.gx_report}), flush=True)
    if 'mdg' in receipt:
        from .stageb_mdg import attach
        attach(model, receipt['mdg'], processor, receipt['streams']['mdg']['inputs'])
        model.mdg_receipt = receipt
    if 'gf1' in (model.geometry_online or {}):
        from .gf1 import configure_trainables
        configure_trainables(model)
    if not evaluation:
        from .trained_groups import capture
        capture(model)
    return model


INIT_KEYS = {'artifact', 'lm', 'heads'}


def validate_init(spec):
    if (not isinstance(spec, dict) or set(spec) != INIT_KEYS or spec['lm'] not in ('full', 'base')
            or not isinstance(spec['heads'], list) or len(set(spec['heads'])) != len(spec['heads'])
            or any(h not in ('pose', 'frame_embeddings', 'depth', 'patch_fusion', 'gf1') for h in spec['heads'])
            or (spec['lm'] == 'base' and not spec['heads'])
            or not isinstance(spec['artifact'], dict) or set(spec['artifact']) != {'path', 'sha256'}):
        # heads [] with lm full = warm LM with cold (planned-init) heads; lm base with heads = E4 graft.
        raise ValueError('init_artifact needs {artifact pin, lm full|base, heads ⊆ [pose, frame_embeddings, depth, patch_fusion, gf1]}')
    return spec


def init_mirror(artifact_pin):
    """Node-local copy of the init milestone staged and hash-verified by the kit (C1_INIT_LOCAL)."""
    root = os.environ.get('C1_INIT_LOCAL')
    if not root:
        return None
    local = Path(root)/artifact_pin['sha256'][:16]
    return local if (local/'.verified').is_file() else None


def init_from_artifact(model, spec, verify=True, part='heads', evaluation=False):
    """Warm-start from a C1-family milestone export (carrier-c1-artifact-v1).

    part 'lm': lm 'full' replaces every base tensor (LM and frozen vision) with the export;
    'base' keeps the base model and grafts heads only (the E4 fallback). part 'heads': the
    listed head modules load by exact name and shape; every other head keeps its
    planned init.
    """
    validate_init(spec)
    if part not in ('lm', 'heads'):
        raise ValueError('init part must be lm or heads')
    local = init_mirror(spec['artifact'])
    artifact = load(local/'artifact.json' if local else (pinned(spec['artifact']) if verify else spec['artifact']['path']))
    if local and sha256(local/'artifact.json') != spec['artifact']['sha256']:
        raise ValueError('Staged init artifact differs from its pin')
    if artifact.get('schema') != 'carrier-c1-artifact-v1' or artifact.get('pose_backing') != 'lm_final_norm':
        raise ValueError('init_artifact is not a C1 milestone export')
    if (artifact.get('placement') != model.carrier_placement
            or artifact.get('frame_layout', 'spread') != model.frame_layout
            or artifact.get('carrier_position_policy', 'native_v1') != model.carrier_position_policy):
        raise ValueError('init_artifact placement/layout/position policy differs from the model')
    donor_fusion = (artifact.get('geometry_online') or {}).get('gf1')
    live_fusion = (getattr(model, 'geometry_online', None) or {}).get('gf1')
    # Zero initialization is a training choice. Evaluation must restore trained GF1 tensors.
    explicit_zero = bool(not evaluation and live_fusion and live_fusion['stage'] == 2 and live_fusion['gf1_init'] == 'zero')
    if evaluation and live_fusion and 'gf1' not in spec['heads']:
        raise ValueError('GF1 export requires gf1 in evaluator init heads')
    if explicit_zero and 'gf1' in spec['heads']:
        raise ValueError('Explicit GF1 zero init conflicts with loading gf1 heads')
    if donor_fusion and (not live_fusion or ('gf1' not in spec['heads'] and not explicit_zero)):
        raise ValueError('GF1 export requires gf1 in the model and init heads')
    if live_fusion and live_fusion['stage'] == 2 and live_fusion['gf1_init'] != 'zero' and 'gf1' not in spec['heads']:
        raise ValueError('Stage 2 requires gf1 init heads or explicit gf1_init: zero')
    if 'gf1' in spec['heads']:
        donor = (artifact.get('geometry_online') or {}).get('gf1')
        live = (model.geometry_online or {}).get('gf1')
        architecture = ('layers', 'hidden', 'top_k', 'injection')
        if not donor or not live or any(donor[k] != live[k] for k in architecture):
            raise ValueError('GF1 warm-start architecture differs')
    report = dict(artifact=spec['artifact'], step=artifact.get('step'), lm=spec['lm'], heads=sorted(spec['heads']))
    opener_ids = (artifact.get('mdg', {}).get('lora_config') or {}).get('opener_tokens')
    if spec['lm'] == 'full' and opener_ids:
        report['ground_token_ids'] = opener_ids
    if part == 'lm':
        if spec['lm'] == 'full':
            directory = local/'full_weights' if local else Path(artifact['full_weights']['path']).parent
            if not local and verify:
                pinned(artifact['full_weights'])
                full_ft.read_export(directory)
            report['lm_tensors'] = load_export_masters(model, directory)
        return report
    teacher_space = artifact.get('pose_projector') == 'teacher_space_mlp_v1'
    live_teacher = bool(getattr(model.auxiliary_heads.pose, 'projector_fp32', False))
    if teacher_space and not live_teacher:
        raise ValueError('A teacher-space init artifact needs the align projector in the model')
    # A pre-teacher init (C1-a) with the teacher package added: the 2H projector keeps its planned init.
    fresh = live_teacher and not teacher_space
    keep = lambda key: key.split('.')[0] in spec['heads'] and not (fresh and key.startswith('pose.projector.'))
    heads_path = local/'heads.pt' if local else (pinned(artifact['heads']) if verify else Path(artifact['heads']['path']))
    state = torch.load(heads_path, map_location='cpu', weights_only=True)
    if spec['lm'] == 'full' and opener_ids:
        from .ground_tokens import retain_warm_rows
        retain_warm_rows(model, state, opener_ids)
    live = model.auxiliary_heads.state_dict()
    wanted = {k for k in live if keep(k)}
    selected = {k: v for k, v in state.items() if keep(k)}
    # A pose_only donor (C1-a, C1-r) trained with zero gravity and scale weights, so it never built
    # those branches; the final-mode head has them, and they keep their planned init.
    optional = (('pose.head.gravity_branch.', 'pose.head.scale_branch.', 'pose.head.scale_token')
                if artifact.get('training_mode') == 'pose_only' else ())
    donor_geometry = artifact.get('geometry_online') or {}
    if getattr(model, 'geometry_online', None) and not donor_geometry:
        optional += ('pose.cam_token_connector.', 'patch_fusion.')
    if donor_geometry.get('patch_fusion') and hasattr(model.auxiliary_heads, 'patch_fusion') and 'patch_fusion' not in spec['heads']:
        raise ValueError('Warm patch_fusion donor requires patch_fusion in init heads')
    absent = {k for k in wanted - set(selected) if optional and k.startswith(optional)}
    wanted -= absent
    report['projector'] = 'planned_init' if fresh else 'loaded'
    report['planned_init'] = sorted(absent | {k for k in live if k.startswith('patch_fusion.') and k not in selected})
    if set(selected) != wanted:
        raise ValueError(f'init heads differ: missing {sorted(wanted - set(selected))[:5]}, '
                         f'extra {sorted(set(selected) - wanted)[:5]}')
    for name, value in selected.items():
        if tuple(value.shape) != tuple(live[name].shape):
            raise ValueError('init head tensor shape differs: ' + name)
    result = model.auxiliary_heads.load_state_dict({k: v.to(live[k].dtype) for k, v in selected.items()}, strict=False)
    if result.unexpected_keys or set(result.missing_keys) != set(live) - wanted:
        raise ValueError('init head load touched modules outside the selected heads')
    if 'gf1' in (model.geometry_online or {}):
        from .gf1 import check_camera_context
        check_camera_context(model, artifact)
        report['gf1_camera_loaded'] = 'pose.cam_token_connector.rms_cam' in selected
    report.update(head_tensors=len(selected), kept=sorted({k.split('.')[0] for k in set(live) - wanted}))
    init = artifact.get('head_init') or {}
    if spec['heads'] and 'pose' in spec['heads'] and init.get('prefix') == 'global_camera_head.':
        names = set(init.get('copied', [])) | set(init.get('derived', []))
        # C1-r's LR split: copied teacher trunk tensors keep the LM rate (c1r_run.optimizer_groups).
        model.inherited_head_params = sorted(n for n in names if n.startswith(
            ('token_norm.', 'trunk.', 'trunk_norm.', 'pose_modulation.')) or n == 'embed_pose.bias')
        report['inherited_head_params'] = len(model.inherited_head_params)
    print(json.dumps({'init_artifact': {k: v for k, v in report.items() if k != 'artifact'}}), flush=True)
    return report


def load_export_masters(model, directory):
    """Copy a BF16 full-weights export into the FP32 base masters by exact name and shape."""
    from safetensors.torch import load_file
    directory = Path(directory)
    manifest = json.loads((directory/full_ft.EXPORT_MANIFEST).read_text())
    index = json.loads((directory/manifest['index']['name']).read_text())
    live = dict(full_ft.base_parameters(model))
    if set(index['weight_map']) != set(live):
        missing, extra = sorted(set(live) - set(index['weight_map']))[:5], sorted(set(index['weight_map']) - set(live))[:5]
        raise ValueError(f'Full-weights tensors differ from the model (missing {missing}, extra {extra})')
    loaded = 0
    for item in manifest['files']:
        tensors = load_file(str(directory/item['name']), device='cpu')
        expected = {name for name, shard in index['weight_map'].items() if shard == item['name']}
        if set(tensors) != expected:
            raise ValueError('Full-weights shard membership differs from index: ' + item['name'])
        for name, value in tensors.items():
            parameter = live[name]
            if value.shape != parameter.shape or value.dtype != torch.bfloat16:
                raise ValueError('Full-weights tensor shape or dtype differs: ' + name)
            with torch.no_grad():
                parameter.copy_(value.to(device=parameter.device, dtype=parameter.dtype))
            loaded += 1
    if loaded != len(live):
        raise ValueError('Full-weights load did not cover every base tensor')
    return loaded


class Rows:
    def __init__(self, receipt, processor):
        self.connections = {k: connect(v['database']) for k, v in receipt['streams'].items() if v.get('kind') not in ('mix', 'mdg')}
        self.processor = processor
        from .type_mix import bound as bound_type_mix
        self.type_mix = bound_type_mix(receipt, receipt)
        self.h1 = receipt.get('h1', {})
        self.placement = receipt.get('carrier_placement', data.C1_A)
        self.receipt_pointing_weights = receipt.get('pointing_weights')
        self.tool_flag = receipt.get('tool_mode_flag')
        self.mode = receipt.get('training_mode', 'mixed')
        self.layout, self.gap = data.layout_settings(receipt)
        self.geometry_online = receipt.get('geometry_online')
        self.indices = {k: load(pinned(v['indices'])) for k, v in receipt['streams'].items() if 'indices' in v}
        self.counts = {k: v['count'] for k, v in receipt['streams'].items()}
        self.mixes = {}
        self.validation = None
        self.mdg = None
        if 'mdg' in receipt:
            from .stageb_mdg import dataset
            self.mdg = dataset(receipt, processor)
        if 'validation' in receipt:
            from .c1_pose_mix import RowSource
            value = receipt['validation']
            self.validation = RowSource(value, processor, self.placement, self.mode, self.layout, self.gap)
            self.validation_indices = load(pinned(value['indices']))
        for name, value in receipt['streams'].items():
            if value.get('kind') == 'mix':
                from .c1_pose_mix import PoseMix
                self.mixes[name] = PoseMix(value, processor, self.placement, self.mode, self.layout, self.gap,
                                           receipt['depth']['num_points_per_frame'])

    def count(self, stream):
        return self.counts[stream]

    def validation_count(self):
        return len(self.validation_indices) if self.validation is not None else 0

    def validation_get(self, index):
        index = self.validation_indices[index]
        batch, targets, audit = self.validation.get(index)
        row = json.loads(self.validation.conn.execute('SELECT row FROM rows WHERE i=?', (index,)).fetchone()[0])
        return batch, targets, {**audit, 'scene': row['scene']}

    def row(self, stream, index):
        if stream in self.indices:
            index = self.indices[stream][index]
        row = self.connections[stream].execute('SELECT row,target FROM rows WHERE i=?',(index,)).fetchone()
        if row is None:
            raise ValueError('Missing planned C1 row')
        value = json.loads(row[0])
        if stream == 'routing':
            value = routing.tool_mode(value, self.tool_flag)
        return value, json.loads(row[1])

    def get(self, stream, index):
        if stream == 'mdg':
            item = self.mdg._item(index)
            return ({**item['batch'], 'aux_mdg_labels': item['labels']}, item['targets'],
                    dict(qid=item['clip']['qid'], Q=len(item['labels'])))
        if stream in self.mixes:
            return self.mixes[stream].get(index)
        row, target = self.row(stream, index)
        if stream == 'routing':
            batch, audit = routing.encode(self.processor, row, self.placement, self.mode, self.layout, self.gap,
                                           geometry_online=self.geometry_online)
            if self.h1.get('routing_pose_targets'):
                from .h1 import pose_targets
                targets, counts = pose_targets(row, batch, self.h1)
                audit = {**audit, 'h1_pose': counts, 'h1': dict(
                    type=row['routing']['question_type'], values='gt', refused=None, answer_differs=False)}
                return batch, targets, audit
            return batch, None, audit
        if self.mode == 'pose_only' and not dense_pose_row(row, target):
            raise ValueError('Pose-only index selected a non-dense row')
        options = {} if self.layout == 'spread' else dict(frame_layout=self.layout, frame_pair_gap_seconds=self.gap)
        if self.geometry_online:
            options['geometry_online'] = self.geometry_online
        batch, targets, audit = data.encode(self.processor, row, target, stream, self.placement, self.mode, **options)
        if self.mode == 'final' and stream in ('vqa', 'pointing'):
            # Logging-only token tags: coordinate/format/null for pointing, answer/trace for VQA.
            tokenizer = self.processor.tokenizer
            batch['aux_segments'] = data.segment_tags(batch['labels'][:, 1:], stream,
                                                      lambda i: tokenizer.decode([i]))
            batch['aux_segments'] = torch.cat((torch.full_like(batch['aux_segments'][:, :1], -1),
                                               batch['aux_segments']), dim=1)
        weights = self.receipt_pointing_weights if self.mode == 'final' and stream == 'pointing' else None
        if weights:
            tokenizer = self.processor.tokenizer
            shifted = data.pointing_token_weights(batch['labels'][:, 1:], lambda i: tokenizer.decode([i]), **weights)
            batch['aux_token_weights'] = torch.cat((torch.zeros_like(shifted[:, :1]), shifted), dim=1)
        return batch, targets, audit

    def close(self):
        if self.validation is not None:
            self.validation.close()
        for conn in self.connections.values():
            conn.close()
        for mix in self.mixes.values():
            mix.close()


def move(value, device):
    return None if value is None else {k: (v if k == 'aux_mdg_labels' else v.to(device)) for k, v in value.items()}


def norm(parameters):
    values = [p.grad.float().square().sum() for p in parameters if p.grad is not None]
    return float(torch.sqrt(sum(values))) if values else 0.


def wrap_model(model, device, mixed_precision=True):
    offload = os.environ.get('C1_FSDP_CPU_OFFLOAD', '0')
    if offload not in ('0', '1'):
        raise ValueError('C1_FSDP_CPU_OFFLOAD must be 0 or 1')
    wrapped=full_ft.wrap_full_model(model,list(model.auxiliary_heads.parameters()),dist.group.WORLD,
                                    device,mixed_precision=mixed_precision, cpu_offload=offload == '1',
                                    **({'frozen_base': True} if (getattr(model, 'geometry_online', None) or {}).get('gf1', {}).get('stage') == 1 else {}))
    wrapped.c1_cpu_offload = offload == '1'
    # FSDP's root default would also downcast the floating GT tensors in our
    # targets dict. Native Qwen casts its visual inputs; embeddings already have
    # the base compute dtype. Keep GT and replicated head math in FP32.
    wrapped.mixed_precision=replace(wrapped.mixed_precision,cast_root_forward_inputs=False)
    return wrapped


def memory_stats(device):
    if device.type != 'cuda':
        return dict(allocated_bytes=0, reserved_bytes=0)
    return dict(allocated_bytes=torch.cuda.memory_allocated(device),
                reserved_bytes=torch.cuda.memory_reserved(device))


class OffloadedGradients:
    """Accumulate reduced CPU shards outside FSDP, which overwrites its CPU buffer.

    Never use no_sync: that retains full unsharded gradients on the accelerator.
    Replicated heads keep the ordinary autograd accumulation path.
    """
    def __init__(self, model):
        self.parameters = [p for n, p in full_ft.named_trainable(model) if not n.startswith('auxiliary_heads.')]
        self.sums = {}

    def capture(self):
        for p in self.parameters:
            if p.grad is not None:
                if p.device.type != 'cpu':
                    raise ValueError('Offloaded base gradients must reside on CPU')
                if p in self.sums:
                    self.sums[p].add_(p.grad)
                else:
                    self.sums[p] = p.grad.detach().clone()
                p.grad = None

    def restore(self):
        for p, value in self.sums.items():
            p.grad = value


def processor_for_receipt(manifest, receipt):
    """Bind native GX readouts and deterministic final-mode head-opener tokens."""
    processor = processor_for(manifest['root'])
    processor._s1_rehearsal = rehearsal.fixture_manifest(manifest)
    if receipt.get('geometry_online'):
        from .g3t_online import NATIVE_INPUT
        if receipt['geometry_online']['input'] == NATIVE_INPUT:
            # Mode-x callers encode READOUT_TARGET as VQA without an explicit GX argument.
            processor._c1_readout_geometry_online = receipt['geometry_online']
    if receipt.get('training_mode') == 'final':
        routing.add_routing_tokens(processor, include_ground=bool(receipt.get('mdg')))
        from . import ground_tokens
        if ground_tokens.enabled(receipt):
            ground_tokens.add(processor)
        # Per-group `Frame k: ` markers (config switch, off by default); every encode path reads it.
        processor.tokenizer._c1_frame_markers = bool(receipt.get('frame_markers', False))
    return processor


def own_values(model, rows, batch, audit, index, decision, device):
    """Scheduled sampling: replace GT routed values with the model's own head values.

    `decision` = (depth_own, pose_own) is identical on every rank (rank zero broadcasts
    it), so every rank runs the no-grad readout forward in the same microstep. A row
    with closed gates keeps GT values. Once a gate requests own values, a render
    refusal stops all ranks before backward instead of changing the supervision.
    """
    if getattr(rows, 'h1', {}).get('faithful_own_camera_rows'):
        from .h1_faithful import own_values as faithful_own_values
        return faithful_own_values(model, rows, batch, audit, index, decision, device)
    if not any(decision):
        return batch, audit
    try:
        row, _ = rows.row('routing', index)
        queries = routing.depth_queries(row['routing'])
        uv, slots = routing.query_tensor(queries)
        query_error = None
    except (routing.RenderError, KeyError, ValueError) as exc:
        # Every rank must still join the collective readout forward.
        queries, slots, query_error = [], [], exc
        uv = torch.full((32, 1, 2), 500.)
    with torch.no_grad():
        readout = model(move(routing.prefix_batch(batch), device), {'uv': uv.to(device)}, stream='readout')
    failure = None
    result = None
    try:
        if query_error is not None:
            raise routing.RenderError(f'depth queries: {query_error}')
        geometry, source = routing.row_geometry(row['routing'], readout, queries, slots, *decision)
        if geometry is None:
            raise routing.RenderError(f'own geometry unavailable: {source}')
        target, spans, segments = routing.rerender(row['routing'], geometry)
        result = routing.encode_own(rows.processor, row, batch, target, spans, segments, source)
    except (routing.RenderError, ValueError) as exc:
        failure = str(exc)[:200]
    flag = torch.tensor([failure is not None], dtype=torch.int32, device=device)
    if dist.is_initialized():
        dist.all_reduce(flag, op=dist.ReduceOp.MAX)
    if flag.item():
        raise ValueError(f'Own-value rendering failed on a rank; refusing GT fallback: {failure}')
    return result


def replay_gates(output, start_step, gates):
    """Rebuild the gate EMAs from the run's metrics files up to the resume step."""
    by_step = {}
    for path in sorted(Path(output).glob('metrics_*.jsonl')):
        with path.open() as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record['step'] <= start_step:
                    by_step[record['step']] = record['ranks'][0].get('head_metrics') or {}
    for step in sorted(by_step):
        gates.update(by_step[step])
    return gates


MAX_TOKENS = 16384


def check_row(batch, targets, stream, model):
    """Pre-forward checks of what the final-mode losses assert, so a bad row fails before any
    collective instead of inside one rank's forward (camera_head.loss, PrivateDepth, labels)."""
    tokens = batch['input_ids'].shape[1]
    recipe = getattr(model, 'recipe', {})
    limit = recipe.get('max_row_tokens', MAX_TOKENS)
    if tokens > limit:
        raise ValueError(f'{tokens} tokens exceed {limit}')
    if stream == 'routing' and 'max_routing_suffix_tokens' in recipe:
        suffix = tokens - int(batch['aux_suffix_start'].item())
        if suffix > recipe['max_routing_suffix_tokens']:
            raise ValueError(f'{suffix} routing suffix tokens exceed {recipe["max_routing_suffix_tokens"]}')
    image_vqa = (stream == 'vqa' and getattr(model, 'training_mode', None) == 'final'
                 and bool(getattr(model, 'geometry_online', None)))
    if (stream == 'pointing' or image_vqa) and 'image_grid_thw' in batch:
        if (batch['image_grid_thw'].shape != (1, 3) or int(batch['image_grid_thw'][0, 0]) != 1
                or 'pixel_values' not in batch or targets is not None
                or any(k in batch for k in ('video_grid_thw', 'pixel_values_videos'))
                or any(k.startswith('aux_camera') for k in batch)):
            raise ValueError('Single-image pointing requires one image without video or camera targets'
                             if stream == 'pointing' else 'Single-image VQA requires one image without video or camera targets')
        if not (batch['labels'][:, 1:] != -100).any():
            raise ValueError(f'{stream} row has no assistant labels')
        return
    positions = batch['aux_camera_positions']
    valid = positions >= 0
    if positions.shape != (1, 32) or torch.any(valid != (valid.long().cumprod(dim=1) > 0)):
        raise ValueError('Carrier positions must be a prefix of 32 slots')
    if stream == 'mdg':
        labels = batch.get('aux_mdg_labels')
        if (not isinstance(labels, list) or not labels or not all(isinstance(v, str) and v for v in labels)
                or targets is None or targets['clip_present'].shape != (len(labels),)
                or targets['frame_presence'].shape != (len(labels), 32)
                or not targets['mask_valid'].any()):
            raise ValueError('MDG row requires labels and eligible 32-frame mask targets')
        from .mdg_features import suffix_tokens
        from .grounding_features import frame_token_index
        model.check_placement(batch)
        if frame_token_index(batch).shape[0] != 32 or not (batch['attention_mask'] == 1).all():
            raise ValueError('MDG requires an unpadded 32-frame prefix')
        suffix_lengths = [len(suffix_tokens(model.mdg_tokenizer, label)[0]) for label in labels]
        if 'max_row_tokens' in recipe and tokens + max(suffix_lengths) > limit:
            raise ValueError(f'{tokens + max(suffix_lengths)} MDG prefix-plus-suffix tokens exceed {limit}')
        return
    if stream == 'pose':
        mask = targets['aux_camera_mask']
        if mask.shape != (1, 32) or torch.any(mask & ~valid) or not mask.any():
            raise ValueError('Pose targets name slots without carriers')
        depth = targets.get('aux_point_depth_mask')
        if depth is None or depth.shape[:2] != (1, 32) or torch.any(depth.any(-1) & ~valid):
            raise ValueError('Depth labels name slots without visible frames')
        uv = targets.get('aux_point_depth_uv')
        if uv is None or uv.shape != (*depth.shape, 2):
            raise ValueError('Depth queries need one uv pair per depth label')
        labelled = uv[depth.bool()]
        if not bool(torch.isfinite(labelled).all()) or bool((labelled < 0).any()) or bool((labelled > 1000).any()):
            raise ValueError('Labelled depth queries must lie in [0, 1000] x [0, 1000]')
        if hasattr(model, 'align_settings') and ('aux_g3t_cam' not in targets or 'aux_g3t_valid' not in targets):
            raise ValueError('Teacher-aligned pose rows need aux_g3t_cam and aux_g3t_valid')
    elif not (batch['labels'][:, 1:] != -100).any():
        raise ValueError(f'{stream} row has no assistant labels')


SKIPPED = dict(skipped=0, total=0)


def fetch(rows, stream, index, model, tries=8, device=None, distributed=False):
    """Every rank agrees on each microstep's outcome. A row that fails to encode or to pass the
    loss checks on ANY rank moves every rank to its next candidate row of the same stream (MIN
    all-reduce per try), so one bad row never leaves the other ranks in a collective. After
    `tries` failures every rank skips the microstep together (returns None). Other modes refuse."""
    if getattr(model, 'training_mode', None) != 'final':
        return rows.get(stream, index)
    count = rows.count(stream)
    errors = []
    for offset in range(tries):
        candidate = (index + offset) % count
        try:
            batch, targets, audit = rows.get(stream, candidate)
            check_row(batch, targets, stream, model)
            ok = 1
        except Exception as exc:  # any row error; the decision below is shared by all ranks
            ok, batch = 0, None
            errors.append(f'{type(exc).__name__}: {str(exc)[:160]}')
        flag = torch.tensor([ok], dtype=torch.int32, device=device or 'cpu')
        if distributed:
            dist.all_reduce(flag, op=dist.ReduceOp.MIN)
        if not flag.item() and 'gf1' in (getattr(model, 'geometry_online', None) or {}):
            raise ValueError('GF1 row failure forbids substitution: ' + '; '.join(errors))
        if not flag.item():
            raise ValueError(f'Final-mode row failure: stream={stream}, index={index}, local_errors={errors}; no substitution')
        if flag.item():
            audit = {**(audit or {}), 'index': candidate}
            if offset:
                audit.update(substituted_from=index, row_errors=errors, offset=offset)
            return batch, targets, audit
    print(json.dumps({'row_skip': dict(stream=stream, index=index, errors=errors[-3:])}), flush=True)
    return None


def skip_guard(skipped, total, limit=.01, floor=100):
    """All ranks hold identical counters (shared skip decisions), so they abort together."""
    if total >= floor and skipped > limit * total:
        raise ValueError(f'{skipped} of {total} microsteps skipped (> {limit:.0%}); stopping')


def fetch_nominal(rows, stream, indices, model, tries=8, device=None, distributed=False):
    """Retry one reference-world microstep across all of this rank's physical slices.

    Every slice is checked before any forward. One shared offset, or one exhausted
    skip, applies to the entire nominal group, including slices on other ranks.
    """
    count = rows.count(stream)
    errors = [[] for _ in indices]
    for offset in range(tries):
        fetched, ok = [], 1
        for slot, index in enumerate(indices):
            candidate = (index + offset) % count
            try:
                batch, targets, audit = rows.get(stream, candidate)
                check_row(batch, targets, stream, model)
                audit = {**(audit or {}), 'index': candidate}
                if offset:
                    audit.update(substituted_from=index, row_errors=list(errors[slot]), offset=offset)
                fetched.append((batch, targets, audit))
            except Exception as exc:
                ok = 0
                errors[slot].append(f'{type(exc).__name__}: {str(exc)[:160]}')
        flag = torch.tensor([ok], dtype=torch.int32, device=device or 'cpu')
        if distributed:
            dist.all_reduce(flag, op=dist.ReduceOp.MIN)
        if not flag.item() and 'gf1' in (getattr(model, 'geometry_online', None) or {}):
            raise ValueError('GF1 row failure forbids substitution: ' + str(errors))
        if not flag.item():
            raise ValueError(f'Final-mode row failure: stream={stream}, indices={indices}, local_errors={errors}; no substitution')
        if flag.item():
            return fetched
        # Release failed candidates before encoding the next full group.
        fetched.clear()
    print(json.dumps({'row_skip': dict(stream=stream, indices=indices, errors=errors)}), flush=True)
    return [None] * len(indices)


def nominal_slices(recipe, plan):
    """Validate reference-world grouping before any rank enters a collective."""
    world = recipe['world_size']
    reference = recipe.get('reference_world_size', world)
    factor = reference // world
    if reference % world or factor < 1 or len(plan) % factor:
        raise ValueError('Plan cannot form complete reference-world groups')
    if factor > 1:
        for start in range(0, len(plan), factor):
            group = plan[start:start + factor]
            if any(stream != group[0][0] or len(indices) != world for stream, indices in group):
                raise ValueError('Reference-world group must contain equal same-stream slices')
    return factor


def fetch_plan(rows, model, plan, rank, device=None, distributed=False):
    """Yield each physical slice using its reference-world admission decision."""
    if 'stream_rows_per_step' in model.recipe:
        from .e2e_recipe import plan_groups
        groups = list(plan_groups(model.recipe, plan))
    else:
        factor = nominal_slices(model.recipe, plan) if getattr(model, 'training_mode', None) == 'final' else 1
        groups = [plan[start:start + factor] for start in range(0, len(plan), factor)]
    for group in groups:
        factor = len(group)
        stream, indices = group[0]
        if factor == 1:
            yield fetch(rows, stream, indices[rank], model, device=device, distributed=distributed)
        else:
            local = [part[rank] for _, part in group]
            nominal = fetch_nominal(rows, stream, local, model, device=device, distributed=distributed)
            for slot in range(factor):
                result = nominal[slot]
                nominal[slot] = None
                yield result


def clip_groups(model, attached):
    """(carrier/frame embeddings, other heads) in final mode; ([], attached) otherwise. Disjoint."""
    if getattr(model, 'training_mode', None) != 'final':
        return [], attached
    special = [model.auxiliary_heads.pose.tokens]
    if hasattr(model.auxiliary_heads, 'frame_embeddings'):
        special.append(model.auxiliary_heads.frame_embeddings.weight)
    carriers = [p for p in attached if any(p is q for q in special)]
    return carriers, [p for p in attached if all(p is not c for c in carriers)]


def optimize_step(model, optimizer, rows, plan, rank, device, step, distributed=False, gates=None):
    """Rank-aligned microsteps (four in mixed/pose-only); FSDP reduces each (no large no_sync grads)."""
    started, waiting = time.perf_counter(), 0.
    unwrapped = model.module if distributed else model
    recipe = unwrapped.recipe
    if 'stream_rows_per_step' in recipe:
        from .e2e_recipe import plan_groups
        groups = list(plan_groups(recipe, plan))
        group_ids = [i for i, group in enumerate(groups) for _ in group]
        group_starts = {sum(len(g) for g in groups[:i]) for i in range(len(groups))}
    else:
        factor = nominal_slices(recipe, plan) if getattr(unwrapped, 'training_mode', None) == 'final' else 1
        group_ids = [i // factor for i in range(len(plan))]
        group_starts = set(range(0, len(plan), factor))
    optimizer.zero_grad(set_to_none=True)
    offload = bool(getattr(model, 'c1_cpu_offload', False))
    accumulated = OffloadedGradients(model) if offload else None
    phase_memory, peaks, reserved_peaks = [], [], []
    components, shapes, pose_batch = {}, [], None
    head_sums = dict.fromkeys(routing.Gates.METRICS, 0.)
    head_counts = dict.fromkeys(routing.Gates.METRICS, 0)
    decisions = torch.zeros((len(plan), 2), dtype=torch.int32, device=device)
    if gates is not None:
        for microstep, (stream, _) in enumerate(plan):
            if stream == 'routing':
                decisions[microstep] = torch.tensor(gates.decide(step, group_ids[microstep]), dtype=torch.int32)
        if distributed:
            dist.broadcast(decisions, src=0)
    skipped, stream_sums, stream_counts = [], {}, {}
    gf1_enabled = (getattr(unwrapped, 'geometry_online', None) or {}).get('gf1')
    screen = None
    screen_metrics = None
    fetched_rows = fetch_plan(rows, unwrapped, plan, rank, device=device, distributed=distributed)
    for microstep, (stream, indices) in enumerate(plan):
        if device.type == 'cuda':
            torch.cuda.reset_peak_memory_stats(device)
        start = time.perf_counter()
        fetched = next(fetched_rows)
        waiting += time.perf_counter()-start
        if getattr(unwrapped, 'training_mode', None) == 'final':
            SKIPPED['total'] += int(microstep in group_starts)
            if fetched is None:
                # Every rank skips this microstep together (shared decision in fetch).
                SKIPPED['skipped'] += int(microstep in group_starts)
                skipped.append(dict(microstep=microstep, stream=stream))
                skip_guard(SKIPPED['skipped'], SKIPPED['total'])
                continue
        batch, targets, audit = fetched
        if stream == 'routing':
            batch, audit = own_values(model, rows, batch, audit, (audit or {}).get('index', indices[rank]),
                                      tuple(bool(x) for x in decisions[microstep].tolist()), device)
        batch, targets = move(batch, device), move(targets, device)
        if device.type == 'cuda':
            torch.cuda.synchronize(device)
        if gf1_enabled and step == 1 and screen is None and stream == 'vqa':
            from .gf1 import screen_loss, harm_guard
            loss0, ratio0 = screen_loss(model, batch, targets, stream)
            harm_guard(ratio0, device=device, distributed=distributed)
            screen = (batch, targets, stream, loss0)
        result = model(batch, targets, stream=stream)
        if gf1_enabled:
            from .gf1 import harm_guard
            harm_guard(result.get('metrics', {}).get('gx', {}).get('patch_delta_ratio', 0.),
                       device=device, distributed=distributed)
        phases = dict(after_forward=memory_stats(device))
        if not torch.isfinite(result['loss']):
            raise ValueError('Nonfinite C1 loss')
        (result['loss']/len(plan)).backward()
        phases['after_backward'] = memory_stats(device)
        if rank == 0 and 'gf1' in (getattr(unwrapped, 'geometry_online', None) or {}):
            # The launch guard observes completed microbatches even when world-1
            # accumulation takes longer than its optimizer-step stall budget.
            print(json.dumps({'gf1_progress': dict(step=step, microstep=microstep, stream=stream,
                loss=float(result['loss'].detach()), gx=result.get('metrics', {}).get('gx', {}))}), flush=True)
        if accumulated is not None:
            accumulated.capture()
        peaks.append(torch.cuda.max_memory_allocated(device) if device.type == 'cuda' else 0)
        reserved_peaks.append(torch.cuda.max_memory_reserved(device) if device.type == 'cuda' else 0)
        phase_memory.append(dict(microbatch=len(phase_memory), stream=stream, **phases,
                                 peak_allocated_bytes=peaks[-1], peak_reserved_bytes=reserved_peaks[-1]))
        for key, value in result['components'].items():
            components[key] = components.get(key,0.) + float(value)/len(plan)
        # Per-row mean of the microstep's own stream component (no /len(plan) dilution).
        stream_sums[stream] = stream_sums.get(stream, 0.) + float(result['components'][stream])
        stream_counts[stream] = stream_counts.get(stream, 0) + 1
        for key in routing.Gates.METRICS:
            value = result.get('metrics', {}).get(key)
            if value is not None:
                head_sums[key] += value
                head_counts[key] += 1
        shapes.append(dict(stream=stream, tokens=list(batch['input_ids'].shape),
                           **({k: audit[k] for k in ('substituted_from', 'encode_errors') if k in audit}
                              if isinstance(audit, dict) else {}),
                           **({k: audit[k] for k in ('qid', 'values', 'own_refusal', 'own_skip', 'trained_tokens', 'h1', 'h1_pose')
                               if k in audit} if stream == 'routing' else {}),
                           **({'segments': result['metrics']['segments']}
                              if 'segments' in result.get('metrics', {}) else {}),
                           **({'pose_parts': result['metrics']['pose_parts']}
                              if 'pose_parts' in result.get('metrics', {}) else {}),
                           **({'gx': result['metrics']['gx']} if 'gx' in result.get('metrics', {}) else {}),
                           **({k: audit[k] for k in ('source', 'dataset') if k in audit}
                              if stream == 'pose' and isinstance(audit, dict) else {}),
                           grid=batch['video_grid_thw' if 'video_grid_thw' in batch else 'image_grid_thw'].tolist(),
                           carriers=int((batch['aux_camera_positions']>=0).sum()) if 'aux_camera_positions' in batch else 0))
        if stream == 'pose':
            pose_batch = (batch,targets)
        del result
    if accumulated is not None:
        accumulated.restore()
    reduced = torch.tensor([v for k in routing.Gates.METRICS for v in (head_sums[k], head_counts[k])],
                           dtype=torch.float64, device=device)
    if distributed:
        dist.all_reduce(reduced)
    head_metrics = {k: (float(reduced[2*i] / reduced[2*i+1]) if reduced[2*i+1] > 0 else None)
                    for i, k in enumerate(routing.Gates.METRICS)}
    unwrapped = model.module if distributed else model
    attached = [p for p in unwrapped.auxiliary_heads.parameters() if p.requires_grad]
    if distributed:
        from .fsdp_training import average_adapter_gradients
        average_adapter_gradients(attached, dist.group.WORLD)
    gradients = {g['name']:norm(g['params']) for g in optimizer.param_groups}
    from .trained_groups import observe
    trained_group_gradients = observe(unwrapped)
    branch=unwrapped.auxiliary_heads.pose.head.pose_branch.fc2.weight
    pose_gradient=branch.grad
    head_gradients=dict(rotation_weight_norm=float(pose_gradient[3:7].norm()) if pose_gradient is not None else 0.,
                        fov_weight_norm=float(pose_gradient[7:9].norm()) if pose_gradient is not None else 0.,
                        carrier_embedding_norm=norm([unwrapped.auxiliary_heads.pose.tokens]))
    if not all(np.isfinite(v) and v>0 for v in gradients.values()):
        # Private depth can legitimately be absent from a sampled pose batch.
        # A shared microstep skip can leave a group without a gradient this update.
        if not all(np.isfinite(v) and (v>0 or k in ('encoder_copy', 'geometry_encoder') or skipped)
                   for k,v in gradients.items()):
            raise ValueError('C1 gradient flow failed')
    base = [p for n,p in full_ft.named_trainable(model) if not n.startswith('auxiliary_heads.')]
    carriers, heads = clip_groups(unwrapped, attached)
    clip_norms = {}
    geometry = [p for group in optimizer.param_groups if group['name'] == 'geometry_encoder' for p in group['params']]
    if geometry:
        heads = [p for p in heads if all(p is not q for q in geometry)]
        clip_norms['geometry_encoder'] = float(torch.nn.utils.clip_grad_norm_(
            geometry, unwrapped.geometry_online['finetune']['clip_norm']))
    if distributed:
        if base:
            full_ft.clip_sharded(base,RECIPE['clip_norm'],dist.group.WORLD)
        if carriers:
            # Final mode: carrier/frame embeddings clip apart from the heads (eps-scale tokens).
            clip_norms['carriers'] = float(torch.nn.utils.clip_grad_norm_(carriers,RECIPE['clip_norm']))
        clip_norms['heads'] = float(torch.nn.utils.clip_grad_norm_(heads,RECIPE['clip_norm']))
    elif getattr(unwrapped, 'geometry_online', None):
        torch.nn.utils.clip_grad_norm_(base, RECIPE['clip_norm'])
        clip_norms['heads'] = float(torch.nn.utils.clip_grad_norm_(heads, RECIPE['clip_norm']))
    elif carriers:
        clip_norms['carriers'] = float(torch.nn.utils.clip_grad_norm_(carriers,RECIPE['clip_norm']))
        rest = [p for p in model.parameters() if p.requires_grad and all(p is not c for c in carriers)]
        clip_norms['rest'] = float(torch.nn.utils.clip_grad_norm_(rest,RECIPE['clip_norm']))
    else:
        torch.nn.utils.clip_grad_norm_(model.parameters(),RECIPE['clip_norm'])
    head_gradients['clip_group_norms'] = clip_norms
    for group in optimizer.param_groups:
        group['lr'] = learning_rate(step, {**recipe,'learning_rate':group['initial_lr']})
        if group['name'] == 'geometry_encoder':
            from .g3t_online import learning_rate_ramp
            group['lr'] *= learning_rate_ramp(unwrapped.geometry_online, step)
        fusion = (getattr(unwrapped, 'geometry_online', None) or {}).get('patch_fusion')
        if fusion is not None and step <= fusion['align_steps'] and not group.get('gx_alignment', False):
            group['lr'] = 0.
    if gf1_enabled and step == 1 and screen is None:
        raise ValueError('GF1 first update requires a fixed VQA row for the harm screen')
    optimizer.step()
    if screen is not None:
        from .gf1 import screen_loss, harm_guard
        screen_batch, screen_targets, screen_stream, loss0 = screen
        loss1, ratio1 = screen_loss(model, screen_batch, screen_targets, screen_stream)
        harm_guard(ratio1, loss0, loss1, device=device, distributed=distributed)
        screen_metrics = dict(step0_loss=loss0, step1_loss=loss1, patch_delta_ratio=ratio1,
                              scope='same encoded VQA row before/after first optimizer update per rank')
    after_optimizer = memory_stats(device)
    if device.type == 'cuda':
        torch.cuda.synchronize(device)
    h1_metrics = {}
    if any(s.get('h1') for s in shapes):
        from .h1 import summarize
        h1_metrics = {'h1': summarize(shapes)}
    if getattr(rows, 'h1', {}).get('faithful_own_camera_rows'):
        from .h1 import global_answer_counts
        h1_metrics['h1_answer_counts'] = global_answer_counts(shapes, device, distributed)
    return dict(step=step, **h1_metrics, **({'gf1_harm_screen': screen_metrics} if gf1_enabled else {}), wall_seconds=time.perf_counter()-started, data_seconds=waiting,
                skipped_microsteps=skipped, skip_totals=dict(SKIPPED),
                component_normalization='components: sum over microsteps of each row-mean loss / len(plan); '
                                        'stream_means: row-mean loss of each stream over its own microsteps',
                stream_means={k: stream_sums[k]/stream_counts[k] for k in stream_sums},
                components=components, head_metrics=head_metrics,
                gates=None if gates is None else dict(gates.state(step), decisions=decisions.tolist()), gradient_norms=gradients,
                trained_group_gradients=trained_group_gradients, head_gradients=head_gradients, shapes=shapes,
                rank=rank, cpu_offload=offload, memory=dict(microbatches=phase_memory, after_optimizer_step=after_optimizer),
                peak_allocated_bytes=max(peaks + [torch.cuda.max_memory_allocated(device) if device.type=='cuda' else 0]),
                peak_reserved_bytes=max(reserved_peaks + [torch.cuda.max_memory_reserved(device) if device.type=='cuda' else 0])), pose_batch


def dryrun(cfg, report_path):
    start = time.perf_counter()
    receipt, manifest = prepared(cfg, admission=True)
    auth_seconds = time.perf_counter()-start
    processor = processor_for_receipt(manifest, receipt)
    start = time.perf_counter(); model = load_model(manifest,receipt,processor).cpu().train()
    load_seconds = time.perf_counter()-start
    optimizer = torch.optim.AdamW(parameter_groups(model, **gx_recipe(model)),weight_decay=RECIPE['weight_decay'])
    rows = Rows(receipt,processor)
    counts = {k:v['count'] for k,v in receipt['streams'].items()}
    recipe = recipe_for(cfg)
    offset = cfg.get('row_start_step', 0)
    plan = next(data.mixed_indices(counts,offset+1,start_step=offset,training_mode=cfg.get('training_mode', 'mixed'),
                                   mix=recipe['mix'],world=recipe['world_size'],type_mix=getattr(rows, 'type_mix', None)))
    rank_shapes = []
    try:
        # Encode each rank's actual first row in every stream; no synthetic admission.
        for rank in range(recipe['world_size']):
            for stream, indices in plan:
                batch, _, _ = rows.get(stream,indices[rank])
                rank_shapes.append(dict(rank=rank,stream=stream,tokens=list(batch['input_ids'].shape)))
        frozen_before = {n: p.detach().clone() for n,p in model.model.visual.named_parameters()}
        representative = {g['name']: g['params'][0].detach().clone() for g in optimizer.param_groups}
        step, pose_batch = optimize_step(model,optimizer,rows,plan,0,torch.device('cpu'),1)
        checks = dict(frozen_base_vision=all(torch.equal(p,frozen_before[n]) for n,p in model.model.visual.named_parameters()),
                      lm_update=not torch.equal(optimizer.param_groups[0]['params'][0],representative['llm']),
                      finite_gradients=all(np.isfinite(x) for x in step['gradient_norms'].values()))
        report = dict(schema='c1-dryrun-v1',status='PASS' if all(checks.values()) else 'FAIL',
                      checks=checks,step=step,rank_shapes=rank_shapes,head_probe=model.eval().probe(*pose_batch),
                      authentication_seconds=auth_seconds,model_load_seconds=load_seconds,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                      dtype='CPU LM FP32; private V-C BF16; heads FP32',gpu_fit_measured=False)
        write(report_path,report)
        if report['status'] != 'PASS':
            raise ValueError('C1 CPU dryrun failed')
        return report
    finally:
        rows.close()


def gx_rule_rebind(old, bound, cfg, old_cfg):
    """Authenticate a GX rule transition or an otherwise identical code transition."""
    if (set(old) != EXPORT_BINDING_KEYS or set(bound) != EXPORT_BINDING_KEYS
            or any(old[k] != bound[k] for k in ('preparation', 'world_size'))
            or not cfg or not old_cfg or not cfg.get('geometry_online')
            or not old_cfg.get('geometry_online') or identity(cfg) != bound['config_sha256']
            or identity(old_cfg) != old['config_sha256']):
        raise ValueError('GX resume differs outside fail_fast')
    from .g3t_online import normalize
    old_geometry = copy.deepcopy(old_cfg['geometry_online'])
    old_fail = old_geometry.get('fail_fast')
    legacy_reference = isinstance(old_fail, dict) and 'reference' in old_fail and 'reference_binding' not in old_fail
    if legacy_reference:
        # This config is historical evidence authenticated above, never launch input.
        reference = old_fail.pop('reference')
        if not isinstance(reference, str) or not Path(reference).is_absolute():
            raise ValueError('GX previous reference must be an absolute output path')
    normalized = normalize(old_geometry)
    if legacy_reference:
        normalized['fail_fast']['reference'] = reference
    if normalized != old_cfg['geometry_online']:
        raise ValueError('GX previous configuration is not normalized')
    previous = copy.deepcopy(cfg)
    if 'fail_fast' in old_cfg['geometry_online']:
        previous['geometry_online']['fail_fast'] = old_cfg['geometry_online']['fail_fast']
    else:
        previous['geometry_online'].pop('fail_fast', None)
    rule_changed = cfg['geometry_online'].get('fail_fast') != old_cfg['geometry_online'].get('fail_fast')
    code_changed = cfg.get('code') != old_cfg.get('code')
    if code_changed:
        if old['trainer_commit'] == bound['trainer_commit']:
            raise ValueError('GX code transition requires a trainer_commit transition')
        if 'code' not in cfg or 'code' not in old_cfg:
            raise ValueError('GX code transition requires both code pins')
        previous['code'] = old_cfg['code']
    elif not rule_changed and old['trainer_commit'] != bound['trainer_commit']:
        raise ValueError('GX code-only transition requires changed code pins')
    if identity(previous) != old['config_sha256']:
        raise ValueError('GX resume differs outside fail_fast')
    return 'gx-code-rebind-v1' if code_changed and not rule_changed else 'gx-rule-rebind-v1'


def output_bindings(output):
    """Follow immutable rebind receipts from the untouched original binding."""
    output = Path(output)
    path = output/'binding.json'
    chain = [(load(path), path)]
    pending = [(p, load(p)) for p in output.glob('binding_rebind_*.json')]
    while pending:
        previous = file_pin(chain[-1][1])
        children = [(p, r) for p, r in pending if r.get('previous') == previous]
        if len(children) != 1:
            raise ValueError('GX output has a forked or disconnected binding history')
        path, record = children[0]
        kind = gx_rule_rebind(chain[-1][0], record['binding'], record['config'], record['previous_config'])
        if record.get('schema') != kind:
            raise ValueError('Invalid GX rebind record')
        if record['config'].get('code') != record['previous_config'].get('code') and (
                record.get('previous_code') != record['previous_config'].get('code') or
                record.get('code') != record['config'].get('code')):
            raise ValueError('GX rebind code pins differ')
        if kind == 'gx-code-rebind-v1' and (
                record.get('previous_trainer_commit') != chain[-1][0]['trainer_commit'] or
                record.get('trainer_commit') != record['binding']['trainer_commit']):
            raise ValueError('GX rebind trainer commits differ')
        chain.append((record['binding'], path))
        pending = [(p, r) for p, r in pending if p != path]
    return chain


def stored_config(output, bound, manifest=None):
    """Recover a hash-authenticated config from a checkpoint, snapshot, or legacy receipt."""
    def candidates():
        if manifest:
            yield manifest
        snapshot = Path(output)/f'binding_config_{digest(bound)}.json'
        if snapshot.exists():
            yield load(snapshot)
        # Legacy receipts must name the exact binding and authenticate the full config.
        for pattern in ('attempt_*.json', 'run_*.json', 'binding_rebind_*.json'):
            for path in sorted(Path(output).glob(pattern)):
                yield load(path)
    for receipt in candidates():
        if not isinstance(receipt, dict) or receipt.get('binding') != bound:
            continue
        cfg = receipt.get('config')
        if isinstance(cfg, dict) and identity(cfg) == bound.get('config_sha256'):
            return cfg
    raise ValueError('GX resume needs a hash-authenticated previous config')


def complete_states(output, bound):
    """Find this run's complete states without reading the large shard payloads.

    Restoration still authenticates every payload hash. Partial markers, absent
    or truncated files, foreign bindings and symlinked directories are ignored.
    """
    output = Path(output)
    if bound not in [b for b, _ in output_bindings(output)]:
        raise ValueError('Resume output belongs to another run')
    states = []
    for directory in output.glob('checkpoint_*'):
        if (not re.fullmatch(r'checkpoint_\d{6}(?:_[0-9a-f]{32})?', directory.name)
                or directory.is_symlink() or not directory.is_dir()):
            continue
        marker = directory/'complete.json'
        try:
            manifest = load(marker)
            files = manifest['files']
            world = len(manifest['layouts'])
            required = {f'shards/rank{rank:03d}.pt' for rank in range(world)}
            required.update(f'rng{rank:03d}.pt' for rank in range(world))
            if (marker.is_symlink() or manifest['schema'] != 'c1-checkpoint-v1'
                    or manifest['binding'] != bound or world < 1
                    or manifest['step'] != int(directory.name.split('_')[1])
                    or not required <= files.keys()
                    or not files.keys() <= required | {full_ft.REPLICATED_FILE}):
                continue
            if any(Path(name).is_absolute() or '..' in Path(name).parts
                   or (directory/name).resolve().parent not in (directory.resolve(), (directory/'shards').resolve())
                   or (directory/name).is_symlink() or not (directory/name).is_file()
                   or (directory/name).stat().st_size != pin['bytes'] for name, pin in files.items()):
                continue
            # Archive only the exact state tree, never extra artifacts.
            entries = list(directory.rglob('*'))
            actual = {str(p.relative_to(directory)) for p in entries if not p.is_dir()}
            folders = {str(p.relative_to(directory)) for p in entries if p.is_dir()}
            if (actual != set(files) | {'complete.json'} or folders != {'shards'}
                    or any(p.is_symlink() for p in entries)):
                continue
            states.append((marker.stat().st_mtime_ns, manifest['step'], marker))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return [entry[2] for entry in sorted(states)]


def bind_output(output, bound, *, resume=False, cfg=None, resume_pin=None):
    """Reuse an identical early-crash binding only before any complete state."""
    output = Path(output)
    if cfg and cfg.get('geometry_online') and identity(cfg) != bound['config_sha256']:
        raise ValueError('GX binding config identity differs')
    binding = output/'binding.json'
    rebind = None
    if resume or binding.exists():
        previous, previous_path = output_bindings(output)[-1]
        if previous != bound:
            if not resume or not cfg or not cfg.get('geometry_online') or not resume_pin:
                raise ValueError('Resume output belongs to another run')
            resume_manifest = load(pinned(resume_pin))
            old_cfg = stored_config(output, previous, resume_manifest)
            kind = gx_rule_rebind(previous, bound, cfg, old_cfg)
            # Recheck the selected state under the run lock before publishing a new binding.
            gx_rule_rebind(resume_manifest['binding'], bound, cfg,
                           stored_config(output, resume_manifest['binding'], resume_manifest))
            if Path(resume_pin['path']) not in complete_states(output, resume_manifest['binding']):
                raise ValueError('GX rebind needs a complete state in this output')
            record = dict(schema=kind, previous=file_pin(previous_path),
                          binding=bound, config=cfg, previous_config=old_cfg, resume=resume_pin)
            if cfg.get('code') != old_cfg.get('code'):
                record.update(previous_code=old_cfg['code'], code=cfg['code'])
            if kind == 'gx-code-rebind-v1':
                record.update(previous_trainer_commit=previous['trainer_commit'],
                              trainer_commit=bound['trainer_commit'])
            path = output/f'binding_rebind_{uuid.uuid4().hex}.json'
            write(path, record)
            rebind = file_pin(path)
        if not resume and complete_states(output, bound):
            raise ValueError('Complete C1 resume state exists; resume instead of starting fresh')
    else:
        write(binding, bound)
    if cfg and cfg.get('geometry_online'):
        snapshot = output/f'binding_config_{digest(bound)}.json'
        if not snapshot.exists():
            write(snapshot, dict(binding=bound, config=cfg))
    return rebind


def latest_resume(output, bound, *, cfg=None):
    bindings = output_bindings(output)
    states = complete_states(output, bound) if bound in [b for b, _ in bindings] else []
    if not states and cfg and cfg.get('geometry_online'):
        candidates = []
        for old, _ in bindings:
            for marker in complete_states(output, old):
                manifest = load(marker)
                try:
                    gx_rule_rebind(old, bound, cfg, stored_config(output, old, manifest))
                except ValueError:
                    continue
                candidates.append(marker)
        states = sorted(candidates, key=lambda p: (p.stat().st_mtime_ns, load(p)['step']))
    if not states:
        raise ValueError('No complete C1 resume state')
    return file_pin(states[-1])


def checkpoint(directory, model, optimizer, bound, step, *, rotate=False, gx_history=None, disk_guard=None):
    """Immutable rank-sharded state; complete.json is written last, after a barrier."""
    from .trace_version import metadata
    version_metadata=metadata({'trace_program_version':getattr(model,'trace_program_version',None)})
    rank, world = dist.get_rank(),dist.get_world_size()
    directory = Path(directory)
    named = full_ft.named_trainable(model)
    buffers = full_ft.named_buffers(model)
    from .checkpoint_space import Budget, check as check_space
    export_named = [(full_ft.clean_name(name), value) for name, value in model.named_parameters()]
    space = check_space(directory.parent, named, optimizer, buffers, rank, world, disk_guard, export_named=export_named)
    if rotate:
        # A retry at the same step must leave an interrupted save untouched.
        names = [str(directory.with_name(f'checkpoint_{step:06d}_{uuid.uuid4().hex}')) if rank == 0 else None]
        dist.broadcast_object_list(names, src=0)
        directory = Path(names[0])
        if rank == 0 and output_bindings(directory.parent)[-1][0] != bound:
            raise ValueError('Resume output belongs to another run')
    if rank==0:
        directory.mkdir(parents=True,exist_ok=False)
    dist.barrier()
    layout = digest(full_ft.shard_layout(named))
    pins = full_ft.write_rank_shard(directory,rank,named,optimizer,layout,buffers=buffers)
    rng=rng_state()
    # weights_only checkpoints store NumPy's MT19937 array as a tensor.
    numpy_state=rng['numpy']
    rng['numpy']=(numpy_state[0],torch.from_numpy(numpy_state[1].astype(np.int64)),*numpy_state[2:])
    rng_pin = full_ft._write_payload(directory/f'rng{rank:03d}.pt',rng)
    payload = dict(rank=rank,layout=layout,pins=pins,rng=rng_pin)
    gathered = [None]*world; dist.all_gather_object(gathered,payload)
    dist.barrier()  # Every rank has finished and fsynced its payloads.
    space['serialized_state_bytes'] = sum(entry['rng']['bytes']+
        sum(pin['bytes'] for pin in entry['pins'].values()) for entry in gathered)
    if space['serialized_state_bytes'] > space['state_bytes']:
        raise ValueError('Checkpoint payload exceeds its measured disk budget; no complete state is published')
    if rank==0:
        files = {}
        for entry in gathered:
            for pin in entry['pins'].values():
                files[pin['name']] = {k:v for k,v in pin.items() if k!='name'}
            files[f"rng{entry['rank']:03d}.pt"] = entry['rng']
        # Persist directory entries as well as the already-fsynced payloads.
        for folder in (directory/'shards', directory):
            descriptor = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        extra = dict(version_metadata, buffer_state_version=1, disk_guard=space)
        if hasattr(model, 'trained_group_state'):
            extra['trained_group_state'] = model.trained_group_state
        if getattr(model, 'training_mode', None) == 'final' and getattr(model, 'geometry_online', None):
            extra['geometry_encoder'] = model.geometry_online['encoder']
        if getattr(model, 'geometry_online', None) and 'encoder_dtype' in model.geometry_online:
            extra['geometry_encoder_dtype'] = model.geometry_online['encoder_dtype']
        if gx_history is not None:
            gx_validate_history(gx_history, step)
            extra['gx_history'] = gx_history
            extra['gx_attempt'] = rehearsal.attempt_id() if rehearsal.enabled() else os.environ.get('SLURM_JOB_ID', 'cpu')
        if 'config_sha256' in bound:
            snapshot = directory.parent/f'binding_config_{digest(bound)}.json'
            if snapshot.exists():
                extra['config'] = stored_config(directory.parent, bound)
        write(directory/'complete.json',dict(schema='c1-checkpoint-v1',binding=bound,step=step,
                                             layouts=[g['layout'] for g in gathered],files=files, **extra))
        with (directory/'complete.json').open('rb') as handle:
            os.fsync(handle.fileno())
        for folder in (directory, directory.parent):
            descriptor = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        if rotate:
            states = complete_states(directory.parent, bound)
            if directory/'complete.json' not in states:
                raise ValueError('New C1 resume state is incomplete; retaining older states')
            # Preserve superseded states without deleting their payloads.
            for marker in states[:-2]:
                archive = directory.parent/'_superseded'
                archive.mkdir(exist_ok=True)
                marker.parent.rename(archive/marker.parent.name)
    dist.barrier()
    if isinstance(disk_guard, Budget):
        disk_guard.complete('checkpoint')
    return file_pin(directory/'complete.json')


def restore(pin, model, optimizer, bound, *, cfg=None):
    manifest = load(pinned(pin)); directory = Path(pin['path']).parent
    from .trace_version import bind
    requested = (cfg or {}).get('trace_program_version',getattr(model,'trace_program_version',None))
    bind(model,manifest,{'trace_program_version':requested})
    if manifest.get('schema')!='c1-checkpoint-v1':
        raise ValueError('C1 resume binding differs')
    if manifest.get('buffer_state_version', 1) != 1:
        raise ValueError('C1 resume buffer-state version differs')
    from .trained_groups import restore as restore_groups
    restore_groups(model, manifest.get('trained_group_state'))
    geometry = getattr(model, 'geometry_online', None) or {}
    if manifest.get('geometry_encoder_dtype', 'fp32') != geometry.get('encoder_dtype', 'fp32'):
        raise ValueError('C1 resume geometry encoder dtype differs')
    if getattr(model, 'training_mode', None) == 'final' and getattr(model, 'geometry_online', None):
        if manifest.get('geometry_encoder') != model.geometry_online['encoder']:
            raise ValueError('C1 resume geometry encoder pins differ')
    if manifest['binding'] != bound:
        if not cfg or not cfg.get('geometry_online'):
            raise ValueError('C1 resume binding differs')
        if Path(cfg['output']).resolve() != directory.parent.resolve():
            raise ValueError('GX rule-only resume must use the same output')
        gx_rule_rebind(manifest['binding'], bound, cfg, stored_config(directory.parent, manifest['binding'], manifest))
        if Path(pin['path']) not in complete_states(directory.parent, manifest['binding']):
            raise ValueError('GX resume state is outside its output or incomplete')
    rank = dist.get_rank()
    named=full_ft.named_trainable(model); layout=digest(full_ft.shard_layout(named))
    if layout!=manifest['layouts'][rank]:
        raise ValueError('C1 resume shard layout differs')
    full_ft.read_rank_shard(directory,rank,manifest['files'],named,optimizer,layout,dist.group.WORLD,
                           buffers=full_ft.named_buffers(model))
    rng=full_ft._verified_load(directory/f'rng{rank:03d}.pt',manifest['files'][f'rng{rank:03d}.pt'],'RNG')
    numpy_state=rng['numpy']
    rng['numpy']=(numpy_state[0],numpy_state[1].numpy().astype(np.uint32),*numpy_state[2:])
    restore_rng(rng)
    return manifest['step']


def export(directory, wrapped, model, cfg, step, *, optimizer=None, disk_guard=None):
    from .trace_version import metadata, model_version
    version_metadata=metadata(cfg)
    model_version(model,cfg['trace_program_version'])
    from .checkpoint_space import Budget, check as check_space
    budget = Budget(cfg.get('checkpoint_disk_guard')) if disk_guard is None else disk_guard
    export_named = [(full_ft.clean_name(name), value) for name, value in wrapped.named_parameters()]
    check_space(Path(directory).parent, full_ft.named_trainable(wrapped), optimizer, full_ft.named_buffers(wrapped),
                dist.get_rank(), dist.get_world_size(), budget, export_named=export_named, kind='export')
    if 'mdg' in cfg:
        from .stageb_mdg import calibrate
        tau, tau_info = ((model.mdg_tau, model.mdg_tau_info) if model.mdg_tau is not None
                         else calibrate(wrapped, model))
    from .fsdp_training import publication_state
    state = publication_state(wrapped)
    if dist.get_rank()==0:
        from .ground_tokens import materialize_export_rows
        state = materialize_export_rows(state, model)
        directory=Path(directory); directory.mkdir(parents=True,exist_ok=False)
        names=[full_ft.clean_name(n) for n,_ in full_ft.base_parameters(model)]
        weights = full_ft.save_export(full_ft.export_tensors(state,names),directory/'full_weights',
                                     {'base_identity':cfg['base_identity']},model.full_ft_report)
        heads = {n.removeprefix('auxiliary_heads.'):v for n,v in state.items() if n.startswith('auxiliary_heads.')}
        if model.training_mode == 'final' and getattr(model, 'geometry_online', None):
            # The frozen encoder reloads from its authenticated source, never
            # from a student checkpoint. Bind that source inside heads.pt too.
            heads = {k: v for k, v in heads.items() if not k.startswith('geometry_encoder.')}
            heads['_gx_geometry_online'] = model.geometry_online
        pin=full_ft._write_payload(directory/'heads.pt',heads)
        mdg_meta = {}
        if 'mdg' in cfg:
            from dataclasses import asdict
            mdg_meta = dict(mdg=dict(config=asdict(model.auxiliary_heads.mdg.cfg), tau=float(tau),
                                     calibration=tau_info))
            if hasattr(model, 'mdg_lora_config'):
                mdg_meta['mdg']['lora_config'] = model.mdg_lora_config
        from .trained_groups import publish
        contract = publish(model, state, step)
        from .source_seal import binding
        sealed = binding(load(pinned(cfg['code'])), identity(cfg)) if cfg.get('code') else None
        training_seal = load(pinned(cfg['preparation'])).get('source_seal') if sealed is not None else None
        write(directory/'artifact.json',dict(**version_metadata,schema='carrier-c1-artifact-v1',step=step,
            **(dict(trained_groups=contract) if contract is not None else {}),
            **(dict(source_seal=sealed, training_source_seal=training_seal) if sealed is not None else {}),
            config_sha256=identity(cfg),base_identity=cfg['base_identity'],
            anchors=list(range(1,33)),
            placement=model.carrier_placement, training_mode=model.training_mode, pose_backing='lm_final_norm',
            frame_layout=model.frame_layout, **mdg_meta,
            carrier_position_policy=model.carrier_position_policy,
            depth_backing='private_vit' if hasattr(model.auxiliary_heads, 'depth') else None,
            **(dict(geometry_online=model.geometry_online,
                    gx=dict(rms_cam=float(model.auxiliary_heads.pose.cam_token_connector.rms_cam.item()),
                            mode=model.geometry_online['mode'])) if getattr(model, 'geometry_online', None) else {}),
            full_weights=file_pin(directory/'full_weights/full_weights.json'),
            heads={'path':str((directory/'heads.pt').resolve()),'sha256':pin['sha256']}))
        if 'mdg' in cfg:
            from .stageb_mdg import export as export_mdg
            export_mdg(directory, model, state, cfg, step, tau, tau_info)
    dist.barrier()
    if isinstance(budget, Budget):
        budget.complete('export')


def existing_export(directory, cfg, step):
    """A timed resume may replay an already exported step; preserve that artifact."""
    directory = Path(directory)
    if not directory.exists():
        return False
    artifact = load(directory/'artifact.json')  # Incomplete exports fail closed.
    accepted = {identity(cfg)}
    if cfg.get('geometry_online') and artifact.get('config_sha256') not in accepted:
        output = Path(cfg['output'])
        if directory.resolve().parent != output.resolve():
            raise ValueError('Existing milestone is outside the GX output')
        chain = output_bindings(output)
        if chain[-1][0]['config_sha256'] != identity(cfg):
            raise ValueError('Existing milestone lacks the current GX binding')
        accepted.update(b['config_sha256'] for b, _ in chain)
    if (artifact.get('schema') != 'carrier-c1-artifact-v1' or artifact.get('step') != step
            or artifact.get('config_sha256') not in accepted):
        raise ValueError('Existing milestone belongs to another C1 run or step')
    # Authenticate the small manifest and heads; do not reread all LM weights.
    for name in ('full_weights', 'heads'):
        path = pinned(artifact[name])
        if not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError('Existing milestone payload is outside its directory')
    if 'mdg' in cfg:
        from .mask_grounding_head import load_artifact as load_mdg
        _, meta = load_mdg(directory/'mdg')
        if meta['base_artifact'] != file_pin(directory/'artifact.json'):
            raise ValueError('MDG milestone base artifact differs')
    return True


def validation_read(model, rows, rank, device, step, output, distributed):
    """Read the held-out pose monitor with identical forwards on every rank."""
    n = rows.validation_count() if hasattr(rows, 'validation_count') else 0
    if not n:
        return None
    from .all_frame_readout import pose_metrics
    output = Path(output)
    path = output/f'validation_m{step}.json'
    previous = None
    if rank == 0:
        try:
            previous = load(path) if path.is_file() else None
        except Exception:
            previous = None
        if not isinstance(previous, dict) or previous.get('schema') != 'cp1-pose-validation-v1':
            previous = None
    exists = [previous is not None if rank == 0 else None]
    if distributed:
        dist.broadcast_object_list(exists, src=0)
    if exists[0]:
        if rank != 0:
            return dict(step=step, reused=True)
        try:
            update_best(output, step, previous.get('slice_pose_loss'))
        except Exception as exc:
            print(json.dumps({'warning': f'best pose pointer not updated at step {step}: {type(exc).__name__}: {exc}'[:400]}), flush=True)
        return {**previous, 'reused': True}
    world = dist.get_world_size() if distributed else 1
    records, scalars, skips = [], [], 0
    training = model.training
    try:
        model.eval()
        with torch.no_grad():
            for offset in range((n + world - 1)//world):
                index = rank + offset*world
                try:
                    batch, targets, audit = rows.validation_get(index % n)
                    check_row(batch, targets, 'pose', model)
                    batch, targets = move(batch, device), move(targets, device)
                    ok = 1
                except Exception:
                    ok = 0
                flag = torch.tensor([ok], dtype=torch.int32, device=device)
                if distributed:
                    dist.all_reduce(flag, op=dist.ReduceOp.MIN)
                if not flag.item():
                    skips += 1
                    continue
                result = model(batch, targets, stream='pose')
                prediction = model(batch, None, stream='readout')
                if index >= n:
                    continue
                values = dict(pose=float(result['components']['pose']))
                values.update({k: float(result['metrics'][k]) for k in ('rotation_deg', 'fov_deg', 'depth_absrel')
                               if result['metrics'].get(k) is not None})
                values['pose_parts'] = {k: float(v) for k, v in result['metrics'].get('pose_parts', {}).items()}
                scalars.append(values)
                camera = lambda key: targets[key][0].detach().cpu().tolist()
                records.append(dict(dataset=audit['dataset'], scene=audit['scene'],
                    gt=dict(camera=camera('aux_camera_target'), camera_mask=camera('aux_camera_mask'),
                            gravity=camera('aux_gravity_target')),
                    pred=dict(camera=prediction['pose'][0].detach().cpu().tolist(),
                              gravity=None if prediction['gravity'] is None else prediction['gravity'][0].detach().cpu().tolist())))
    finally:
        model.train(training)
    gathered = [None]*world
    if distributed:
        dist.all_gather_object(gathered, dict(records=records, scalars=scalars, skips=skips))
    else:
        gathered[0] = dict(records=records, scalars=scalars, skips=skips)
    if rank != 0:
        return dict(step=step, n=len(records), skips=skips)
    records = [r for part in gathered for r in part['records']]
    scalars = [v for part in gathered for v in part['scalars']]
    try:
        return validation_summary(records, scalars, skips, step, output, path, pose_metrics)
    except Exception as exc:
        print(json.dumps({'warning': f'validation read at step {step} not recorded: {type(exc).__name__}: {exc}'[:400]}), flush=True)
        return dict(step=step, n=len(records), skips=skips, error=f'{type(exc).__name__}: {exc}'[:400])


def validation_summary(records, scalars, skips, step, output, path, pose_metrics):
    mean = lambda values: sum(values)/len(values) if values else None
    summary = dict(schema='cp1-pose-validation-v1', step=step, n=len(records),
                   scenes=len({(r['dataset'], r['scene']) for r in records}), skips=skips,
                   slice_pose_loss=mean([v['pose'] for v in scalars]),
                   pose_parts={k: mean([v['pose_parts'][k] for v in scalars if k in v['pose_parts']])
                               for k in sorted({k for v in scalars for k in v['pose_parts']})},
                   pose_metrics=pose_metrics(records, range(32), gravity=True))
    summary.update({k: mean([v[k] for v in scalars if k in v])
                    for k in ('rotation_deg', 'fov_deg', 'depth_absrel')})
    update_best(output, step, summary['slice_pose_loss'])
    replace_json(path, summary)
    return summary


def replace_json(path, value):
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}')
    write(temporary, value)
    os.replace(temporary, path)


def update_best(output, step, value):
    """Point best_pose.json at the milestone with the lowest slice pose loss (ties keep the earlier step)."""
    best_path = output/'best_pose.json'
    try:
        best = load(best_path) if best_path.is_file() else None
    except Exception:
        best = None
    if not (isinstance(best, dict) and type(best.get('step')) is int and isinstance(best.get('value'), (int, float))
            and isinstance(best.get('history'), list)):
        best = None
    if value is None or (best is not None and (value >= best['value'] or step == best['step'])):
        return best
    best = dict(schema='cp1-best-pose-v1', step=step, criterion='slice_pose_loss', value=value,
                artifact=file_pin(output/f'm{step}'/'artifact.json'),
                history=(best['history'] if best else []) + [dict(step=step, value=value)])
    replace_json(best_path, best)
    return best


def step400_gate_enabled(cfg):
    """Final GX shares CP1's gate; pose-only GX has its own stopping rules."""
    return cfg.get('gate_stop', True) and not (
        cfg.get('training_mode') == 'pose_only' and cfg.get('geometry_online'))


def run_steps(model, wrapped, optimizer, rows, counts, output, cfg, bound, device,
              rank=0, start_step=0, smoke_steps=None, started=None, stop=None, distributed=True,
              resume_history=None):
    """Shared native loop; CPU smoke exercises it without CUDA or collectives."""
    started=time.monotonic() if started is None else started
    stop=[False] if stop is None else stop
    world=dist.get_world_size() if distributed else 1
    recipe = recipe_for(cfg)
    from .s1_first_step import POLICY, report as first_step_report
    if cfg.get('first_step_admission') not in (None, POLICY):
        raise ValueError('Unknown first-step admission policy')
    steps=start_step+(smoke_steps or (recipe['steps']-start_step))
    if start_step>=steps:
        raise ValueError('Completed C1 schedules cannot resume')
    timing = cfg.get('schedule', {})
    if not smoke_steps and cfg.get('training_mode') == 'pose_only':
        steps = start_step + capped_steps(timing, recipe['resume_every_seconds'], start_step=start_step,
                                         elapsed_seconds=time.monotonic()-started,
                                         total_steps=recipe['steps'], milestones=recipe['milestones'])
    # Training step s reads the sampler's plan step row_start_step + s (a warm start continues its donor's order).
    offset = cfg.get('row_start_step', 0)
    output=Path(output);attempt=rehearsal.attempt_id() if rehearsal.enabled() else os.environ.get('SLURM_JOB_ID','cpu')
    measured=[]; step=start_step; gate_stop=False; gx_stop=False; h1_stop=False
    gx_history = []
    if cfg.get('geometry_online'):
        gx_history = copy.deepcopy(resume_history) if resume_history is not None else gx_step_history(output, start_step)
        gx_validate_history(gx_history, start_step)
        gx_reference(cfg, 0)
    from .checkpoint_space import Budget
    disk_budget = Budget(cfg.get('checkpoint_disk_guard'))
    checkpoint_options = lambda: dict(disk_guard=disk_budget,
                                     **(dict(gx_history=gx_history) if cfg.get('geometry_online') else {}))
    if start_step == 0 and 0 in recipe['milestones'] and not smoke_steps:
        reused = [existing_export(output/'m0', cfg, 0) if rank == 0 else None]
        if distributed:
            dist.broadcast_object_list(reused, src=0)
        if not reused[0]:
            export(output/'m0', wrapped, model, cfg, 0, optimizer=optimizer, disk_guard=disk_budget)
    h1_reason='h1_stop_after_step'
    h1_state=None;answer_stop=None
    if cfg.get('h1', {}).get('faithful_own_camera_rows'):
        from .h1 import AnswerStop, STOP_RULE
        answer_stop=AnswerStop()
        states=[None]
        if rank==0:
            try:
                h1_state=answer_stop.replay(output,start_step)
                states[0]=dict(state=h1_state,differs=answer_stop.differs,own=answer_stop.own)
            except (ValueError,KeyError) as exc:states[0]=dict(error=str(exc))
        if distributed:dist.broadcast_object_list(states,src=0)
        if 'error' in states[0]:raise ValueError(states[0]['error'])
        h1_state=states[0]['state'];answer_stop.differs=states[0]['differs']
        answer_stop.own=states[0]['own'];answer_stop.last_step=start_step
    h1_limit = cfg.get('h1', {}).get('stop_after_step')
    if h1_state and h1_state['triggered']:
        h1_limit=min(h1_limit or 100,100);h1_reason=STOP_RULE
    if not smoke_steps and h1_limit is not None and start_step >= h1_limit:
        if start_step != h1_limit:
            raise ValueError('H1 checkpoint is past stop_after_step')
        reused = [existing_export(output/f'm{start_step}', cfg, start_step) if rank == 0 else None]
        if distributed:
            dist.broadcast_object_list(reused, src=0)
        if not reused[0]:
            export(output/f'm{start_step}', wrapped, model, cfg, start_step,
                   optimizer=optimizer, disk_guard=disk_budget)
        report = dict(schema='c1-run-v1', status='H1_STOP', first_step=None, last_step=start_step,
                      steps=[], elapsed_seconds=time.monotonic()-started, stopped_for_resume=False,
                      world_size=world, gpu_fit_measured=False, stop_reason=h1_reason)
        if rank == 0:
            record=dict(schema='h1-stop-v1', step=start_step, lr_horizon=recipe['steps'],
                        milestone=str(output/f'm{start_step}'), reason=h1_reason, stop_state=h1_state)
            path=output/f'h1_stop_{start_step:06d}.json'
            if path.exists():
                if load(path)!=record:raise ValueError('Existing H1 stop record differs')
            else:write(path,record)
            path=output/f'run_{attempt}_h1_stopped_resume.json'
            if not path.exists():write(path,report)
        return report
    gates=None
    if recipe.get('scheduled_sampling'):
        gates=routing.Gates(recipe['scheduled_sampling'],getattr(model,'depth_stage1',False))
        state=[replay_gates(cfg['output'],start_step,gates).ema if rank==0 else None]
        if distributed:
            dist.broadcast_object_list(state,src=0)
        gates.ema=dict(state[0])
    last_save=time.monotonic()
    request=torch.tensor([int(stop[0] or (output/('stop.'+os.environ.get('SLURM_JOB_ID','local')+'.request')).exists() or steps==start_step)],device=device)
    if distributed:
        # Startup durations can differ. All ranks must use the shortest budget.
        end=torch.tensor([steps],device=device)
        dist.all_reduce(end,op=dist.ReduceOp.MIN)
        steps=int(end.item())
        dist.all_reduce(request,op=dist.ReduceOp.MAX)
    if request.item():
        steps=start_step
    budget_stop=steps<recipe['steps'] and not smoke_steps
    if steps==start_step and not smoke_steps:
        # A budget exhausted during startup can recur on resume at the same
        # step. Each allocation retains its own immutable exact checkpoint.
        checkpoint(output/f'checkpoint_{start_step:06d}',wrapped,optimizer,bound,start_step,rotate=True, **checkpoint_options())
        if recipe.get('export_at_stop'):
            export_resume_state(output, wrapped, model, cfg, start_step, rank, distributed=distributed,
                                optimizer=optimizer, disk_guard=disk_budget)
    for step,plan in enumerate(data.mixed_indices(counts,offset+steps,start_step=offset+start_step,
                              training_mode=cfg.get('training_mode', 'mixed'),
                              mix=recipe['mix'],world=recipe['world_size'],type_mix=getattr(rows, 'type_mix', None)),start_step+1):
        info,_=optimize_step(wrapped,optimizer,rows,plan,rank,device,step,distributed,gates)
        if answer_stop is not None:
            h1_state=answer_stop.update(step,info['h1_answer_counts'])
            info['h1_answer_stop']=h1_state
            if h1_state['triggered']:
                h1_limit=min(h1_limit or 100,100);h1_reason=STOP_RULE
        gathered = [None]*world
        if cfg.get('first_step_admission') and step == start_step+1:
            if distributed:
                dist.all_gather_object(gathered, info)
            else:
                gathered[0] = info
            first = first_step_report(gathered, bound, recipe, step, device.type)
            if rank == 0:
                (output/'inputs').mkdir(exist_ok=True)
                write(output/'inputs'/f'first_step_{attempt}.json', first)
            if first['status'] != 'PASS':
                raise ValueError('First native step failed admission: '+', '.join(first['errors']))
        if cfg.get('geometry_online'):
            if distributed:
                dist.all_gather_object(gathered, info)
            else:
                gathered[0] = info
            gx_history.append(gathered)
            fail = cfg['geometry_online'].get('fail_fast')
            if fail and (step == fail['step'] or
                         ('reference' in fail and step > fail['step'] and (step-fail['step']) % 10 == 0)):
                verdicts = [None]
                if rank == 0:
                    try:
                        verdicts[0] = gx_fail_fast(gx_history, fail, end_step=step,
                                                 reference_history=gx_reference(cfg, step))
                        # Every attempt and window retains its own immutable verdict.
                        write(output/f'gx_fail_fast_{attempt}_step_{step:06d}.json', verdicts[0])
                    except Exception as exc:
                        verdicts[0] = dict(error=f'{type(exc).__name__}: {exc}')
                if distributed:
                    dist.broadcast_object_list(verdicts, src=0)
                verdict = verdicts[0]
                if 'error' in verdict:
                    raise ValueError('GX fail-fast check failed: '+verdict['error'])
                gx_stop = verdict['verdict'] == 'STOP'
        if gates is not None:
            gates.update(info['head_metrics'])
        due=torch.tensor([int(time.monotonic()-last_save >= recipe['resume_every_seconds']
                              or (bool(cfg.get('first_step_admission')) and step == start_step+1))],device=device)
        if distributed:
            dist.all_reduce(due,op=dist.ReduceOp.MAX)
        pending = timing.get('checkpoint_seconds',0.) if due.item() else 0.
        pending += timing.get('export_seconds',0.) if step in recipe['milestones'] else 0.
        next_cost = max(info['wall_seconds'],timing.get('p95_step_seconds',0.)) + timing.get('checkpoint_seconds',0.)
        next_cost += timing.get('export_seconds',0.) if (step+1 in recipe['milestones'] or recipe.get('export_at_stop')) else 0.
        request=torch.tensor([int(stop[0] or (output/('stop.'+os.environ.get('SLURM_JOB_ID','local')+'.request')).exists() or time.monotonic()-started+pending+next_cost >=
            recipe['wall_seconds']-recipe['stop_before_seconds'])],device=device)
        if distributed:
            dist.all_reduce(request,op=dist.ReduceOp.MAX)
        gate_stop=not smoke_steps and step==400 and start_step<400 and step400_gate_enabled(cfg)
        h1_stop = bool(not smoke_steps and h1_limit is not None and step >= h1_limit)
        stopping=bool(request.item()) or step==steps or gate_stop or gx_stop or h1_stop
        info['checkpoint_seconds']=info['export_seconds']=0.
        if (not smoke_steps and (due.item() or stopping)) or gx_stop:
            tick=time.perf_counter()
            checkpoint(output/f'checkpoint_{step:06d}',wrapped,optimizer,bound,step,rotate=True, **checkpoint_options())
            info['checkpoint_seconds']=time.perf_counter()-tick
            last_save=time.monotonic()
        if not smoke_steps and (step in recipe['milestones'] or h1_stop or (stopping and recipe.get('export_at_stop'))):
            tick=time.perf_counter()
            reused = [existing_export(output/f'm{step}', cfg, step) if rank == 0 else None]
            if distributed:
                dist.broadcast_object_list(reused, src=0)
            if not reused[0]:
                export(output/f'm{step}',wrapped,model,cfg,step,optimizer=optimizer,disk_guard=disk_budget)
            info['export_reused'] = reused[0]
            info['export_seconds']=time.perf_counter()-tick
            if hasattr(rows, 'validation_count') and rows.validation_count():
                tick=time.perf_counter()
                info['validation'] = validation_read(wrapped,rows,rank,device,step,output,distributed)
                info['validation_seconds']=time.perf_counter()-tick
        gathered=[None]*world
        if distributed:
            dist.all_gather_object(gathered,info)
        else:
            gathered[0]=info
        if rank==0:
            measured.append(gathered)
            with (output/f'metrics_{attempt}.jsonl').open('a') as handle:
                handle.write(json.dumps(dict(step=step,ranks=gathered))+'\n')
        if h1_stop and rank == 0:
            write(output/f'h1_stop_{step:06d}.json', dict(schema='h1-stop-v1', step=step,
                  lr_horizon=recipe['steps'], milestone=str(output/f'm{step}'), reason=h1_reason, stop_state=h1_state))
        if stopping:
            break
    report=dict(schema='c1-smoke-v1' if smoke_steps else 'c1-run-v1',status='PASS',
        first_step=start_step+1,last_step=step,steps=measured,elapsed_seconds=time.monotonic()-started,
        stopped_for_resume=not h1_stop and not bool(smoke_steps) and step<recipe['steps'],world_size=world,
        gpu_fit_measured=device.type=='cuda' and distributed)
    if h1_stop:report['status']='H1_STOP'
    report['stop_reason']=h1_reason if h1_stop else 'gx_fail_fast' if gx_stop else 'm400_gate' if gate_stop else 'budget_or_signal' if bool(request.item()) or budget_stop else 'schedule'
    if cfg.get('geometry_online'):
        report['binding'] = bound
    if rank==0:
        write(output/('smoke.json' if smoke_steps else f'run_{attempt}.json'),report)
    return report


def gx_recipe(model):
    """A GX model's own recipe (it carries geometry_learning_rate); other models keep the default groups."""
    model = getattr(model, 'module', model)
    return {'recipe': model.recipe} if getattr(model, 'geometry_online', None) else {}


def metrics_records(path):
    """Ignore only an unterminated final JSON write; validate every other line."""
    def reject_constant(value):
        raise ValueError('Nonfinite metrics JSON: '+value)
    with Path(path).open('rb') as handle:
        remaining = os.fstat(handle.fileno()).st_size
        while remaining:
            raw = handle.readline(remaining)
            if not raw:
                raise ValueError('Metrics file shortened during read')
            remaining -= len(raw)
            line = raw.decode('utf-8')
            try:
                row = json.loads(line, object_pairs_hook=unique, parse_constant=reject_constant)
            except json.JSONDecodeError as exc:
                tail = line[exc.pos:].rstrip()
                incomplete = (exc.msg.startswith('Unterminated string') or not tail or
                              any(word.startswith(tail) for word in ('true', 'false', 'null')) or
                              (tail == '-' and exc.msg == 'Expecting value') or
                              (exc.msg == "Expecting ',' delimiter" and
                               re.fullmatch(r'(?:[eE][+-]?|\.)', tail) is not None) or
                              (exc.msg == 'Invalid \\uXXXX escape' and
                               re.fullmatch(r'u[0-9a-fA-F]{0,4}', tail) is not None))
                if not remaining and not line.endswith('\n') and incomplete:
                    return
                raise
            if (not isinstance(row, dict) or type(row.get('step')) is not int or row['step'] < 1
                    or not isinstance(row.get('ranks'), list) or not row['ranks']
                    or any(not isinstance(r, dict) or r.get('step') != row['step'] for r in row['ranks'])):
                raise ValueError('Invalid metrics step record')
            yield row


def gx_validate_history(history, step):
    if (len(history) != step or any(not ranks or any(r.get('step') != s for r in ranks)
                                   for s, ranks in enumerate(history, 1))):
        raise ValueError('Missing GX fail-fast window steps in resume history')


def reference_attempt_records(output, expected_binding):
    """Authenticate resumed attempts by checkpoint pins, never by file timestamps."""
    output = Path(output)
    bindings = [b for b, _ in output_bindings(output)]
    if any(b != expected_binding for b in bindings):
        raise ValueError('Reference history differs from pinned binding')
    def config_evidence(receipt):
        if 'config' not in receipt:
            return
        try:
            valid = isinstance(receipt['config'], dict) and identity(receipt['config']) == expected_binding['config_sha256']
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError('Malformed reference receipt config') from exc
        if not valid:
            raise ValueError('Reference receipt config identity differs')
    attempts, reports, rows = {}, {}, {}
    def job_identity(receipt, name):
        # Native CTRL receipts identify the job by their filename. Check an explicit
        # job_id too when supplied; it cannot override the paired filename suffix.
        if 'job_id' in receipt and (type(receipt['job_id']) not in (str, int)
                                   or str(receipt['job_id']) != name):
            raise ValueError('Reference receipt job id differs from its filename')
    for path in sorted(output.glob('attempt_*.json')):
        name = path.stem.removeprefix('attempt_')
        attempt = load(path)
        if attempt.get('binding') != expected_binding:
            raise ValueError('Reference attempt binding differs')
        job_identity(attempt, name)
        config_evidence(attempt)
        if attempt.get('export_of') is not None:
            continue
        if attempt.get('binding') not in bindings or type(attempt.get('first_step')) is not int:
            raise ValueError('Reference attempt binding or first step differs')
        attempts[name] = attempt
        report_path = output/f'run_{name}.json'
        if report_path.exists():
            report = load(report_path)
            job_identity(report, name)
            if (('binding' in report and report['binding'] != expected_binding) or
                    report.get('schema') != 'c1-run-v1' or report.get('status') != 'PASS'
                    or report.get('world_size') != attempt['binding']['world_size']
                    or type(report.get('first_step')) is not int
                    or report.get('first_step') != attempt['first_step']
                    or type(report.get('last_step')) is not int
                    or report['last_step'] < report['first_step']
                    or ('last_step' in attempt and attempt['last_step'] != report['last_step'])
                    or not isinstance(report.get('steps'), list)):
                raise ValueError('Reference run receipt differs from its attempt')
            config_evidence(report)
            reports[name] = report
    if any(path.stem.removeprefix('run_') not in reports for path in output.glob('run_*.json')):
        raise ValueError('Reference run receipt lacks an authenticated attempt')
    for path in sorted(output.glob('metrics_*.jsonl')):
        name = path.stem.removeprefix('metrics_')
        if name not in attempts:
            raise ValueError('Reference metrics lack an authenticated attempt')
        records = list(metrics_records(path))
        if len({r['step'] for r in records}) != len(records):
            raise ValueError('Duplicate reference steps within an attempt')
        for record in records:
            if (record['step'] < attempts[name]['first_step'] or
                    len(record['ranks']) != attempts[name]['binding']['world_size']):
                raise ValueError('Reference metrics differ from attempt row layout')
        if name in reports:
            report = reports[name]
            # The completed receipt retains the exact rank collections written to metrics.
            expected = {report['first_step']+i: ranks for i, ranks in enumerate(report['steps'])}
            if (len(expected) != report['last_step']-report['first_step']+1 or
                    len(records) != len(expected) or
                    [r['step'] for r in records] != list(expected) or
                    any(expected.get(r['step']) != r['ranks'] for r in records)):
                raise ValueError('Reference metrics differ from completed run receipt')
        rows[name] = records
    if any(name not in rows for name in reports):
        raise ValueError('Reference completed run lacks its metrics file')
    if not attempts:
        raise ValueError('Reference has no authenticated attempts')
    parents, cuts = {}, {}
    for name, attempt in attempts.items():
        resume = attempt.get('resume')
        if resume is None:
            if attempt['first_step'] != 1:
                raise ValueError('Reference root does not start at step 1')
            parents[name] = None
            continue
        path = Path(resume['path'])
        if (path.name != 'complete.json' or path.parent.parent.resolve() != output.resolve()):
            raise ValueError('Reference resume is outside its run')
        if not path.exists():
            path = output/'_superseded'/path.parent.name/path.name
        manifest = load(pinned({**resume, 'path': str(path)}))
        cut = manifest['step']
        if (manifest.get('schema') != 'c1-checkpoint-v1' or manifest.get('binding') not in bindings
                or attempt['first_step'] != cut+1):
            raise ValueError('Reference resume identity differs')
        owner = manifest.get('gx_attempt')
        candidates = [key for key, report in reports.items() if key != name
                      and report['first_step'] <= cut <= report['last_step']
                      and attempts[key]['binding'] == manifest['binding']]
        if owner is not None:
            candidates = [owner] if owner in attempts and owner != name and (
                attempts[owner]['binding'] == manifest['binding'] and attempts[owner]['first_step'] <= cut) else []
        if len(candidates) != 1:
            raise ValueError('Reference resume has ambiguous or missing attempt lineage')
        parents[name], cuts[name] = candidates[0], cut
    tips = set(attempts)-{p for p in parents.values() if p is not None}
    if len(tips) != 1:
        raise ValueError('Reference attempt lineage is forked')
    chain, name = [], tips.pop()
    while name is not None:
        if name in chain:
            raise ValueError('Reference attempt lineage is cyclic')
        chain.append(name)
        name = parents[name]
    if len(chain) != len(attempts):
        raise ValueError('Reference attempt lineage is disconnected')
    records = {}
    for name in reversed(chain):
        if name in cuts:
            records = {s: r for s, r in records.items() if s <= cuts[name]}
        records.update({r['step']: r['ranks'] for r in rows.get(name, [])})
    return records, bindings


def gx_preparation_rows(receipt):
    """Compare row content and sampling, excluding model/optimizer/GX metadata."""
    if receipt.get('schema') != 'c1-preparation-v1':
        raise ValueError('Reference preparation schema differs')
    def content(value):
        # Equal SHA-256 pins name equal bytes even when preparation directories differ.
        # Do not read large databases/frame bundles during reference authentication.
        if isinstance(value, dict):
            if set(value) == {'path', 'sha256'}:
                if (not isinstance(value['path'], str) or not Path(value['path']).is_absolute()
                        or not isinstance(value['sha256'], str)
                        or re.fullmatch('[0-9a-f]{64}', value['sha256']) is None):
                    raise ValueError('Invalid reference preparation content pin')
                return {'sha256': value['sha256']}
            return {k: content(v) for k, v in value.items()}
        if isinstance(value, list):
            return [content(v) for v in value]
        return value
    recipe = receipt['recipe']
    world = recipe['world_size']
    order = [stream for stream in recipe['mix'] for _ in range(world)]
    if not order or len(order) != recipe['global_batch']:
        raise ValueError('Reference preparation sampler layout differs')
    # Compare every stream entry, including receipt, database, count, source_count,
    # indices; composite streams also bind kind, sources and order. This includes
    # all nested row inventories and frame-bundle pins. The database/source receipt
    # hashes bind the per-row RGB pins. Preserve stream insertion order: the sampler
    # seeds its independent RNGs by that order. No stream field is discarded.
    return dict(streams=[(name, content(value)) for name, value in receipt['streams'].items()],
                training_mode=receipt.get('training_mode', 'mixed'),
                row_start_step=receipt.get('row_start_step', 0),
                seed=recipe['seed'], global_batch=recipe['global_batch'], flattened_mix=order,
                frame_layout=receipt.get('frame_layout', 'spread'),
                frame_pair_gap_seconds=receipt.get('frame_pair_gap_seconds'))


def gx_reference(cfg, end_step):
    """Bind a paired control to the same admitted rows and flattened sampler order."""
    fail = (cfg.get('geometry_online') or {}).get('fail_fast')
    if not fail or 'reference' not in fail:
        return None
    output = Path(fail['reference'])
    from .g3t_online import reference_binding_pin
    pin = reference_binding_pin(fail.get('reference_binding'))
    reference_binding = load(pinned(dict(path=str(output/'binding.json'), sha256=pin['sha256'])))
    if (set(reference_binding) != EXPORT_BINDING_KEYS or
            reference_binding['config_sha256'] != pin['config_sha256'] or
            reference_binding['trainer_commit'] != pin['trainer_commit']):
        raise ValueError('Reference binding differs from parent pin')
    records, bindings = reference_attempt_records(output, reference_binding)
    preparation = cfg['preparation']
    receipt = load(pinned(preparation))
    def schedule(value, world):
        recipe = value['recipe']
        order = [s for s in recipe['mix'] for _ in range(world)]
        if recipe['world_size'] != world or len(order) != recipe['global_batch']:
            raise ValueError('Reference sampler world/microstep layout differs')
        return (value.get('training_mode', 'mixed'), value.get('row_start_step', 0), recipe['seed'], order)
    own = schedule(cfg, recipe_for(cfg)['world_size'])
    for bound in bindings:
        reference_receipt = load(pinned(bound['preparation']))
        if (bound['preparation'] != preparation and
                digest(gx_preparation_rows(reference_receipt)) != digest(gx_preparation_rows(receipt))):
            raise ValueError('Reference preparation row identity differs')
        try:
            reference_cfg = stored_config(output, bound)
        except ValueError:
            # B0 CTRL receipts do not store a full config. Native prepared() enforces
            # this pinned non-GX receipt's recipe, streams and sampler offset exactly.
            if (reference_receipt.get('schema') != 'c1-preparation-v1' or reference_receipt.get('geometry_online') or
                    (output/f'binding_config_{digest(bound)}.json').exists()):
                raise ValueError('Reference lacks authenticated sampler settings')
            reference_cfg = reference_receipt
        if schedule(reference_cfg, bound['world_size']) != own:
            raise ValueError('Reference sampler or row_start_step differs')
        if ('streams' in reference_cfg and reference_cfg is not reference_receipt and
                reference_cfg['streams'] != cfg['streams']):
            raise ValueError('Reference stream order differs')
    return {s: r for s, r in records.items() if s <= end_step}


def gx_step_history(output, start_step, *, by_step=False):
    """Read one retained rank collection per completed step through the resume point."""
    records = {}
    for path in sorted(Path(output).glob('metrics_*.jsonl'), key=lambda p: (p.stat().st_mtime_ns, p.name)):
        for row in metrics_records(path):
            if row['step'] <= start_step:
                records[row['step']] = row['ranks']
    return records if by_step else [records[k] for k in sorted(records)]


def gx_rule_hash(settings):
    """Hash the normalized fail-fast block, including its optional control path."""
    normalized = copy.deepcopy(settings)
    if normalized is not None:
        for key in ('min_delta_ratio', 'max_loss_ratio'):
            normalized[key] = float(normalized[key])
    return digest(normalized)


def gx_fail_fast(history, settings, *, end_step=None, reference_history=None):
    """Compare rank-mean pose losses on matched steps, or retain the original self-history rule."""
    def step_values(ranks):
        deltas = [shape['gx']['delta_ratio'] for info in ranks for shape in info['shapes']
                  if 'gx' in shape and not shape['gx'].get('single_image_fusion_skipped', False)
                  and not shape['gx'].get('no_carriers_geometry_skipped', False)]
        losses = [info['stream_means']['pose'] for info in ranks]
        if not deltas or not all(np.isfinite(v) for v in deltas + losses):
            raise ValueError('Missing or nonfinite GX fail-fast history')
        return float(np.median(deltas)), float(np.mean(losses))
    end_step = settings['step'] if end_step is None else end_step
    recent_history = history[-10:]
    reference_mean, missing = None, []
    if 'reference' in settings:
        first = max(1, end_step-9)
        own = {ranks[0]['step']: ranks for ranks in history}
        window = list(range(first, end_step+1))
        if any(s not in own or any(r['step'] != s for r in own[s]) for s in window):
            raise ValueError('Missing GX fail-fast window steps')
        recent_history = [own[s] for s in window]
        if reference_history is None:
            raise ValueError('Paired GX fail-fast requires an authenticated reference snapshot')
        reference = reference_history
        missing = [s for s in window if s not in reference]
        if not missing:
            losses = [[r['stream_means']['pose'] for r in reference[s]] for s in window]
            if any(not values or not all(np.isfinite(v) for v in values) for values in losses):
                raise ValueError('Missing or nonfinite reference pose loss')
            reference_mean = float(np.mean([np.mean(values) for values in losses]))
    steps = [step_values(ranks) for ranks in history]
    initial = float(np.mean([v[1] for v in steps[:10]]))
    recent = float(np.mean([step_values(ranks)[1] for ranks in recent_history]))
    delta = float(np.median([shape['gx']['delta_ratio'] for ranks in recent_history
                            for info in ranks for shape in info['shapes']
                            if 'gx' in shape and not shape['gx'].get('single_image_fusion_skipped', False)
                            and not shape['gx'].get('no_carriers_geometry_skipped', False)]))
    baseline = reference_mean if 'reference' in settings else initial
    stop = not missing and (delta < settings['min_delta_ratio'] or recent > settings['max_loss_ratio'] * baseline)
    return dict(step=end_step, rule_sha256=gx_rule_hash(settings),
                rule='paired_control' if 'reference' in settings else 'own_history',
                reference=settings.get('reference'), reference_pose_loss=reference_mean,
                missing_reference_steps=missing, window_start_step=max(1, end_step-len(recent_history)+1),
                reason='missing_reference_steps' if missing else 'threshold_exceeded' if stop else 'within_thresholds',
                median_delta_ratio=delta, initial_pose_loss=initial,
                recent_pose_loss=recent, min_delta_ratio=settings['min_delta_ratio'],
                max_loss_ratio=settings['max_loss_ratio'], verdict='STOP' if stop else 'CONTINUE')


def gx_resume_verdicts(output, settings):
    """Current-rule STOPs block training; retain and report older-rule STOPs."""
    ignored = []
    for path in sorted(Path(output).glob('gx_fail_fast*.json')):
        verdict = load(path)
        if verdict.get('verdict') != 'STOP':
            continue
        if verdict.get('rule_sha256') == gx_rule_hash(settings):
            raise ValueError('GX fail-fast STOP output cannot resume under the current rule')
        ignored.append(dict(path=str(path), rule_sha256=verdict.get('rule_sha256')))
    return ignored


EXPORT_BINDING_KEYS = {'config_sha256', 'preparation', 'trainer_commit', 'world_size'}


def check_export_binding(export_binding, bound):
    """An export leg restores another trainer build's state: same world and preparation, its own binding."""
    if (not isinstance(export_binding, dict) or set(export_binding) != EXPORT_BINDING_KEYS
            or export_binding['world_size'] != bound['world_size']
            or export_binding['preparation'] != bound['preparation']):
        raise ValueError('Export binding must name the run state at this world size and preparation')
    return export_binding


def export_resume_state(output, wrapped, model, cfg, step, rank, distributed=True, *, optimizer=None, disk_guard=None):
    """Publish a restored resume state as the milestone-format artifact m<step> (the 'x' leg)."""
    directory = Path(output)/f'm{step}'
    reused = [existing_export(directory, cfg, step) if rank == 0 else None]
    if distributed:
        dist.broadcast_object_list(reused, src=0)
    if not reused[0]:
        export(directory, wrapped, model, cfg, step, optimizer=optimizer, disk_guard=disk_guard)
    return directory, bool(reused[0])


def train(cfg, smoke_steps=None, resume_pin=None, export_binding=None):
    from .trace_version import metadata, bind
    version_metadata = metadata(cfg)
    validate(cfg)
    ignored_stops = []
    if cfg.get('geometry_online'):
        ignored_stops = gx_resume_verdicts(cfg['output'], cfg['geometry_online'].get('fail_fast'))
        if ignored_stops:
            print(json.dumps(dict(gx_ignored_older_rule_stops=ignored_stops)), file=sys.stderr, flush=True)
        gx_reference(cfg, 0)  # Refuse an unrelated control before CUDA/model startup.
    if smoke_steps is not None and (type(smoke_steps)!=int or not 1<=smoke_steps<=10 or resume_pin):
        raise ValueError('Smoke needs 1..10 steps and cannot resume')
    export_only = export_binding is not None
    if export_only and (smoke_steps is not None or not resume_pin):
        raise ValueError('An export leg restores a resume state and trains no step')
    world_size=recipe_for(cfg)['world_size']
    cpu = rehearsal.enabled()
    if (not cpu and not torch.cuda.is_available()) or int(os.environ.get('WORLD_SIZE','0'))!=world_size:
        raise ValueError('C1 training requires a parent-authorized '
                         + ('eight' if world_size == 8 else str(world_size)) + '-GPU allocation')
    rank=int(os.environ['RANK']); local=int(os.environ['LOCAL_RANK'])
    device=torch.device('cpu' if cpu else f'cuda:{local}')
    if not cpu:
        torch.cuda.set_device(local)
    import datetime
    # Training collectives fail fast (15 min). Only the startup barriers and broadcasts, while
    # rank 0 hashes and loads assets, may wait longer (a separate gloo group, 60 min).
    dist.init_process_group('gloo' if cpu else 'nccl', timeout=datetime.timedelta(seconds=30 if cpu else 900))
    startup=dist.new_group(backend='gloo', timeout=datetime.timedelta(seconds=30 if cpu else 3600))
    started=time.monotonic()
    if os.environ.get('TK_JOB_START','').isdecimal():
        # The leg budget counts from the allocation start (kit staging included), so the trainer
        # checkpoints and exits before the wall; the kit sends no USR1 (it would kill the sandbox).
        started-=max(0.,time.time()-int(os.environ['TK_JOB_START']))
    network=network_preflight(device, world_size)
    # Authentication runs once, before other ranks load any payload.
    values=[None]
    if rank==0:
        try:
            values[0]=prepared(cfg,admission=True)
        except Exception as exc:
            values[0]=dict(error=f'{type(exc).__name__}: {exc}')
    dist.broadcast_object_list(values,src=0,group=startup)
    if isinstance(values[0],dict):
        raise ValueError('Rank 0 preparation check failed: '+values[0]['error'][:400])
    receipt,manifest=values[0]
    # All ranks authenticate the source, without repeatedly hashing large data.
    commit=authenticate(cfg)
    authorization=load(pinned(cfg['authorization'])) if cfg.get('authorization') else {}
    if (authorization.get('config_sha256')!=identity(cfg) or authorization.get('new_gpus')!=(0 if cpu else world_size)
            or str(authorization.get('job_id'))!=rehearsal.attempt_id()
            or authorization.get('verdict')!='GO'):
        warn(cfg,'Parent must authorize this exact eight-GPU allocation')
    torch.manual_seed(RECIPE['seed']);random.seed(RECIPE['seed']);np.random.seed(RECIPE['seed'])
    processor=processor_for_receipt(manifest,receipt)
    # Parent stages a single authenticated model on node-local storage. Hash once
    # in rank zero; every rank still loads the same immutable base manifest.
    model, error = None, None
    if rank==0:
        try:
            model=load_model(manifest,receipt,processor)
        except Exception as exc:
            error=f'{type(exc).__name__}: {exc}'
    agree(startup, error if rank==0 else None)
    if rank!=0:
        try:
            model=load_model(manifest,receipt,processor,verify_assets=False)
        except Exception as exc:
            error=f'{type(exc).__name__}: {exc}'
    if error is None and os.environ.get('C1_EXPECT_FLA')=='1':
        error=fla_check(model)
    agree(startup, error)
    bind(model,version_metadata,cfg)
    model.train()  # HF decoder checkpointing requires training mode; vision stays eval.
    wrapped=wrap_model(model,device,mixed_precision=not cpu)
    bind(wrapped,version_metadata,cfg)
    optimizer=torch.optim.AdamW(parameter_groups(wrapped,inherited=set(getattr(model,'inherited_head_params',())),
                                                 pose_lr_scale=cfg.get('pose_lr_scale', 1.0),
                                                 lm_lr_scale=cfg.get('lm_lr_scale', 1.0), **gx_recipe(model)),
                                weight_decay=RECIPE['weight_decay'])
    bound=dict(config_sha256=identity(cfg),preparation=cfg['preparation'],trainer_commit=commit,world_size=world_size)
    restore_bound = check_export_binding(export_binding, bound) if export_only else bound
    if resume_pin == 'latest':
        pins = [(latest_resume(cfg['output'], restore_bound, cfg=cfg) if cfg.get('geometry_online') and not export_only
                 else latest_resume(cfg['output'], restore_bound)) if rank == 0 else None]
        dist.broadcast_object_list(pins, src=0)
        resume_pin = pins[0]
    restore_options = dict(cfg=cfg) if cfg.get('geometry_online') and not export_only else {}
    start_step=restore(resume_pin,wrapped,optimizer,restore_bound, **restore_options) if resume_pin else 0
    if start_step>=recipe_for(cfg)['steps'] and not export_only:
        raise ValueError('Completed C1 schedules cannot resume')
    if start_step>=400 and not smoke_steps and step400_gate_enabled(cfg):
        milestone_gate(cfg)
    output=Path(cfg['output'])
    if smoke_steps:
        output=output/'smoke'/rehearsal.attempt_id()
    error=None
    try:
        rows=Rows(receipt,processor)
    except Exception as exc:
        rows,error=None,f'{type(exc).__name__}: {exc}'
    agree(startup, error)
    counts={k:v['count'] for k,v in receipt['streams'].items()}
    stop=[False]
    previous=signal.signal(signal.SIGUSR1,lambda *_:stop.__setitem__(0,True))
    attempt=rehearsal.attempt_id()
    lock=run_lock(output,rank); held=False
    try:
        error=None
        try:
            lock.__enter__(); held=True
            if rank==0:
                rebind = None
                if not smoke_steps and not export_only:
                    bind_options = dict(cfg=cfg, resume_pin=resume_pin) if cfg.get('geometry_online') else {}
                    rebind = bind_output(output, bound, resume=bool(resume_pin), **bind_options)
                write(output/f'attempt_{attempt}.json',dict(binding=bound,resume=resume_pin,first_step=start_step+1,
                      network=network,init=getattr(model,'init_report',None),export_of=export_binding,
                      **(dict(config=cfg, rebind=rebind, ignored_older_rule_stops=ignored_stops)
                         if cfg.get('geometry_online') else {})))
        except Exception as exc:
            error=f'{type(exc).__name__}: {exc}'
        # A rank-0 lock or binding refusal must stop every rank, never leave them in a barrier.
        agree(startup, error)
        dist.barrier()
        if device.type == 'cuda':
            torch.cuda.reset_peak_memory_stats(device)
        if export_only:
            directory, reused = export_resume_state(output, wrapped, model, cfg, start_step, rank, optimizer=optimizer)
            if rank==0:
                write(output/f'export_{attempt}.json', dict(step=start_step, resume=resume_pin, binding=restore_bound,
                      reused=reused, artifact=file_pin(directory/'artifact.json')))
            return
        history_options = {}
        if cfg.get('geometry_online') and resume_pin:
            saved = load(pinned(resume_pin))
            if 'gx_history' in saved:
                history_options['resume_history'] = saved['gx_history']
        run_or_exit(run_steps,model,wrapped,optimizer,rows,counts,output,cfg,bound,device,rank,start_step,
                    smoke_steps,started,stop,distributed=True, **history_options)
    finally:
        if sys.exc_info()[0] is not None:
            traceback.print_exc()
            sys.stdout.flush(); sys.stderr.flush()
            os._exit(1)
        if held:
            lock.__exit__(None,None,None)
        rows.close();signal.signal(signal.SIGUSR1,previous);dist.destroy_process_group()


def run_or_exit(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except Exception:
        traceback.print_exc()
        sys.stdout.flush(); sys.stderr.flush()
        os._exit(1)


def rewrite(path, value):
    """Progress files the check rewrites after every row: atomic replace, unlike write-once `write`."""
    path = Path(path); tmp = path.with_name(path.name + '.part')
    tmp.write_text(json.dumps(value, indent=1, sort_keys=True) + '\n')
    os.replace(tmp, path)


def check_plan_rows(model, rows, plans, ranks, sink=None, device=None):
    """Each listed rank's rows of the given step plans through fetch (encode, check_row) and the full
    no-grad forward on `device` (CPU by default); one record per (step, microstep, rank)."""
    records = []
    for step, plan in enumerate(plans, 1):
        for microstep, (stream, indices) in enumerate(plan):
            for rank in ranks:
                tick = time.perf_counter()
                record = dict(step=step, microstep=microstep, rank=rank, stream=stream, index=int(indices[rank]))
                try:
                    fetched = fetch(rows, stream, int(indices[rank]), model)
                    if fetched is None:
                        raise ValueError('every candidate row failed its checks')
                    batch, targets, audit = fetched
                    if device is not None:
                        batch, targets = move(batch, device), move(targets, device)
                    cuda = device is not None and torch.device(device).type == 'cuda'
                    if cuda:
                        torch.cuda.reset_peak_memory_stats(device)
                    with torch.no_grad():
                        result = model(batch, targets, stream=stream)
                    if stream == 'mdg':
                        import resource
                        record.update(result['metrics']['mdg'],
                                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
                    parts = {k: float(v) for k, v in result['components'].items()}
                    loss = float(result['loss'])
                    effective_tokens = int(batch['input_ids'].shape[-1])
                    if stream == 'mdg':
                        from .mdg_features import suffix_tokens
                        effective_tokens += max(len(suffix_tokens(model.mdg_tokenizer, label)[0])
                                                for label in batch['aux_mdg_labels'])
                    record.update(qid=(audit or {}).get('qid'), substituted_from=(audit or {}).get('substituted_from'),
                                  tokens=int(batch['input_ids'].shape[-1]),
                                  effective_tokens=effective_tokens, over_10k_tokens=effective_tokens > 10000,
                                  loss=loss, components=parts,
                                  finite=math.isfinite(loss) and all(math.isfinite(v) for v in parts.values()))
                    if cuda:
                        # No-grad forward peak on one device (whole model, no FSDP shards); not the training peak.
                        record['forward_peak_gib'] = round(torch.cuda.max_memory_allocated(device) / 2**30, 2)
                except Exception as exc:
                    record.update(error=f'{type(exc).__name__}: {str(exc)[:300]}', finite=False)
                record['seconds'] = round(time.perf_counter() - tick, 2)
                records.append(record)
                if sink:
                    sink(records)
    return records


def first_batch_check(cfg, ranks, out_path, steps=1, device='cpu', progress_dir=None, rank_limit=None):
    """First-batch check: every listed rank's first-step rows run the full forward on one device (CPU by
    default, or one GPU), with the LM base in BF16 as FSDP computes it and the heads in FP32."""
    validate(cfg)
    if not cfg.get('preparation'):
        # Same-job check right after prepare(): pin the receipt that prepare just wrote.
        cfg = {**cfg, 'preparation': file_pin(Path(cfg['preparation_output'])/'receipt.json')}
    receipt, manifest = prepared(cfg, admission=True)
    recipe = recipe_for(cfg)
    ranks = list(ranks)
    if (not ranks or len(set(ranks)) != len(ranks)
            or any(type(r) is not int or not 0 <= r < recipe['world_size'] for r in ranks)):
        raise ValueError('First-batch ranks must lie inside the run world')
    if rank_limit is not None and (progress_dir is None or type(rank_limit) is not int or rank_limit < 1):
        raise ValueError('A rank limit requires a checkpointed first-batch check')
    counts = {k: v['count'] for k, v in receipt['streams'].items()}
    plans = list(data.mixed_indices(counts, steps, training_mode=cfg.get('training_mode', 'mixed'),
                                    mix=recipe['mix'], world=recipe['world_size'],type_mix=getattr(rows, 'type_mix', None)))
    device = torch.device(device)
    out = Path(out_path)
    journal, completed, records = None, {}, []
    resources = dict(cpu_threads=torch.get_num_threads(), model_loads=0, reused_ranks=[], executed_ranks=[])
    if progress_dir is not None:
        from .first_batch_progress import RankJournal
        journal = RankJournal(progress_dir, dict(config_sha256=identity(cfg), preparation=cfg['preparation'],
            code=cfg['code'], steps=steps, device=str(device), torch_version=torch.__version__,
            cpu_threads=torch.get_num_threads()), plans)
        completed = {rank: value for rank in ranks if (value := journal.load(rank)) is not None}
        records = [row for rank in ranks if rank in completed for row in completed[rank]['records']]
        resources['reused_ranks'] = list(completed)
    pending = [rank for rank in ranks if rank not in completed]

    def report(current):
        extra = (dict(status='PASS' if len(completed) == len(ranks) else 'PARTIAL', resources=resources,
                      completed_ranks=list(completed), rank_resources={str(k): v['resources'] for k, v in completed.items()},
                      progress_directory=str(journal.root)) if journal is not None else {})
        rewrite(out, dict(schema='c1-first-batch-check-v1', ranks=ranks, steps=steps, device=str(device),
                          records=current, **extra))

    if not pending:
        report(records)
        return records
    if journal is not None:
        torch.manual_seed(RECIPE['seed']); random.seed(RECIPE['seed']); np.random.seed(RECIPE['seed'])
    started = time.perf_counter()
    processor = processor_for_receipt(manifest, receipt)
    model = load_model(manifest, receipt, processor)
    resources.update(model_loads=1, model_load_seconds=time.perf_counter()-started,
                     total_parameters=sum(p.numel() for p in model.parameters()),
                     base_parameters=sum(p.numel() for _, p in full_ft.base_parameters(model)))
    for _, parameter in full_ft.base_parameters(model):
        parameter.data = parameter.data.to(torch.bfloat16)
    model.to(device).eval()
    rows = Rows(receipt, processor)
    try:
        if journal is not None:
            import resource
            for rank in pending[:rank_limit]:
                started = time.perf_counter()
                current = check_plan_rows(model, rows, plans, [rank], device=None if device.type == 'cpu' else device,
                                          sink=lambda chunk: report(records+chunk))
                if any(record['finite'] is not True for record in current):
                    raise ValueError(f'First-batch check failed on rank {rank}')
                measured = dict(seconds=time.perf_counter()-started, cpu_threads=torch.get_num_threads(),
                                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                rows=len(current), tokens=sum(row['effective_tokens'] for row in current))
                completed[rank] = journal.save(rank, current, measured)
                resources['executed_ranks'].append(rank)
                records.extend(current)
                report(records)
        else:
            records = check_plan_rows(model, rows, plans, ranks, device=None if device.type == 'cpu' else device,
                                      sink=report)
        failed = [(record['rank'], record['stream']) for record in records if not record['finite']]
        if failed:
            raise ValueError(f'First-batch check failed on rank/stream pairs: {failed}')
        return records
    finally:
        rows.close()


def fla_check(model):
    """The kit's fla overlay must bind the fused Gated DeltaNet kernel and gated norm (LT1's tested pair)."""
    try:
        import triton
        import fla
        attention = model.model.language_model.layers[0].linear_attn
        found = dict(triton=triton.__version__, fla=fla.__version__, norm=type(attention.norm).__name__,
                     kernel=getattr(attention.chunk_gated_delta_rule, '__module__', ''))
    except Exception as exc:
        return f'fla overlay check failed: {type(exc).__name__}: {exc}'
    if (found['triton'] != '3.7.1' or found['fla'] != '0.6.0' or found['norm'] != 'FusedRMSNormGated'
            or not found['kernel'].startswith('fla')):
        return 'fla overlay not bound: ' + json.dumps(found)
    return None


def agree(group, error=None):
    """Every rank learns whether any rank failed a startup step (gloo, 60 min); all raise together."""
    errors=[None]*dist.get_world_size()
    dist.all_gather_object(errors, error, group=group)
    failed=[(rank, e) for rank, e in enumerate(errors) if e]
    if failed:
        raise ValueError(f'Startup failed on rank {failed[0][0]}: {failed[0][1][:400]}')


def network_preflight(device, world, floor_gbps=150., total_bytes=2 << 30):
    """Multi-node worlds must reach `floor_gbps` all_gather bus bandwidth (EFA), never TCP."""
    local = int(os.environ.get('LOCAL_WORLD_SIZE', world))
    if world <= local:
        return None
    per_rank = total_bytes // world // 2
    send = torch.ones(per_rank, dtype=torch.bfloat16, device=device)
    receive = torch.empty(per_rank * world, dtype=torch.bfloat16, device=device)
    times = []
    for _ in range(8):
        torch.cuda.synchronize(device); tick = time.perf_counter()
        dist.all_gather_into_tensor(receive, send)
        torch.cuda.synchronize(device); times.append(time.perf_counter() - tick)
    measured = sorted(times[2:])[len(times[2:]) // 2]
    busbw = torch.tensor([2 * per_rank * world * (world - 1) / world / measured / 1e9], device=device)
    dist.all_reduce(busbw, op=dist.ReduceOp.MIN)
    del send, receive
    torch.cuda.empty_cache()
    report = dict(all_gather_busbw_gbps=round(float(busbw), 1), world=world, bytes=2 * per_rank * world,
                  floor_gbps=floor_gbps, plugin=os.environ.get('NCCL_NET_PLUGIN'), provider=os.environ.get('FI_PROVIDER'))
    print(json.dumps({'network_preflight': report}), flush=True)
    if float(busbw) < floor_gbps:
        raise ValueError(f'Inter-node all_gather {float(busbw):.1f} GB/s < {floor_gbps} GB/s; refusing to train over TCP')
    return report


def load_artifact(model, artifact_pin):
    artifact=load(pinned(artifact_pin))
    from .trace_version import bind
    if artifact.get('trace_program_version') is not None or artifact.get('trace_version_binding'):
        bind(model,artifact,{'trace_program_version':getattr(model,'trace_program_version',None)})
    if artifact.get('trace_program_version') == '3.14' and not isinstance(artifact.get('trained_groups'), dict):
        raise ValueError('v3.14 artifact lacks its trained-group contract')
    if artifact.get('schema')!='carrier-c1-artifact-v1' or artifact['pose_backing']!='lm_final_norm':
        raise ValueError('Not a C1 artifact')
    if artifact.get('geometry_online') != getattr(model, 'geometry_online', None):
        raise ValueError('Artifact geometry_online differs from the model')
    if (artifact.get('placement') != model.carrier_placement or artifact.get('training_mode') != model.training_mode
            or artifact.get('frame_layout', 'spread') != model.frame_layout
            or artifact.get('carrier_position_policy', 'native_v1') != model.carrier_position_policy
            or (artifact.get('depth_backing') is not None) != hasattr(model.auxiliary_heads, 'depth')):
        raise ValueError('Artifact placement/training mode/position policy/depth differs')
    for _,p in full_ft.base_parameters(model):
        p.data=p.data.to(torch.bfloat16)
    full_ft.load_export(model,Path(pinned(artifact['full_weights'])).parent)
    state=torch.load(pinned(artifact['heads']),map_location='cpu',weights_only=True)
    if 'trained_groups' in artifact:
        from .trained_groups import validate
        validate(model, state, artifact['trained_groups'], artifact.get('step'))
    if artifact.get('mdg') and 'tau' in artifact['mdg']:
        from .mdg_decode import threshold
        model.mdg_tau = artifact['mdg']['tau']
        model.mdg_tau_info = artifact['mdg'].get('calibration', {})
        threshold(model)
    if model.training_mode == 'final' and getattr(model, 'geometry_online', None):
        if state.pop('_gx_geometry_online', None) != model.geometry_online:
            raise ValueError('heads.pt geometry_online pins differ')
        live = model.auxiliary_heads.state_dict()
        expected = {k for k in live if not k.startswith('geometry_encoder.')}
        missing, extra = expected - set(state), set(state) - expected
        if missing or extra:
            raise RuntimeError(f'Missing key(s): {sorted(missing)}; Unexpected key(s): {sorted(extra)}')
        model.auxiliary_heads.load_state_dict(state, strict=False)
    else:
        model.auxiliary_heads.load_state_dict(state,strict=True)
    if (getattr(model, 'geometry_online', None) or {}).get('gf1'):
        from .gf1 import check_camera_context
        check_camera_context(model, artifact)
    return artifact


def inference(cfg, artifact_pin, device):
    from .trace_version import resolve
    version_artifact=load(pinned(artifact_pin))
    resolve(version_artifact,cfg)
    native_cfg=cfg if 'trace_program_version' in version_artifact else {k:v for k,v in cfg.items() if k!='trace_program_version'}
    receipt,manifest=prepared(native_cfg,admission=True)
    processor=processor_for_receipt(manifest,receipt)
    if (receipt.get('geometry_online') or {}).get('gf1'):
        if 'gf1' not in (receipt.get('init_artifact') or {}).get('heads', []):
            raise ValueError('GF1 export requires gf1 in evaluator init heads')
    if device.type=='cuda':
        auth=load(pinned(cfg['authorization'])) if cfg.get('authorization') else {}
        if (auth.get('config_sha256')!=identity(cfg) or auth.get('new_gpus')!=1
                or str(auth.get('job_id'))!=os.environ.get('SLURM_JOB_ID') or auth.get('verdict')!='GO'):
            warn(cfg,'Parent must authorize this exact readout allocation')
    model=load_model(manifest,receipt,processor,evaluation=True)
    artifact=load_artifact(model,artifact_pin)
    from .trace_version import bind
    bind(model,artifact,cfg)
    if artifact['base_identity']!=cfg['base_identity']:
        raise ValueError('Readout artifact has another base model')
    if artifact['config_sha256']!=identity(native_cfg):
        warn(cfg,'Readout artifact has another C1 config identity')
    model.to(device).eval().requires_grad_(False)
    return model,processor,receipt,artifact


def probe(cfg, artifact_pin, report_path, device=torch.device('cpu'), zero_g3t=False):
    model,processor,receipt,artifact=inference(cfg,artifact_pin,device)
    model.gx_zero_feature = zero_g3t
    rows=Rows(receipt,processor);records=[]
    try:
        for index in range(min(32,receipt['streams']['pose']['count'])):
            batch,target,_=rows.get('pose',index)
            start=time.perf_counter()
            result=model.probe(move(batch,device),move(target,device))
            records.append(dict(index=index,seconds=time.perf_counter()-start,**result))
    finally:
        rows.close()
    report=dict(schema='c1-head-probe-v1',artifact=artifact_pin,step=artifact['step'],rows=records,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                peak_cuda_bytes=torch.cuda.max_memory_allocated(device) if device.type=='cuda' else 0)
    if cfg.get('geometry_online'):
        report.update(geometry_online=cfg['geometry_online'], zero_g3t=zero_g3t)
    write(report_path,report)
    return report


def evaluate(cfg, artifact_pin, report_path, device=torch.device('cpu'), zero_g3t=False):
    """Always score sparse anchors; add contiguous clips when their pin exists."""
    import gzip
    from .all_frame_bank import read_bank
    from .all_frame_readout import evaluate as score
    from .compact_label_bank import frame_set_sha256
    from .carrier_c1_clip import check_clips, pose_vectors_to_c2w, trajectory_metrics, summarize
    model,processor,receipt,artifact=inference(cfg,artifact_pin,device)
    model.gx_zero_feature = zero_g3t
    held=cfg['readout'];bank=read_bank(str(pinned(held['bank'])))
    lookup={k:i for i,k in enumerate(zip(bank['dataset_tokens'].tolist(),bank['scene_tokens'].tolist()))}
    training={tuple(x) for x in load(pinned(held['training_scenes']))['scenes']}
    if len(lookup)!=38 or set(lookup)&training:
        raise ValueError('C1 readout needs the 38 disjoint gate scenes')
    clip_pin = held.get('contiguous_clips')
    clips = check_clips(load(pinned(clip_pin)), sorted(lookup), sorted(training)) if clip_pin is not None else []
    chosen={}
    for pin in load(pinned(held['rows_inventory']))['files']:
        with gzip.open(pinned(pin),'rt') as handle:
            for line in handle:
                row=json.loads(line);key=(row['dataset'],row['scene'])
                if key not in lookup or frame_set_sha256(row['student_input']['frame_indices'])!=str(bank['frame_set_sha256'][lookup[key]]):
                    raise ValueError('Heldout scene/frame selection differs')
                if key in chosen and row['student_input']['frames']!=chosen[key]['student_input']['frames']:
                    raise ValueError('Conflicting heldout RGB selection')
                chosen.setdefault(key,row)
    if set(chosen)!=set(lookup):
        raise ValueError('Missing heldout scene')
    records=[]
    for key,row in sorted(chosen.items()):
        i=lookup[key]
        # Unlabelled native prefix still receives per-frame carriers. The answer
        # suffix is after every carrier and cannot affect any head prediction.
        batch,_,_=data.encode(processor,{**row,'target':data.READOUT_TARGET},{},'vqa',cfg['carrier_placement'],
                             frame_layout=cfg.get('frame_layout', 'spread'),
                             frame_pair_gap_seconds=cfg.get('frame_pair_gap_seconds'),
                             **(dict(geometry_online=cfg['geometry_online']) if cfg.get('geometry_online') else {}))
        uv=bank['point_depth_uv'][i]
        values=model.readout(move(batch,device),uv)
        records.append(dict(dataset=key[0],scene=key[1],
            gt=dict(camera=bank['camera'][i],camera_mask=bank['camera_mask'][i],gravity=bank['gravity'][i],
                    gravity_mask=bool(bank['gravity_mask'][i]),trajectory_scale=float(bank['trajectory_scale'][i]),
                    point_depth_uv=uv,point_depth_gt=bank['point_depth_gt'][i],point_depth_mask=bank['point_depth_mask'][i],
                    depth_anchor_frames=bank['depth_anchor_frames'].tolist()),
            pred=dict(camera=values['raw_pose'],gravity=values['gravity_up'],
                      trajectory_step_m=values['trajectory_step_m'],point_depth=values['point_depth'],
                      invalid_fov_frames=values['invalid_fov_frames'],geometry_error=values['geometry_error'])))
    heads = {'pose'} if cfg.get('training_mode') == 'pose_only' else {'pose','gravity','scale'}
    if hasattr(model.auxiliary_heads, 'depth'):
        heads.add('depth')
    result=score(records,heads,sorted(lookup),sorted(training))
    measurements = []
    for clip in clips:
        batch,_,_=data.encode(processor,{**clip,'target':data.READOUT_TARGET},{},'vqa',cfg['carrier_placement'],
                             frame_layout=cfg.get('frame_layout', 'spread'),
                             frame_pair_gap_seconds=cfg.get('frame_pair_gap_seconds'),
                             **(dict(geometry_online=cfg['geometry_online']) if cfg.get('geometry_online') else {}))
        prediction = pose_vectors_to_c2w(model.pose_readout(move(batch, device)))
        measurements.append(dict(dataset=clip['dataset'], scene=clip['scene'], recording_id=clip['recording_id'],
                                 **trajectory_metrics(prediction, clip['gt_c2w'])))
    report=dict(schema='c1-readout-v2',artifact=artifact_pin,step=artifact['step'],bank=held['bank'],detail=result,
                config_sha256=identity(cfg), readout_sha256=readout_identity(cfg), contiguous_clips=clip_pin,
                contiguous_clip=summarize(measurements) if clip_pin is not None else None,
                contiguous_clip_pending=clip_pin is None, pose_gate_threshold_deg=39.,
                pointing_gate_pending=cfg.get('training_mode') != 'pose_only',
                vsi500_gate_pending=cfg.get('training_mode') != 'pose_only')
    if cfg.get('geometry_online'):
        report.update(geometry_online=cfg['geometry_online'], zero_g3t=zero_g3t)
    write(report_path,report)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['prepare','dryrun','train','build-stream','build-clips','probe','evaluate'])
    parser.add_argument('--config',required=True);parser.add_argument('--report')
    parser.add_argument('--smoke-steps',type=int);parser.add_argument('--resume',help='Pin JSON path, or latest')
    parser.add_argument('--artifact');parser.add_argument('--device',default='cpu',choices=['cpu','cuda:0'])
    parser.add_argument('--zero-g3t', action='store_true')
    args=parser.parse_args();cfg=load(args.config)
    if args.zero_g3t and (args.mode not in ('probe', 'evaluate') or not cfg.get('geometry_online')):
        parser.error('--zero-g3t requires GX probe/evaluate')
    if args.mode=='prepare':
        prepare(cfg)
    elif args.mode=='dryrun':
        if not args.report:
            parser.error('--report is required')
        dryrun(cfg,args.report)
    elif args.mode=='build-stream':
        data.build_stream(cfg['source'],cfg['division'],cfg['output'],cfg['stream'],
                          training_mode=cfg.get('training_mode', 'mixed'), geometry_online=cfg.get('geometry_online'))
    elif args.mode=='build-clips':
        from .carrier_c1_clip import build_clips
        build_clips(cfg)
    elif args.mode in ('probe','evaluate'):
        if not args.artifact or not args.report:
            parser.error('--artifact and --report are required')
        (probe if args.mode=='probe' else evaluate)(cfg,load(args.artifact),args.report,torch.device(args.device),
                                                   **({'zero_g3t': True} if args.zero_g3t else {}))
    else:
        train(cfg,args.smoke_steps,'latest' if args.resume == 'latest' else load(args.resume) if args.resume else None)


if __name__=='__main__':
    main()
