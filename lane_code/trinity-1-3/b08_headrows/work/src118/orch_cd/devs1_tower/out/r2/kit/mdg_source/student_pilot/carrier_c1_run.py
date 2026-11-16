"""C1 preparation, CPU dryrun, FSDP smoke/train/resume and native head probes.

This module never submits jobs or grants GPU admission. The parent supplies the
sealed source, inputs, independent review and allocation authorization.
"""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import random
import re
import resource
import shutil
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
from .p3_provenance import digest, file_pin, load, pinned, write, source_files, sha256
from . import carrier_c1_routing as routing


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


def validate(cfg):
    data.layout_settings(cfg)
    if 'skip_unsupervised_lm' in cfg and type(cfg['skip_unsupervised_lm']) is not bool:
        raise ValueError('skip_unsupervised_lm must be boolean')
    if cfg.get('schema') != 'carrier-c1-run-v1' or cfg.get('recipe') != recipe_for(cfg):
        raise ValueError('C1 requires its explicit fixed recipe')
    if cfg.get('carrier_placement') not in data.PLACEMENTS:
        raise ValueError('C1 requires an explicit carrier_placement')
    if cfg.get('init') != 'base' or cfg.get('parallel') != 'fsdp' or cfg.get('all_frames') is not True:
        raise ValueError('C1 starts from BASE with full LM FSDP and all-frame carriers')
    expected = {'pose'} if cfg.get('training_mode') == 'pose_only' else {'pose', 'vqa', 'pointing'}
    if cfg.get('training_mode') == 'final':
        expected = {'pose', 'vqa', 'pointing', 'routing'}
        if cfg.get('depth_fov_source') != 'pose_head':
            raise ValueError('Final mode feeds the pose-head FoV to depth and unprojection')
    if set(cfg.get('streams', {})) != expected:
        raise ValueError('Pinned streams must match training_mode exactly')
    if cfg.get('training_mode') == 'pose_only' and type(cfg.get('depth_enabled')) is not bool:
        raise ValueError('Pose-only arms must explicitly select optional depth')
    if 'frame_markers' in cfg and (type(cfg['frame_markers']) is not bool
                                   or (cfg['frame_markers'] and cfg.get('frame_layout') not in ('duplicate', 'paired'))):
        raise ValueError('frame_markers must be boolean and needs a one-viewpoint-per-group layout')
    if 'route_table' in cfg:
        validate_route_table(cfg['route_table'])
    if 'pose_lr_scale' in cfg and (type(cfg['pose_lr_scale']) not in (int, float) or not 0 < cfg['pose_lr_scale'] <= 1):
        raise ValueError('pose_lr_scale must be in (0, 1]')
    if 'exclude_sources' in cfg and (not isinstance(cfg['exclude_sources'], dict) or any(
            not isinstance(v, list) or any(not isinstance(t, str) or not t for t in v) for v in cfg['exclude_sources'].values())):
        raise ValueError('exclude_sources maps stream names to non-empty source-tag substrings')
    levers = {k for k in ('align', 'init_artifact', 'camera_overrides', 'gate_stop', 'frame_markers', 'route_table',
                          'exclude_qids', 'exclude_sources', 'pose_lr_scale')
              if k in cfg}
    if levers and cfg.get('training_mode') != 'final':
        raise ValueError('align/init_artifact/camera_overrides/gate_stop are final-mode levers')
    if cfg.get('align') is not None:
        from .c1r_align import validate as validate_align
        validate_align(cfg['align'])
        if cfg['align']['cam']['layer'] != 'final' or cfg['align'].get('patch') is not None:
            raise ValueError('Final mode aligns final-layer carrier states only, without a patch term')
    if cfg.get('init_artifact') is not None:
        validate_init(cfg['init_artifact'])
    overrides = cfg.get('camera_overrides', {})
    if (not isinstance(overrides, dict) or set(overrides) - {'weight_focal'}
            or any(type(v) not in (int, float) or not v >= 0 for v in overrides.values())):
        raise ValueError('camera_overrides may set nonnegative weight_focal only')
    if 'gate_stop' in cfg and type(cfg['gate_stop']) is not bool:
        raise ValueError('gate_stop must be boolean')


def warn(cfg, message):
    """Final mode records provenance/review mismatches instead of refusing (USER 11-08 1303Z)."""
    if cfg.get('training_mode') != 'final':
        raise ValueError(message)
    print(json.dumps({'warning': message}), flush=True)


def authenticate(cfg):
    seal = load(pinned(cfg['code']))
    root = Path(__file__).parent.parent
    actual = {str(p.relative_to(root)): sha256(p) for p in source_files([Path(__file__)])}
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
    split that contains the parent's and no parent held-out scene among its training scenes."""
    if stream_division == pose_division:
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


