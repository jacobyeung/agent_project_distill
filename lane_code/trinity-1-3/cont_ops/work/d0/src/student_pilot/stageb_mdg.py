"""Opt-in mask decoder on the current C1 language model's detached cache states."""
from contextlib import contextmanager
import json
import math
from pathlib import Path
import re

import torch
from torch import distributed as dist

from .p3_provenance import digest, file_pin, load, pinned, write


DEFAULTS = dict(weight=1., lr_scale=1., label_chunk=8, max_visible=24, absent_share=.30,
                lora_rank=0, lora_lr=1e-4)
REQUIRED = {'clips_jsonl', 'frame_root', 'rasters', 'confusers', 'vocab', 'exclude_scenes', 'stem_weights'}


def settings(block):
    if not isinstance(block, dict) or REQUIRED - set(block) or set(block) - REQUIRED - set(DEFAULTS) - {'init_artifact'}:
        raise ValueError('mdg requires its data paths and only the documented stage-B settings')
    result = {**DEFAULTS, **block}
    if type(result['lora_rank']) is not int or result['lora_rank'] < 0:
        raise ValueError('Stage-B lora_rank must be a nonnegative integer')
    for key in ('weight', 'lr_scale', 'lora_lr'):
        if type(result[key]) not in (int, float) or not math.isfinite(result[key]) or result[key] <= 0:
            raise ValueError(f'mdg {key} must be finite and positive')
    for key in ('label_chunk', 'max_visible'):
        if type(result[key]) is not int or result[key] < 1:
            raise ValueError(f'mdg {key} must be a positive integer')
    if (type(result['absent_share']) not in (int, float) or not 0 <= result['absent_share'] < 1
            or result['max_visible'] > 24):
        raise ValueError('mdg requires max_visible <= 24 and absent_share in [0,1)')
    return result


def validate(cfg):
    settings(cfg['mdg'])
    if (cfg.get('training_mode') != 'final' or cfg.get('frame_layout') != 'duplicate'
            or cfg.get('frame_markers') is not True
            or cfg.get('carrier_placement') != 'append_after_temporal_group_video_tokens_v1'):
        raise ValueError('mdg requires final C1_A with duplicate frames and frame markers')
    if cfg['streams'].get('mdg') != cfg['mdg']['clips_jsonl']:
        raise ValueError('streams.mdg must name the mdg.clips_jsonl input')


def pin(value):
    return file_pin(pinned(value) if isinstance(value, dict) else value)


def exclusions(value):
    if isinstance(value, list):
        if any(not isinstance(s, str) or not s for s in value):
            raise ValueError('mdg exclude_scenes must contain scene names')
        return sorted(set(value)), None
    bound = pin(value)
    value = load(pinned(bound))
    names = value if isinstance(value, list) else value.get('scenes', value.get('names'))
    if not isinstance(names, list) or any(not isinstance(s, str) for s in names):
        raise ValueError('mdg exclusion file must contain scenes or names')
    return sorted(set(names)), bound


def inputs(block):
    from . import mdg_inputs
    value = settings(block)
    names, bound = exclusions(value['exclude_scenes'])
    rasters, raster_manifest = mdg_inputs.directory(value['rasters'])
    frames, frame_manifest = mdg_inputs.directory(value['frame_root'])
    result = dict(clips_jsonl=pin(value['clips_jsonl']), confusers=pin(value['confusers']),
                  vocab=pin(value['vocab']), stem_weights=pin(value['stem_weights']),
                  rasters=rasters, frame_root=frames,
                  exclude_scenes=names, exclusions_pin=bound)
    sources = mdg_inputs.clip_sources(result['clips_jsonl'])
    if sources is not None:
        result['clips_sources'] = sources
    identities = mdg_inputs.scene_identities(result['clips_jsonl'])
    if identities is not None:
        result['scene_identities'] = identities
    if raster_manifest:
        result['raster_manifest'] = raster_manifest
    if frame_manifest:
        result['frame_manifest'] = frame_manifest
    if value.get('init_artifact'):
        result['init_artifact'] = mdg_inputs.artifact(value['init_artifact'])
    return result