def prepare(cfg):
    """Authenticate existing databases once; never duplicate the A1 payload."""
    validate(cfg)
    commit = authenticate(cfg)
    receipts = {name: load(pinned(pin)) for name, pin in cfg['streams'].items()}
    pose = receipts['pose']
    final = cfg.get('training_mode') == 'final'
    benchmark = routing.load_exclusions(cfg.get('exclusions')) if final else set()
    held_qids = {k: set(v) for k, v in load(pinned(cfg['exclude_qids'])).items()} if cfg.get('exclude_qids') else {}
    held_sources = cfg.get('exclude_sources') or {}
    reported = routing.load_exclusions(cfg.get('report_exclusions')) if final else set()
    mix = None
    if pose.get('schema') == 'c1-pose-mix-v1':
        from . import c1_pose_mix
        if not final or not benchmark:
            raise ValueError('The composite pose stream is final-mode only and needs the exclusion list')
        mix, pose = c1_pose_mix.prepare(cfg['streams']['pose'], cfg['preparation_output'],
                                        benchmark, reported, excluded_row)
    prefix = paired_prefix(cfg, pose) if mix is None else None
    if prefix is not None:
        pose = prefix
    if ((mix is None and (pose.get('schema') != 'decoupled-v-preparation-v1' or pose.get('count') != 321152))
            or pose['settings']['anchors'] != list(range(1, 33))
            or pose['settings']['temporal_grouping'] != 'fused_pairs_all_frames'):
        raise ValueError('C1 requires the admitted 321152-row all-frame A1 preparation')
    division = pose['inputs']['division']
    model = load(pinned(pose['model']))
    from .students import get_student
    spec = get_student('qwen35')
    if (model.get('kind') != 'base' or model['base_identity'] != cfg['base_identity']
            or Path(model['root']).name != spec['snapshot'].name
            or model['files']['config.json'] != spec['config_sha256']):
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
        pinned(receipt['database'])
        with connect(receipt['database']) as conn:
            count, lo, hi = conn.execute('SELECT count(*), min(i), max(i) FROM rows').fetchone()
        if not count or receipt['count'] != count or lo != 0 or hi != count-1:
            raise ValueError('Database indices/count differ from the receipt')
        if cfg.get('frame_layout', 'spread') != 'spread':
            with connect(receipt['database']) as conn:
                for (row,) in conn.execute('SELECT row FROM rows ORDER BY i'):
                    data.layout_inputs(json.loads(row), *data.layout_settings(cfg), verify_partners=True)
        streams[name] = dict(receipt=cfg['streams'][name], database=receipt['database'], count=count,
                             source_count=count)
        if benchmark:
            # Pose rows are filtered here; every other stream must already be clean (refuse otherwise).
            selected, hits, overlap, routed, held = [], 0, 0, 0, 0
            with connect(receipt['database']) as conn:
                for index, row, target in conn.execute('SELECT i,row,target FROM rows ORDER BY i'):
                    row = json.loads(row)
                    if name == 'pose' and not dense_pose_row(row, json.loads(target)):
                        # 16-slot rows break per-frame carriers in duplicate/paired layouts.
                        continue
                    if name != 'pose' and held_row(row, name, held_qids, held_sources):
                        held += 1
                        continue
                    if name == 'vqa' and routed_type(row, cfg):
                        # A type that routes keeps only its routed traces; its direct answers would
                        # teach the opener decision a mix (route table, final mode).
                        routed += 1
                        continue
                    hit, seen = excluded_row(row, benchmark, reported, name)
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
    result = dict(schema='c1-preparation-v1', config_sha256=identity(cfg), trainer_commit=commit,
                  streams=streams, model=pose['model'], division=division,
                  camera=pose['settings']['camera'],
                  # A Stage-1 depth init fixes the point-depth architecture to the artifact's own settings.
                  depth=(load(pinned(cfg['depth_init']))['camera']['point_depth'] if cfg.get('depth_init')
                         else pose['settings']['camera']['point_depth']),
                  carrier_placement=cfg['carrier_placement'], training_mode=cfg.get('training_mode', 'mixed'),
                  depth_enabled=cfg.get('depth_enabled', True), recipe=cfg['recipe'])
    result.update({k: cfg[k] for k in ('frame_layout', 'frame_pair_gap_seconds', 'skip_unsupervised_lm',
                                       'depth_fov_source', 'depth_init', 'exclusions', 'report_exclusions') if k in cfg})
    write(Path(cfg['preparation_output'])/'receipt.json', result)
    return result


def prepared(cfg, admission=False):
    validate(cfg)
    commit = authenticate(cfg)
    receipt = load(pinned(cfg['preparation']))
    if receipt.get('config_sha256') != identity(cfg) or receipt.get('trainer_commit') != commit:
        # Config-only or code changes need no fresh prep when the prepared data is unchanged.
        warn(cfg, 'C1 preparation config/commit identity differs')
    if receipt.get('recipe') != cfg['recipe'] and cfg.get('training_mode') == 'final':
        # Mix/schedule changes do not change the prepared streams.
        warn(cfg, 'C1 preparation recipe differs; using the config recipe')
        receipt = {**receipt, 'recipe': cfg['recipe']}
    if receipt.get('carrier_placement') != cfg['carrier_placement'] and cfg.get('training_mode') == 'final':
        # The prepared streams do not depend on placement; the model takes the config's placement.
        warn(cfg, 'C1 preparation carrier_placement differs; using the config placement')
        receipt = {**receipt, 'carrier_placement': cfg['carrier_placement']}
    if cfg.get('training_mode') == 'final':
        # Freeze-time levers change no prepared stream: the config's init, teacher projector and
        # camera loss weights win over the receipt.
        receipt = {**receipt, 'align': cfg.get('align'), 'init_artifact': cfg.get('init_artifact'),
                   'frame_markers': cfg.get('frame_markers', False),
                   'camera': {**receipt['camera'], **cfg.get('camera_overrides', {})}}
    if (receipt.get('schema') != 'c1-preparation-v1'
            or {k: v['receipt'] for k, v in receipt['streams'].items()} != cfg['streams']
            or receipt.get('carrier_placement') != cfg['carrier_placement']
            or receipt.get('training_mode') != cfg.get('training_mode', 'mixed')
            or receipt.get('depth_enabled') != cfg.get('depth_enabled', True)
            or receipt.get('recipe') != cfg['recipe']):
        raise ValueError('C1 preparation differs from configuration/source')
    if (data.layout_settings(receipt) != data.layout_settings(cfg) or
            receipt.get('skip_unsupervised_lm') != cfg.get('skip_unsupervised_lm')
            or receipt.get('depth_fov_source') != cfg.get('depth_fov_source')
            or receipt.get('depth_init') != cfg.get('depth_init')):
        raise ValueError('C1 preparation frame layout/LM lever differs')
    for value in receipt['streams'].values():
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
    model = load(pinned(receipt['model']))
    if admission:
        review = load(pinned(cfg['admission'])) if cfg.get('admission') else {}
        if (review.get('verdict') != 'PASS' or not review.get('reviewer')
                or review.get('config_sha256') != identity(cfg) or review.get('preparation') != cfg['preparation']):
            warn(cfg, 'Parent must bind independent C1 admission')
    return receipt, model


def load_model(manifest, receipt, processor, verify_assets=True):
    from transformers import Qwen3_5ForConditionalGeneration
    from .camera_targets import carrier_id
    # Full base shards, unlike V-C, must be authenticated before LM loading.
    root = Path(manifest['root'])
    for name, sha in manifest['files'].items():
        if Path(name).name != name or (verify_assets and sha256(root/name) != sha):
            raise ValueError('Base checkpoint/processor asset changed')
    base = Qwen3_5ForConditionalGeneration.from_pretrained(root, local_files_only=True,
        trust_remote_code=False, dtype=torch.bfloat16, attn_implementation='sdpa')
    model = CarrierC1(base, receipt['camera'], receipt['depth'], carrier_id(processor.tokenizer),
                      receipt['carrier_placement'], receipt['training_mode'], receipt['depth_enabled'], receipt['recipe'],
                      receipt.get('skip_unsupervised_lm'), receipt.get('frame_layout', 'spread'),
                      receipt.get('depth_fov_source', 'private'))
    if receipt['training_mode'] == 'final':
        init = receipt.get('init_artifact')
        if init:
            # LM first: the routing openers then initialize from the warm-started rows.
            model.init_report = init_from_artifact(model, init, verify=verify_assets, part='lm')
        routing.init_routing_embeddings(model, processor._routing_tokens)
        if receipt.get('depth_init'):
            from .carrier_c1 import load_depth_stage1
            model.depth_init_report = load_depth_stage1(model, receipt['depth_init'], verify=verify_assets)
        if receipt.get('align'):
            # C1-r teacher package: the 2H projector feeds the pose head (attach before FSDP/optimizer).
            from . import c1r_align
            c1r_align.attach(model, receipt['align'], training=True)
        if init:
            model.init_report.update(init_from_artifact(model, init, verify=verify_assets, part='heads'))
    return model


INIT_KEYS = {'artifact', 'lm', 'heads'}


def validate_init(spec):
    if (not isinstance(spec, dict) or set(spec) != INIT_KEYS or spec['lm'] not in ('full', 'base')
            or not isinstance(spec['heads'], list) or len(set(spec['heads'])) != len(spec['heads'])
            or any(h not in ('pose', 'frame_embeddings') for h in spec['heads'])
            or (spec['lm'] == 'base' and not spec['heads'])
            or not isinstance(spec['artifact'], dict) or set(spec['artifact']) != {'path', 'sha256'}):
        # heads [] with lm full = warm LM with cold (planned-init) heads; lm base with heads = E4 graft.
        raise ValueError('init_artifact needs {artifact pin, lm full|base, heads ⊆ [pose, frame_embeddings]}')
    return spec


def init_mirror(artifact_pin):
    """Node-local copy of the init milestone staged and hash-verified by the kit (C1_INIT_LOCAL)."""
    root = os.environ.get('C1_INIT_LOCAL')
    if not root:
        return None
    local = Path(root)/artifact_pin['sha256'][:16]
    return local if (local/'.verified').is_file() else None