def prepare(cfg, benchmark, reported, scene_filter=None):
    from . import carrier_c1_routing as routing
    from .carrier_c1_run import excluded_row
    from .grounding_targets import build_index
    from .mdg_train import split_index
    from . import mdg_inputs
    source = inputs(cfg['mdg'])
    clips = [pinned(value) for value in source.get('clips_sources', [source['clips_jsonl']])]
    rasters, resized = mdg_inputs.raster_manifest(source), mdg_inputs.frame_hashes(source)
    overlap, identity_rows, identity_scenes = 0, 0, set()
    for path in clips:
        with path.open() as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                row = mdg_inputs.identify_scene(row, source.get('scene_identities'))
                if source.get('scene_identities') is not None:
                    identity_rows += 1
                    identity_scenes.add(row['scene'])
                if row['scene'] in source['exclude_scenes']:
                    continue
                check = dict(row)
                if 'dataset' not in check:
                    if '/' in check['scene']:
                        check['dataset'], check['scene'] = check['scene'].split('/', 1)
                    elif re.fullmatch(r'scene\d{4}_\d{2}', check['scene']):
                        check['dataset'] = 'scannet'
                hit, seen = excluded_row(check, benchmark, reported, 'mdg')
                if (hit or routing.excluded(benchmark, row['scene'])) and not (
                        scene_filter is not None and scene_filter.excluded(check)):
                    raise ValueError('mdg stream contains benchmark-scene rows; rebuild it filtered')
                overlap += seen
                base = path.parent if 'clips_sources' in source else Path(source['rasters'])
                raster = (base / row['path']).resolve()
                if not raster.is_relative_to(Path(source['rasters'])):
                    raise ValueError('MDG raster is outside the configured rasters root')
                if rasters is not None and (raster not in rasters or rasters[raster]['sha256'] != row['sha256']
                                           or raster.stat().st_size != rasters[raster]['bytes']):
                    raise ValueError('MDG clip raster differs from its pinned manifest')
                if resized is not None and not set(row['frame_sha256']) <= resized:
                    raise ValueError('MDG clip uses frames absent from its resized-frame manifest')
                pinned(dict(path=str(raster), sha256=row['sha256']))
    index = build_index([str(path) for path in clips], exclude_scenes=source['exclude_scenes'],
                        holdout_fraction=.05, root=None if 'clips_sources' in source else source['rasters'],
                        remove_files=cfg.get('remove_files', ()),
                        ground_target_filter=cfg.get('ground_target_filter', False),
                        scene_identities=source.get('scene_identities'))
    index = split_index(index, source)
    for split in ('train', 'tau', 'val'):
        index[split] = [mdg_inputs.explicit_frames(row, source['frame_root']) for row in index[split]]
    vocab = load(pinned(source['vocab']))
    if not isinstance(vocab, list) or any(not isinstance(v, str) or not v for v in vocab):
        raise ValueError('MDG vocab must be a JSON list of labels')
    index['vocab'] = vocab
    path = Path(cfg['preparation_output'])/'mdg_index.json'
    write(path, index)
    result = dict(kind='mdg', receipt=cfg['streams']['mdg'], count=len(index['train']),
                index=file_pin(path), inputs=source, settings_sha256=digest(settings(cfg['mdg'])),
                benchmark_rows_dropped=0, reported_overlap_rows=overlap,
                exclusions=cfg.get('exclusions'), report_exclusions=cfg.get('report_exclusions'))
    if source.get('scene_identities') is not None:
        result['scene_identity'] = dict(manifest=source['clips_jsonl'], mapped_rows=identity_rows,
                                        mapped_scenes=len(identity_scenes),
                                        datasets=sorted({source['scene_identities'][scene]['dataset']
                                                         for scene in identity_scenes}))
    return result


def verify(cfg, value):
    if (value.get('kind') != 'mdg' or value.get('inputs') != inputs(cfg['mdg'])
            or value.get('settings_sha256') != digest(settings(cfg['mdg']))
            or value.get('exclusions') != cfg.get('exclusions')
            or value.get('report_exclusions') != cfg.get('report_exclusions')):
        raise ValueError('MDG preparation differs from configuration/source')
    for key in ('exclusions', 'report_exclusions'):
        if value.get(key):
            pinned(value[key])
    index = load(pinned(value['index']))
    from .ground_target_filter import TargetFilter
    if cfg.get('remove_files') or cfg.get('ground_target_filter'):
        expected = TargetFilter(cfg.get('remove_files', ()),
                                shape_filter=cfg.get('ground_target_filter', False)).settings()
        if index.get('target_filter', {}).get('settings') != expected:
            raise ValueError('MDG target-filter rule differs from configuration')
        if any(row.get('ground_target_filter') != expected
               for split in ('train', 'tau', 'val') for row in index[split]):
            raise ValueError('MDG row lacks the prepared target-filter rule')
    from .mdg_train import split_index
    split_index(index, value['inputs'])
    if len(index['train']) != value['count'] or not value['count']:
        raise ValueError('MDG training count differs')
    return index


def dataset(receipt, processor, split='train'):
    from .mdg_train import ClipDataset, bind_frames
    value = receipt['streams']['mdg']
    index = load(pinned(value['index']))
    config = {**settings(receipt['mdg']), **value['inputs']}
    if any(not row.get('student_input') for row in index[split]):
        bind_frames(config)
    return ClipDataset(index[split], index['vocab'], processor, receipt, config)


def attach(model, block, processor, source=None):
    from .mask_grounding_head import load_artifact
    from .mdg_train import new_head
    from .mdg_features import bind_processor
    model.mdg_settings = settings(block)
    bind_processor(model, processor)
    if model.training_mode != 'final':
        raise ValueError('MDG requires training_mode final')
    if block.get('init_artifact'):
        from .mdg_inputs import artifact
        initialization = source['init_artifact'] if source else artifact(block['init_artifact'])
        for value in initialization.values():
            pinned(value)
        init_root = Path(initialization['mdg.json']['path']).parent
        head, meta = load_artifact(init_root)
        if (head.cfg.lm_dim != model.config.text_config.hidden_size
                or head.cfg.vit_dim != model.config.vision_config.hidden_size or head.cfg.geo_dim):
            raise ValueError('MDG init dimensions differ from the C1 model')
        model.mdg_tau = meta['tau']
        model.mdg_tau_info = dict(source='init_artifact', base_artifact=meta['base_artifact'])
    else:
        stem = str(pinned(source['stem_weights'])) if source else str(pinned(pin(block['stem_weights'])))
        head = new_head(model, dict(stem_weights=stem))
        model.mdg_tau = None
        model.mdg_tau_info = {}
    model.auxiliary_heads.mdg = head.float().train(model.training)
    from . import mdg_lora
    mdg_lora.install(model, model.mdg_settings['lora_rank'])
    if hasattr(model, 'ground_token_ids') and model.mdg_settings['lora_rank']:
        from .ground_tokens import install_rows
        install_rows(model)
    if block.get('init_artifact') and meta.get('lora_config'):
        if meta['lora_config']['rank'] != model.mdg_settings['lora_rank']:
            raise ValueError('MDG init LoRA rank differs from settings')
        mdg_lora.load(model, init_root, meta)
    bind_processor(model, processor)
    model.mdg_processor = processor


@contextmanager
def capture_mode(model):
    # Native wrappers call eval() on shared modules. Restore each flag, including checkpointed blocks.
    modes = [(module, module.training) for module in model.modules()]
    try:
        model.eval()
        with torch.no_grad():
            yield
    finally:
        for module, mode in modes:
            module.training = mode