def init_from_artifact(model, spec, verify=True, part='heads'):
    """Warm-start from a C1-family milestone export (carrier-c1-artifact-v1).

    part 'lm': lm 'full' replaces every base tensor (LM and frozen vision) with the export;
    'base' keeps the base model and grafts heads only (the E4 fallback). part 'heads': the
    listed head modules load by exact name and shape; every other head (depth) keeps its
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
    report = dict(artifact=spec['artifact'], step=artifact.get('step'), lm=spec['lm'], heads=sorted(spec['heads']))
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
    live = model.auxiliary_heads.state_dict()
    wanted = {k for k in live if keep(k)}
    selected = {k: v for k, v in state.items() if keep(k)}
    # A pose_only donor (C1-a, C1-r) trained with zero gravity and scale weights, so it never built
    # those branches; the final-mode head has them, and they keep their planned init.
    optional = (('pose.head.gravity_branch.', 'pose.head.scale_branch.', 'pose.head.scale_token')
                if artifact.get('training_mode') == 'pose_only' else ())
    absent = {k for k in wanted - set(selected) if optional and k.startswith(optional)}
    wanted -= absent
    report['projector'] = 'planned_init' if fresh else 'loaded'
    report['planned_init'] = sorted(absent)
    if set(selected) != wanted:
        raise ValueError(f'init heads differ: missing {sorted(wanted - set(selected))[:5]}, '
                         f'extra {sorted(set(selected) - wanted)[:5]}')
    for name, value in selected.items():
        if tuple(value.shape) != tuple(live[name].shape):
            raise ValueError('init head tensor shape differs: ' + name)
    result = model.auxiliary_heads.load_state_dict({k: v.to(live[k].dtype) for k, v in selected.items()}, strict=False)
    if result.unexpected_keys or set(result.missing_keys) != set(live) - wanted:
        raise ValueError('init head load touched modules outside the selected heads')
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
        for name, value in load_file(str(directory/item['name']), device='cpu').items():
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
        self.connections = {k: connect(v['database']) for k, v in receipt['streams'].items() if v.get('kind') != 'mix'}
        self.processor = processor
        self.placement = receipt.get('carrier_placement', data.C1_A)
        self.mode = receipt.get('training_mode', 'mixed')
        self.layout, self.gap = data.layout_settings(receipt)
        self.indices = {k: load(pinned(v['indices'])) for k, v in receipt['streams'].items() if 'indices' in v}
        self.counts = {k: v['count'] for k, v in receipt['streams'].items()}
        self.mixes = {}
        for name, value in receipt['streams'].items():
            if value.get('kind') == 'mix':
                from .c1_pose_mix import PoseMix
                self.mixes[name] = PoseMix(value, processor, self.placement, self.mode, self.layout, self.gap,
                                           receipt['depth']['num_points_per_frame'])

    def count(self, stream):
        return self.counts[stream]

    def row(self, stream, index):
        if stream in self.indices:
            index = self.indices[stream][index]
        row = self.connections[stream].execute('SELECT row,target FROM rows WHERE i=?',(index,)).fetchone()
        if row is None:
            raise ValueError('Missing planned C1 row')
        return json.loads(row[0]), json.loads(row[1])

    def get(self, stream, index):
        if stream in self.mixes:
            return self.mixes[stream].get(index)
        row, target = self.row(stream, index)
        if stream == 'routing':
            batch, audit = routing.encode(self.processor, row, self.placement, self.mode, self.layout, self.gap)
            return batch, None, audit
        if self.mode == 'pose_only' and not dense_pose_row(row, target):
            raise ValueError('Pose-only index selected a non-dense row')
        options = {} if self.layout == 'spread' else dict(frame_layout=self.layout, frame_pair_gap_seconds=self.gap)
        batch, targets, audit = data.encode(self.processor, row, target, stream, self.placement, self.mode, **options)
        if self.mode == 'final' and stream in ('vqa', 'pointing'):
            # Logging-only token tags: coordinate/format/null for pointing, answer/trace for VQA.
            tokenizer = self.processor.tokenizer
            batch['aux_segments'] = data.segment_tags(batch['labels'][:, 1:], stream,
                                                      lambda i: tokenizer.decode([i]))
            batch['aux_segments'] = torch.cat((torch.full_like(batch['aux_segments'][:, :1], -1),
                                               batch['aux_segments']), dim=1)
        return batch, targets, audit

    def close(self):
        for conn in self.connections.values():
            conn.close()
        for mix in self.mixes.values():
            mix.close()


def move(value, device):
    return None if value is None else {k: v.to(device) for k, v in value.items()}


def norm(parameters):
    return float(torch.sqrt(sum(p.grad.float().square().sum() for p in parameters if p.grad is not None)))


def wrap_model(model, device, mixed_precision=True):
    offload = os.environ.get('C1_FSDP_CPU_OFFLOAD', '0')
    if offload not in ('0', '1'):
        raise ValueError('C1_FSDP_CPU_OFFLOAD must be 0 or 1')
    wrapped=full_ft.wrap_full_model(model,list(model.auxiliary_heads.parameters()),dist.group.WORLD,
                                    device,mixed_precision=mixed_precision, cpu_offload=offload == '1')
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
    """Final mode adds the head-opener tokens to the base tokenizer (deterministic ids)."""
    processor = processor_for(manifest['root'])
    if receipt.get('training_mode') == 'final':
        routing.add_routing_tokens(processor)
        # Per-group `Frame k: ` markers (config switch, off by default); every encode path reads it.
        processor.tokenizer._c1_frame_markers = bool(receipt.get('frame_markers', False))
    return processor


def own_values(model, rows, batch, audit, index, decision, device):
    """Scheduled sampling: replace GT routed values with the model's own head values.

    `decision` = (depth_own, pose_own) is identical on every rank (rank zero broadcasts
    it), so every rank runs the no-grad readout forward in the same microstep. A row
    that cannot take own values (closed gate for its heads, missing GT pose for a
    hybrid) or whose re-render refuses keeps its GT values; the audit records why.
    """
    if not any(decision):
        return batch, audit
    row, _ = rows.row('routing', index)
    try:
        queries = routing.depth_queries(row['routing'])
        uv, slots = routing.query_tensor(queries)
        query_error = None
    except (routing.RenderError, KeyError, ValueError) as exc:
        # Every rank must still join the collective readout forward.
        queries, slots, query_error = [], [], exc
        uv = torch.full((32, 1, 2), 500.)
    with torch.no_grad():
        readout = model(move(routing.prefix_batch(batch), device), {'uv': uv.to(device)}, stream='readout')
    try:
        if query_error is not None:
            raise routing.RenderError(f'depth queries: {query_error}')
        geometry, source = routing.row_geometry(row['routing'], readout, queries, slots, *decision)
        if geometry is None:
            return batch, {**audit, 'own_skip': source}
        target, spans, segments = routing.rerender(row['routing'], geometry)
        return routing.encode_own(rows.processor, row, batch, target, spans, segments, source)
    except (routing.RenderError, ValueError) as exc:
        return batch, {**audit, 'values': 'gt_fallback', 'own_refusal': str(exc)[:200]}


def replay_gates(output, start_step, gates):
    """Rebuild the gate EMAs from the run's metrics files up to the resume step."""
    by_step = {}
    for path in sorted(Path(output).glob('metrics_*.jsonl')):
        with path.open() as handle:
            for line in handle:
                record = json.loads(line)
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
    if tokens > MAX_TOKENS:
        raise ValueError(f'{tokens} tokens exceed {MAX_TOKENS}')
    positions = batch['aux_camera_positions']
    valid = positions >= 0
    if positions.shape != (1, 32) or torch.any(valid != (valid.long().cumprod(dim=1) > 0)):
        raise ValueError('Carrier positions must be a prefix of 32 slots')
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
                decisions[microstep] = torch.tensor(gates.decide(step, microstep), dtype=torch.int32)
        if distributed:
            dist.broadcast(decisions, src=0)
    skipped, stream_sums, stream_counts = [], {}, {}
    for microstep, (stream, indices) in enumerate(plan):
        if device.type == 'cuda':
            torch.cuda.reset_peak_memory_stats(device)
        start = time.perf_counter()
        fetched = fetch(rows, stream, indices[rank], unwrapped, device=device, distributed=distributed)
        waiting += time.perf_counter()-start
        if getattr(unwrapped, 'training_mode', None) == 'final':
            SKIPPED['total'] += 1
            if fetched is None:
                # Every rank skips this microstep together (shared decision in fetch).
                SKIPPED['skipped'] += 1
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
        result = model(batch, targets, stream=stream)
        phases = dict(after_forward=memory_stats(device))
        if not torch.isfinite(result['loss']):
            raise ValueError('Nonfinite C1 loss')
        (result['loss']/len(plan)).backward()
        phases['after_backward'] = memory_stats(device)
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
                           **({k: audit[k] for k in ('qid', 'values', 'own_refusal', 'own_skip', 'trained_tokens')
                               if k in audit} if stream == 'routing' else {}),
                           **({'segments': result['metrics']['segments']}
                              if 'segments' in result.get('metrics', {}) else {}),
                           **({'pose_parts': result['metrics']['pose_parts']}
                              if 'pose_parts' in result.get('metrics', {}) else {}),
                           **({k: audit[k] for k in ('source', 'dataset') if k in audit}
                              if stream == 'pose' and isinstance(audit, dict) else {}),
                           grid=batch['video_grid_thw'].tolist(), carriers=int((batch['aux_camera_positions']>=0).sum())))
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
    branch=unwrapped.auxiliary_heads.pose.head.pose_branch.fc2.weight
    pose_gradient=branch.grad
    head_gradients=dict(rotation_weight_norm=float(pose_gradient[3:7].norm()) if pose_gradient is not None else 0.,
                        fov_weight_norm=float(pose_gradient[7:9].norm()) if pose_gradient is not None else 0.,
                        carrier_embedding_norm=norm([unwrapped.auxiliary_heads.pose.tokens]))
    if not all(np.isfinite(v) and v>0 for v in gradients.values()):
        # Private depth can legitimately be absent from a sampled pose batch.
        # A shared microstep skip can leave a group without a gradient this update.
        if not all(np.isfinite(v) and (v>0 or k=='encoder_copy' or skipped) for k,v in gradients.items()):
            raise ValueError('C1 gradient flow failed')
    base = [p for n,p in full_ft.named_trainable(model) if not n.startswith('auxiliary_heads.')]
    carriers, heads = clip_groups(unwrapped, attached)
    clip_norms = {}
    if distributed:
        full_ft.clip_sharded(base,RECIPE['clip_norm'],dist.group.WORLD)
        if carriers:
            # Final mode: carrier/frame embeddings clip apart from the heads (eps-scale tokens).
            clip_norms['carriers'] = float(torch.nn.utils.clip_grad_norm_(carriers,RECIPE['clip_norm']))
        clip_norms['heads'] = float(torch.nn.utils.clip_grad_norm_(heads,RECIPE['clip_norm']))
    elif carriers:
        clip_norms['carriers'] = float(torch.nn.utils.clip_grad_norm_(carriers,RECIPE['clip_norm']))
        rest = [p for p in model.parameters() if p.requires_grad and all(p is not c for c in carriers)]
        clip_norms['rest'] = float(torch.nn.utils.clip_grad_norm_(rest,RECIPE['clip_norm']))
    else:
        torch.nn.utils.clip_grad_norm_(model.parameters(),RECIPE['clip_norm'])
    head_gradients['clip_group_norms'] = clip_norms
    for group in optimizer.param_groups:
        group['lr'] = learning_rate(step, {**recipe,'learning_rate':group['initial_lr']})
    optimizer.step()
    after_optimizer = memory_stats(device)
    if device.type == 'cuda':
        torch.cuda.synchronize(device)
    return dict(step=step, wall_seconds=time.perf_counter()-started, data_seconds=waiting,
                skipped_microsteps=skipped, skip_totals=dict(SKIPPED),
                component_normalization='components: sum over microsteps of each row-mean loss / len(plan); '
                                        'stream_means: row-mean loss of each stream over its own microsteps',
                stream_means={k: stream_sums[k]/stream_counts[k] for k in stream_sums},
                components=components, head_metrics=head_metrics,
                gates=None if gates is None else dict(gates.state(step), decisions=decisions.tolist()), gradient_norms=gradients, head_gradients=head_gradients, shapes=shapes,
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
    optimizer = torch.optim.AdamW(parameter_groups(model),weight_decay=RECIPE['weight_decay'])
    rows = Rows(receipt,processor)
    counts = {k:v['count'] for k,v in receipt['streams'].items()}
    recipe = recipe_for(cfg)
    plan = next(data.mixed_indices(counts,1,training_mode=cfg.get('training_mode', 'mixed'),
                                   mix=recipe['mix'],world=recipe['world_size']))
    rank_shapes = []
    try:
        # Encode each rank's actual first row in every stream; no synthetic admission.
        for rank in range(8):
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


def complete_states(output, bound):
    """Find this run's complete states without reading the large shard payloads.

    Restoration still authenticates every payload hash. Partial markers, absent
    or truncated files, foreign bindings and symlinked directories are ignored.
    """
    output = Path(output)
    if load(output/'binding.json') != bound:
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
            # Rotation may remove only the exact state tree, never extra artifacts.
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


def bind_output(output, bound, *, resume=False):
    """Reuse an identical early-crash binding only before any complete state."""
    output = Path(output)
    binding = output/'binding.json'
    if resume or binding.exists():
        if load(binding) != bound:
            raise ValueError('Resume output belongs to another run')
        if not resume and complete_states(output, bound):
            raise ValueError('Complete C1 resume state exists; resume instead of starting fresh')
    else:
        write(binding, bound)


def latest_resume(output, bound):
    states = complete_states(output, bound)
    if not states:
        raise ValueError('No complete C1 resume state')
    return file_pin(states[-1])


def checkpoint(directory, model, optimizer, bound, step, *, rotate=False):
    """Immutable rank-sharded state; complete.json is written last, after a barrier."""
    rank, world = dist.get_rank(),dist.get_world_size()
    directory = Path(directory)
    if rotate:
        # A retry at the same step must leave an interrupted save untouched.
        names = [str(directory.with_name(f'checkpoint_{step:06d}_{uuid.uuid4().hex}')) if rank == 0 else None]
        dist.broadcast_object_list(names, src=0)
        directory = Path(names[0])
        if rank == 0 and load(directory.parent/'binding.json') != bound:
            raise ValueError('Resume output belongs to another run')
    if rank==0:
        directory.mkdir(parents=True,exist_ok=False)
    dist.barrier()
    named = full_ft.named_trainable(model)
    layout = digest(full_ft.shard_layout(named))
    pins = full_ft.write_rank_shard(directory,rank,named,optimizer,layout)
    rng=rng_state()
    # weights_only checkpoints store NumPy's MT19937 array as a tensor.
    numpy_state=rng['numpy']
    rng['numpy']=(numpy_state[0],torch.from_numpy(numpy_state[1].astype(np.int64)),*numpy_state[2:])
    rng_pin = full_ft._write_payload(directory/f'rng{rank:03d}.pt',rng)
    payload = dict(rank=rank,layout=layout,pins=pins,rng=rng_pin)
    gathered = [None]*world; dist.all_gather_object(gathered,payload)
    dist.barrier()  # Every rank has finished and fsynced its payloads.
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
        write(directory/'complete.json',dict(schema='c1-checkpoint-v1',binding=bound,step=step,
                                             layouts=[g['layout'] for g in gathered],files=files))
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
            # USER-authorized deletion applies only to this run's complete states.
            for marker in states[:-2]:
                shutil.rmtree(marker.parent)
    dist.barrier()
    return file_pin(directory/'complete.json')


def restore(pin, model, optimizer, bound):
    manifest = load(pinned(pin)); directory = Path(pin['path']).parent
    if manifest.get('schema')!='c1-checkpoint-v1' or manifest['binding']!=bound:
        raise ValueError('C1 resume binding differs')
    rank = dist.get_rank()
    named=full_ft.named_trainable(model); layout=digest(full_ft.shard_layout(named))
    if layout!=manifest['layouts'][rank]:
        raise ValueError('C1 resume shard layout differs')
    full_ft.read_rank_shard(directory,rank,manifest['files'],named,optimizer,layout,dist.group.WORLD)
    rng=full_ft._verified_load(directory/f'rng{rank:03d}.pt',manifest['files'][f'rng{rank:03d}.pt'],'RNG')
    numpy_state=rng['numpy']
    rng['numpy']=(numpy_state[0],numpy_state[1].numpy().astype(np.uint32),*numpy_state[2:])
    restore_rng(rng)
    return manifest['step']


def export(directory, wrapped, model, cfg, step):
    from .fsdp_training import publication_state
    state = publication_state(wrapped)
    if dist.get_rank()==0:
        directory=Path(directory); directory.mkdir(parents=True,exist_ok=False)
        names=[full_ft.clean_name(n) for n,_ in full_ft.base_parameters(model)]
        weights = full_ft.save_export(full_ft.export_tensors(state,names),directory/'full_weights',
                                     {'base_identity':cfg['base_identity']},model.full_ft_report)
        heads = {n.removeprefix('auxiliary_heads.'):v for n,v in state.items() if n.startswith('auxiliary_heads.')}
        pin=full_ft._write_payload(directory/'heads.pt',heads)
        write(directory/'artifact.json',dict(schema='carrier-c1-artifact-v1',step=step,
            config_sha256=identity(cfg),base_identity=cfg['base_identity'],anchors=list(range(1,33)),
            placement=model.carrier_placement, training_mode=model.training_mode, pose_backing='lm_final_norm',
            frame_layout=model.frame_layout,
            carrier_position_policy=model.carrier_position_policy,
            depth_backing='private_vit' if hasattr(model.auxiliary_heads, 'depth') else None,
            full_weights=file_pin(directory/'full_weights/full_weights.json'),
            heads={'path':str((directory/'heads.pt').resolve()),'sha256':pin['sha256']}))
    dist.barrier()


def existing_export(directory, cfg, step):
    """A timed resume may replay an already exported step; preserve that artifact."""
    directory = Path(directory)
    if not directory.exists():
        return False
    artifact = load(directory/'artifact.json')  # Incomplete exports fail closed.
    if (artifact.get('schema') != 'carrier-c1-artifact-v1' or artifact.get('step') != step
            or artifact.get('config_sha256') != identity(cfg)):
        raise ValueError('Existing milestone belongs to another C1 run or step')
    # Authenticate the small manifest and heads; do not reread all LM weights.
    for name in ('full_weights', 'heads'):
        path = pinned(artifact[name])
        if not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError('Existing milestone payload is outside its directory')
    return True


def run_steps(model, wrapped, optimizer, rows, counts, output, cfg, bound, device,
              rank=0, start_step=0, smoke_steps=None, started=None, stop=None, distributed=True):
    """Shared native loop; CPU smoke exercises it without CUDA or collectives."""
    started=time.monotonic() if started is None else started
    stop=[False] if stop is None else stop
    world=dist.get_world_size() if distributed else 1
    recipe = recipe_for(cfg)
    steps=start_step+(smoke_steps or (recipe['steps']-start_step))
    if start_step>=steps:
        raise ValueError('Completed C1 schedules cannot resume')
    timing = cfg.get('schedule', {})
    if not smoke_steps and cfg.get('training_mode') == 'pose_only':
        steps = start_step + capped_steps(timing, recipe['resume_every_seconds'], start_step=start_step,
                                         elapsed_seconds=time.monotonic()-started)
    output=Path(output);attempt=os.environ.get('SLURM_JOB_ID','cpu')
    measured=[]; step=start_step; gate_stop=False
    gates=None
    if recipe.get('scheduled_sampling'):
        gates=routing.Gates(recipe['scheduled_sampling'],getattr(model,'depth_stage1',False))
        state=[replay_gates(cfg['output'],start_step,gates).ema if rank==0 else None]
        if distributed:
            dist.broadcast_object_list(state,src=0)
        gates.ema=dict(state[0])
    last_save=time.monotonic()
    request=torch.tensor([int(stop[0] or steps==start_step)],device=device)
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
        checkpoint(output/f'checkpoint_{start_step:06d}',wrapped,optimizer,bound,start_step,rotate=True)
    for step,plan in enumerate(data.mixed_indices(counts,steps,start_step=start_step,
                              training_mode=cfg.get('training_mode', 'mixed'),
                              mix=recipe['mix'],world=recipe['world_size']),start_step+1):
        info,_=optimize_step(wrapped,optimizer,rows,plan,rank,device,step,distributed,gates)
        if gates is not None:
            gates.update(info['head_metrics'])
        due=torch.tensor([int(time.monotonic()-last_save >= recipe['resume_every_seconds'])],device=device)
        if distributed:
            dist.all_reduce(due,op=dist.ReduceOp.MAX)
        pending = timing.get('checkpoint_seconds',0.) if due.item() else 0.
        pending += timing.get('export_seconds',0.) if step in recipe['milestones'] else 0.
        next_cost = max(info['wall_seconds'],timing.get('p95_step_seconds',0.)) + timing.get('checkpoint_seconds',0.)
        next_cost += timing.get('export_seconds',0.) if step+1 in recipe['milestones'] else 0.
        request=torch.tensor([int(stop[0] or time.monotonic()-started+pending+next_cost >=
            recipe['wall_seconds']-recipe['stop_before_seconds'])],device=device)
        if distributed:
            dist.all_reduce(request,op=dist.ReduceOp.MAX)
        gate_stop=not smoke_steps and step==400 and start_step<400 and cfg.get('gate_stop', True)
        stopping=bool(request.item()) or step==steps or gate_stop
        info['checkpoint_seconds']=info['export_seconds']=0.
        if not smoke_steps and (due.item() or stopping):
            tick=time.perf_counter()
            checkpoint(output/f'checkpoint_{step:06d}',wrapped,optimizer,bound,step,rotate=True)
            info['checkpoint_seconds']=time.perf_counter()-tick
            last_save=time.monotonic()
        if not smoke_steps and step in recipe['milestones']:
            tick=time.perf_counter()
            reused = [existing_export(output/f'm{step}', cfg, step) if rank == 0 else None]
            if distributed:
                dist.broadcast_object_list(reused, src=0)
            if not reused[0]:
                export(output/f'm{step}',wrapped,model,cfg,step)
            info['export_reused'] = reused[0]
            info['export_seconds']=time.perf_counter()-tick
        gathered=[None]*world
        if distributed:
            dist.all_gather_object(gathered,info)
        else:
            gathered[0]=info
        if rank==0:
            measured.append(gathered)
            with (output/f'metrics_{attempt}.jsonl').open('a') as handle:
                handle.write(json.dumps(dict(step=step,ranks=gathered))+'\n')
        if stopping:
            break
    report=dict(schema='c1-smoke-v1' if smoke_steps else 'c1-run-v1',status='PASS',
        first_step=start_step+1,last_step=step,steps=measured,elapsed_seconds=time.monotonic()-started,
        stopped_for_resume=not bool(smoke_steps) and step<recipe['steps'],world_size=world,
        gpu_fit_measured=device.type=='cuda' and distributed)
    report['stop_reason']='m400_gate' if gate_stop else 'budget_or_signal' if bool(request.item()) or budget_stop else 'schedule'
    if rank==0:
        write(output/('smoke.json' if smoke_steps else f'run_{attempt}.json'),report)
    return report


EXPORT_BINDING_KEYS = {'config_sha256', 'preparation', 'trainer_commit', 'world_size'}


def check_export_binding(export_binding, bound):
    """An export leg restores another trainer build's state: same world and preparation, its own binding."""
    if (not isinstance(export_binding, dict) or set(export_binding) != EXPORT_BINDING_KEYS
            or export_binding['world_size'] != bound['world_size']
            or export_binding['preparation'] != bound['preparation']):
        raise ValueError('Export binding must name the run state at this world size and preparation')
    return export_binding


def export_resume_state(output, wrapped, model, cfg, step, rank, distributed=True):
    """Publish a restored resume state as the milestone-format artifact m<step> (the 'x' leg)."""
    directory = Path(output)/f'm{step}'
    reused = [existing_export(directory, cfg, step) if rank == 0 else None]
    if distributed:
        dist.broadcast_object_list(reused, src=0)
    if not reused[0]:
        export(directory, wrapped, model, cfg, step)
    return directory, bool(reused[0])


def train(cfg, smoke_steps=None, resume_pin=None, export_binding=None):
    validate(cfg)
    if smoke_steps is not None and (type(smoke_steps)!=int or not 1<=smoke_steps<=10 or resume_pin):
        raise ValueError('Smoke needs 1..10 steps and cannot resume')
    export_only = export_binding is not None
    if export_only and (smoke_steps is not None or not resume_pin):
        raise ValueError('An export leg restores a resume state and trains no step')
    world_size=recipe_for(cfg)['world_size']
    if not torch.cuda.is_available() or int(os.environ.get('WORLD_SIZE','0'))!=world_size:
        raise ValueError('C1 training requires a parent-authorized '
                         + ('eight' if world_size == 8 else str(world_size)) + '-GPU allocation')
    rank=int(os.environ['RANK']); local=int(os.environ['LOCAL_RANK'])
    torch.cuda.set_device(local); device=torch.device('cuda',local)
    import datetime
    # Training collectives fail fast (15 min). Only the startup barriers and broadcasts, while
    # rank 0 hashes and loads assets, may wait longer (a separate gloo group, 60 min).
    dist.init_process_group('nccl', timeout=datetime.timedelta(minutes=15))
    startup=dist.new_group(backend='gloo', timeout=datetime.timedelta(minutes=60))
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
    if (authorization.get('config_sha256')!=identity(cfg) or authorization.get('new_gpus')!=world_size
            or str(authorization.get('job_id'))!=os.environ.get('SLURM_JOB_ID')
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
    model.train()  # HF decoder checkpointing requires training mode; vision stays eval.
    wrapped=wrap_model(model,device)
    optimizer=torch.optim.AdamW(parameter_groups(wrapped,inherited=set(getattr(model,'inherited_head_params',())),
                                                 pose_lr_scale=cfg.get('pose_lr_scale', 1.0)),
                                weight_decay=RECIPE['weight_decay'])
    bound=dict(config_sha256=identity(cfg),preparation=cfg['preparation'],trainer_commit=commit,world_size=world_size)
    restore_bound = check_export_binding(export_binding, bound) if export_only else bound
    if resume_pin == 'latest':
        pins = [latest_resume(cfg['output'], restore_bound) if rank == 0 else None]
        dist.broadcast_object_list(pins, src=0)
        resume_pin = pins[0]
    start_step=restore(resume_pin,wrapped,optimizer,restore_bound) if resume_pin else 0
    if start_step>=recipe_for(cfg)['steps'] and not export_only:
        raise ValueError('Completed C1 schedules cannot resume')
    if start_step>=400 and not smoke_steps and cfg.get('gate_stop', True):
        milestone_gate(cfg)
    output=Path(cfg['output'])
    if smoke_steps:
        output=output/'smoke'/os.environ['SLURM_JOB_ID']
    error=None
    try:
        rows=Rows(receipt,processor)
    except Exception as exc:
        rows,error=None,f'{type(exc).__name__}: {exc}'
    agree(startup, error)
    counts={k:v['count'] for k,v in receipt['streams'].items()}
    stop=[False]
    previous=signal.signal(signal.SIGUSR1,lambda *_:stop.__setitem__(0,True))
    attempt=os.environ['SLURM_JOB_ID']
    lock=run_lock(output,rank); held=False
    try:
        error=None
        try:
            lock.__enter__(); held=True
            if rank==0:
                if not smoke_steps and not export_only:
                    bind_output(output, bound, resume=bool(resume_pin))
                write(output/f'attempt_{attempt}.json',dict(binding=bound,resume=resume_pin,first_step=start_step+1,
                      network=network,init=getattr(model,'init_report',None),export_of=export_binding))
        except Exception as exc:
            error=f'{type(exc).__name__}: {exc}'
        # A rank-0 lock or binding refusal must stop every rank, never leave them in a barrier.
        agree(startup, error)
        dist.barrier(); torch.cuda.reset_peak_memory_stats(device)
        if export_only:
            directory, reused = export_resume_state(output, wrapped, model, cfg, start_step, rank)
            if rank==0:
                write(output/f'export_{attempt}.json', dict(step=start_step, resume=resume_pin, binding=restore_bound,
                      reused=reused, artifact=file_pin(directory/'artifact.json')))
            return
        run_or_exit(run_steps,model,wrapped,optimizer,rows,counts,output,cfg,bound,device,rank,start_step,
                    smoke_steps,started,stop,distributed=True)
    finally:
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
    if artifact.get('schema')!='carrier-c1-artifact-v1' or artifact['pose_backing']!='lm_final_norm':
        raise ValueError('Not a C1 artifact')
    if (artifact.get('placement') != model.carrier_placement or artifact.get('training_mode') != model.training_mode
            or artifact.get('frame_layout', 'spread') != model.frame_layout
            or artifact.get('carrier_position_policy', 'native_v1') != model.carrier_position_policy
            or (artifact.get('depth_backing') is not None) != hasattr(model.auxiliary_heads, 'depth')):
        raise ValueError('Artifact placement/training mode/position policy/depth differs')
    for _,p in full_ft.base_parameters(model):
        p.data=p.data.to(torch.bfloat16)
    full_ft.load_export(model,Path(pinned(artifact['full_weights'])).parent)
    state=torch.load(pinned(artifact['heads']),map_location='cpu',weights_only=True)
    model.auxiliary_heads.load_state_dict(state,strict=True)
    return artifact


def inference(cfg, artifact_pin, device):
    receipt,manifest=prepared(cfg,admission=True)
    processor=processor_for_receipt(manifest,receipt)
    if device.type=='cuda':
        auth=load(pinned(cfg['authorization'])) if cfg.get('authorization') else {}
        if (auth.get('config_sha256')!=identity(cfg) or auth.get('new_gpus')!=1
                or str(auth.get('job_id'))!=os.environ.get('SLURM_JOB_ID') or auth.get('verdict')!='GO'):
            warn(cfg,'Parent must authorize this exact readout allocation')
    model=load_model(manifest,receipt,processor)
    artifact=load_artifact(model,artifact_pin)
    if artifact['base_identity']!=cfg['base_identity']:
        raise ValueError('Readout artifact has another base model')
    if artifact['config_sha256']!=identity(cfg):
        warn(cfg,'Readout artifact has another C1 config identity')
    model.to(device).eval().requires_grad_(False)
    return model,processor,receipt,artifact


def probe(cfg, artifact_pin, report_path, device=torch.device('cpu')):
    model,processor,receipt,artifact=inference(cfg,artifact_pin,device)
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
    write(report_path,report)
    return report


def evaluate(cfg, artifact_pin, report_path, device=torch.device('cpu')):
    """Always score sparse anchors; add contiguous clips when their pin exists."""
    import gzip
    from .all_frame_bank import read_bank
    from .all_frame_readout import evaluate as score
    from .compact_label_bank import frame_set_sha256
    from .carrier_c1_clip import check_clips, pose_vectors_to_c2w, trajectory_metrics, summarize
    model,processor,receipt,artifact=inference(cfg,artifact_pin,device)
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
                             frame_pair_gap_seconds=cfg.get('frame_pair_gap_seconds'))
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
                             frame_pair_gap_seconds=cfg.get('frame_pair_gap_seconds'))
        prediction = pose_vectors_to_c2w(model.pose_readout(move(batch, device)))
        measurements.append(dict(dataset=clip['dataset'], scene=clip['scene'], recording_id=clip['recording_id'],
                                 **trajectory_metrics(prediction, clip['gt_c2w'])))
    report=dict(schema='c1-readout-v2',artifact=artifact_pin,step=artifact['step'],bank=held['bank'],detail=result,
                config_sha256=identity(cfg), readout_sha256=readout_identity(cfg), contiguous_clips=clip_pin,
                contiguous_clip=summarize(measurements) if clip_pin is not None else None,
                contiguous_clip_pending=clip_pin is None, pose_gate_threshold_deg=39.,
                pointing_gate_pending=cfg.get('training_mode') != 'pose_only',
                vsi500_gate_pending=cfg.get('training_mode') != 'pose_only')
    write(report_path,report)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['prepare','dryrun','train','build-stream','build-clips','probe','evaluate'])
    parser.add_argument('--config',required=True);parser.add_argument('--report')
    parser.add_argument('--smoke-steps',type=int);parser.add_argument('--resume',help='Pin JSON path, or latest')
    parser.add_argument('--artifact');parser.add_argument('--device',default='cpu',choices=['cpu','cuda:0'])
    args=parser.parse_args();cfg=load(args.config)
    if args.mode=='prepare':
        prepare(cfg)
    elif args.mode=='dryrun':
        if not args.report:
            parser.error('--report is required')
        dryrun(cfg,args.report)
    elif args.mode=='build-stream':
        data.build_stream(cfg['source'],cfg['division'],cfg['output'],cfg['stream'])
    elif args.mode=='build-clips':
        from .carrier_c1_clip import build_clips
        build_clips(cfg)
    elif args.mode in ('probe','evaluate'):
        if not args.artifact or not args.report:
            parser.error('--artifact and --report are required')
        (probe if args.mode=='probe' else evaluate)(cfg,load(args.artifact),args.report,torch.device(args.device))
    else:
        train(cfg,args.smoke_steps,'latest' if args.resume == 'latest' else load(args.resume) if args.resume else None)


if __name__=='__main__':
    main()