def forward(model, batch, targets):
    from .mdg_features import capture_prefix, suffix_states
    if not hasattr(model.auxiliary_heads, 'mdg') or model.training_mode != 'final':
        raise ValueError('The mdg stream requires an enabled final-mode MDG head')
    labels = batch['aux_mdg_labels']
    count = len(labels)
    if not count:
        raise ValueError('MDG requires at least one label')
    size = torch.tensor(count, device=batch['input_ids'].device)
    if dist.is_initialized():
        dist.all_reduce(size, op=dist.ReduceOp.MAX)
    padded = list(labels) + [labels[0]] * (int(size) - count)
    train_adapters = bool(model.mdg_settings['lora_rank'] and model.training and torch.is_grad_enabled())
    canonical_eval = targets is None and not model.training and not torch.is_grad_enabled()
    with capture_mode(model), torch.autocast(device_type=batch['input_ids'].device.type, enabled=False):
        prefix = capture_prefix(model, batch)
        if canonical_eval:
            from .mdg_stream import stream_suffix_states
            states = stream_suffix_states(model, prefix, batch, padded, chunk=model.mdg_settings['label_chunk'])
        else:
            states = suffix_states(model, prefix, padded, chunk=model.mdg_settings['label_chunk'],
                                   train_adapters=train_adapters)
    inputs = (prefix.taps, prefix.vit, prefix.pixels, prefix.grid)
    del prefix
    head = model.auxiliary_heads.mdg
    with torch.autocast(device_type=batch['input_ids'].device.type, enabled=False):
        video = head.encode_video(*inputs)
        del inputs
        if canonical_eval:
            from .mdg_stream import decoder_outputs
            outs = decoder_outputs(head, video, type(states)(states.query[:count], states.phrase[:count], states.phrase_mask[:count]))
        else:
            outs = head(video, states.query[:count], states.phrase[:count], states.phrase_mask[:count],
                        train_suffix=train_adapters)
        if targets is None:
            return outs
        parts = head.loss(outs, targets)
        # Other mixed streams provide their own zero-gradient participation.
        # Do not give unrelated heads AdamW decay on an isolated LoRA MDG step.
        touched = head.parameters() if model.mdg_settings['lora_rank'] else model.auxiliary_heads.parameters()
        touch = sum(p.reshape(-1)[0] * 0. for p in touched if p.requires_grad)
        return dict(loss=model.mdg_settings['weight'] * parts['total'] + touch,
                    components={'mdg': parts['total'].detach()},
                    metrics=dict(mdg=dict(Q=count, padded_Q=int(size),
                        prompt_tokens=batch['input_ids'].shape[1],
                        loss_parts={k: float(v.detach()) for k, v in parts.items()})))


def calibrate(wrapped, model):
    from .mdg_train import collect_outputs, choose_tau
    from .carrier_c1_run import move
    data = dataset(model.mdg_receipt, model.mdg_processor, 'tau')
    device = next(model.auxiliary_heads.mdg.parameters()).device
    def predict(item):
        batch = {**item['batch'], 'aux_mdg_labels': item['labels']}
        return wrapped(move(batch, device), stream='mdg')
    with capture_mode(model):
        records = collect_outputs(model, model.auxiliary_heads.mdg, data, device,
                                  model.mdg_settings, predictor=predict)
    tau, objective = choose_tau(records)
    return tau, dict(source='tau_slice', split='train', objective=objective,
        clip_ids_sha256=digest(records['clips']), n_clips=len(records['clips']),
        scenes=sorted({r['scene'] for r in data.entries}), val_used=False, sampler_used=False)


def export(directory, model, state, cfg, step, tau, tau_info):
    from .mask_grounding_head import MaskGroundingHead, save_artifact
    from . import mdg_lora
    with torch.random.fork_rng(devices=[]):
        head = MaskGroundingHead(model.auxiliary_heads.mdg.cfg, _load_pretrained=False)
    head.load_state_dict({k.removeprefix('auxiliary_heads.mdg.'): v for k, v in state.items()
                         if k.startswith('auxiliary_heads.mdg.')}, strict=True)
    save_artifact(Path(directory)/'mdg', head, dict(base_artifact=file_pin(Path(directory)/'artifact.json'),
        trainer_commit=load(pinned(cfg['code']))['commit'], step=step, tau=tau, metrics={}, calibration=tau_info,
        **mdg_lora.export(Path(directory)/'mdg', model, state)))


def attach_export(model, metadata):
    from .mask_grounding_head import MDGConfig, MaskGroundingHead
    config = MDGConfig(**metadata['config'])
    if (config.lm_dim != model.config.text_config.hidden_size
            or config.vit_dim != model.config.vision_config.hidden_size or config.geo_dim):
        raise ValueError('MDG export dimensions differ from the C1 model')
    model.auxiliary_heads.mdg = MaskGroundingHead(config, _load_pretrained=False).float()
    if metadata.get('lora_config'):
        from .mdg_lora import install
        install(model, metadata['lora_config']['rank'])
        if metadata['lora_config'].get('opener_tokens'):
            from .ground_tokens import install_rows
            install_rows(model, metadata['lora_config']['opener_tokens'])
        if model.mdg_lora_config != metadata['lora_config']:
            raise ValueError('MDG LoRA export architecture differs')
