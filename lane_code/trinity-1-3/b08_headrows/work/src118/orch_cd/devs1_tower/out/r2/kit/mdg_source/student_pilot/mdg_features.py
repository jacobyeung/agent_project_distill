"""Frozen MDG prefill features and independent hybrid-cache continuations."""
import argparse
import copy
from dataclasses import dataclass
import json
from pathlib import Path
import resource
import time

import torch
import torch.nn.functional as F

from . import grounding_features as gh
from .carrier_c1_data import C1_B, C1_C, frame_position_ids, standard_attention_mask
from .point_depth_head import vit_blocks, vit_grids_by_row, vit_layer_hooks

TAP_LAYERS = (16, 24)
VIT_BLOCKS = (9, 17, 25)
QUERY_LAYER = 24
PHRASE_MAX = 8


@dataclass
class PrefixFeatures:
    taps: list[torch.Tensor]
    vit: list[torch.Tensor]
    pixels: torch.Tensor
    grid: tuple[int, int]
    hidden: torch.Tensor
    cache: object
    prefix_len: int
    rope_deltas: torch.Tensor | None = None


@dataclass
class SuffixStates:
    query: torch.Tensor
    phrase: torch.Tensor
    phrase_mask: torch.Tensor


def bind_processor(model, processor):
    """Bind tokenizer and RGB normalization absent from the feature-call signatures."""
    model.mdg_tokenizer = processor.tokenizer
    model.mdg_video_processor = getattr(processor, 'video_processor', None)


def _tokenizer(model):
    tokenizer = getattr(model, 'mdg_tokenizer', getattr(model, 'tokenizer', None))
    if tokenizer is None:
        raise ValueError('Bind model.mdg_tokenizer (or call bind_processor) before suffix extraction')
    return tokenizer


def suffix_tokens(tokenizer, name):
    if not isinstance(name, str) or not name.strip() or any(c in name for c in '"<>\r\n'):
        raise ValueError('Invalid ground object name')
    start = len('<ground obj="')
    text = f'<ground obj="{name}">'
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = list(encoded['input_ids']), encoded['offset_mapping']
    if ids != tokenizer.encode(text, add_special_tokens=False):
        raise ValueError('Suffix offset tokenization differs from encode')
    span = [i for i, (a, b) in enumerate(offsets) if a < start + len(name) and start < b]
    if not ids or not span or span != list(range(span[0], span[-1] + 1)):
        raise ValueError('Suffix needs a contiguous NAME token span')
    return ids, slice(span[0], span[-1] + 1)


def unpatchify(pixel_values, video_grid_thw, *, patch_size=16, temporal_patch_size=2,
               merge_size=2, image_mean=(.5, .5, .5), image_std=(.5, .5, .5)):
    """Invert Qwen3-VL's [t,h/m,w/m,m,m,c,tp,p,p] video packing."""
    if video_grid_thw.shape != (1, 3):
        raise ValueError('MDG unpatchify requires one video')
    t, h, w = map(int, video_grid_thw[0])
    p, tp, m = patch_size, temporal_patch_size, merge_size
    if min(t, h, w, p, tp, m) <= 0 or h % m or w % m:
        raise ValueError('Invalid video patch grid')
    if tuple(pixel_values.shape) != (t * h * w, 3 * tp * p * p):
        raise ValueError('Video patches differ from the configured processor layout')
    packed = pixel_values.float().reshape(t, h // m, w // m, m, m, 3, tp, p, p)
    pixels = packed.permute(0, 6, 5, 1, 3, 7, 2, 4, 8).reshape(t, tp, 3, h * p, w * p)[:, 0]
    mean = pixels.new_tensor(image_mean).reshape(1, 3, 1, 1)
    std = pixels.new_tensor(image_std).reshape(1, 3, 1, 1)
    return (pixels * std + mean).clamp(0, 1).detach()


def _native(model):
    from transformers import Qwen3_5ForConditionalGeneration
    with torch.device('meta'):
        native = Qwen3_5ForConditionalGeneration(model.config)
    native.model, native.lm_head = model.model, model.lm_head
    return native.eval()


def _prefill(model, batch, native):
    if model.training:
        raise ValueError('MDG capture requires a frozen eval model')
    model.check_placement(batch)
    if not bool((batch['attention_mask'] == 1).all()):
        raise ValueError('MDG requires an unpadded single prefix')
    seen = [False]

    def replace(module, args, output):
        if seen[0]:
            return output
        seen[0] = True
        return model.carrier_embeddings(output, batch['aux_camera_positions'])

    def prefill(module, args, values):
        if model.carrier_placement == C1_B:
            values['position_ids'] = frame_position_ids(values['position_ids'], batch)
        if model.carrier_placement == C1_C:
            values['c1_prefix_mask'] = standard_attention_mask(batch, True)
        return args, values

    hooks = [model.get_input_embeddings().register_forward_hook(replace),
             model.model.language_model.register_forward_pre_hook(prefill, with_kwargs=True)]
    try:
        inputs = {k: batch[k] for k in ('input_ids', 'attention_mask', 'pixel_values_videos',
                                       'video_grid_thw', 'mm_token_type_ids') if k in batch}
        return native(**inputs, use_cache=True, return_dict=True, logits_to_keep=1)
    finally:
        for hook in hooks:
            hook.remove()


@torch.no_grad()
def capture_prefix(model, batch):
    if model.training:
        raise ValueError('MDG capture requires a frozen eval model')
    frames = int(batch['video_grid_thw'][0, 0])
    raw_vit = {}
    blocks = vit_blocks(model.model)
    if any(k - 1 not in blocks for k in VIT_BLOCKS):
        raise ValueError('MDG requires every configured ViT block')
    hooks = vit_layer_hooks(model.model, VIT_BLOCKS, raw_vit)
    try:
        with gh.FeatureCapture(model, batch, expected_frames=frames) as recorded:
            recorded.tap_layers = TAP_LAYERS
            output = _prefill(model, batch, _native(model))
        captured = recorded.finish()
        vit = [vit_grids_by_row(raw_vit[k].detach(), batch['video_grid_thw'], 2)[0] for k in VIT_BLOCKS]
    finally:
        for hook in hooks:
            hook.remove()
    vision = model.config.vision_config
    processor = getattr(model, 'mdg_video_processor', None)
    pixels = unpatchify(batch['pixel_values_videos'], batch['video_grid_thw'],
                        patch_size=vision.patch_size, temporal_patch_size=vision.temporal_patch_size,
                        merge_size=vision.spatial_merge_size,
                        image_mean=getattr(processor, 'image_mean', (.5, .5, .5)),
                        image_std=getattr(processor, 'image_std', (.5, .5, .5)))
    return PrefixFeatures(captured.taps, vit, pixels, captured.grid, captured.hidden,
                          output.past_key_values, batch['input_ids'].shape[1], model.model.rope_deltas.detach().clone())


def expand_cache(cache, count):
    """Copy all four hybrid state tensors; HF's repeat helper lacks GDN support."""
    if count < 1 or getattr(cache, 'offloading', False):
        raise ValueError('MDG requires a positive batch and a resident native hybrid cache')
    result = copy.copy(cache)
    result.layers = []
    for original in cache.layers:
        layer = copy.copy(original)
        for key in ('keys', 'values', 'conv_states', 'recurrent_states'):
            value = getattr(original, key, None)
            if value is not None:
                if value.shape[0] != 1:
                    raise ValueError('MDG prefix cache must have batch size one')
                setattr(layer, key, value.detach().repeat_interleave(count, dim=0))
        if hasattr(layer, 'max_batch_size'):
            layer.max_batch_size = count
        result.layers.append(layer)
    return result


class _SuffixCapture:
    def __init__(self, model):
        self.model, self.states, self.handles = model, {}, []

    def __enter__(self):
        def record(key):
            def hook(module, args, output):
                value = output[0] if isinstance(output, tuple) else output
                self.states[key] = value.detach()
            return hook
        layers = self.model.model.language_model.layers
        if not 1 <= QUERY_LAYER < len(layers):
            raise ValueError('MDG query layer must precede final norm')
        self.handles = [layers[QUERY_LAYER - 1].register_forward_hook(record('layer')),
                        self.model.model.language_model.norm.register_forward_hook(record('norm'))]
        return self

    def __exit__(self, *exc):
        for handle in self.handles:
            handle.remove()

    def finish(self, lengths, spans, offset=0):
        states = [self.states['layer'], self.states['norm']]
        query = torch.stack([torch.stack([s[i, offset + n - 1] for s in states])
                             for i, n in enumerate(lengths)]).float()
        phrase = query.new_zeros((len(lengths), PHRASE_MAX, 2, query.shape[-1]))
        mask = torch.zeros((len(lengths), PHRASE_MAX), dtype=torch.bool, device=query.device)
        for i, span in enumerate(spans):
            n = min(PHRASE_MAX, span.stop - span.start)
            phrase[i, :n] = torch.stack([s[i, offset + span.start:offset + span.start + n]
                                         for s in states], dim=1).float()
            mask[i, :n] = True
        return SuffixStates(query.detach(), phrase.detach(), mask)


@torch.no_grad()
def suffix_states(model, prefix, names, *, chunk=8):
    if model.training or type(chunk) is not int or chunk < 1:
        raise ValueError('MDG requires eval mode and a positive integer chunk')
    tokenizer = _tokenizer(model)
    rows = [suffix_tokens(tokenizer, name) for name in names]
    if not rows:
        d = prefix.hidden.shape[-1]
        return SuffixStates(prefix.hidden.new_zeros((0, 2, d), dtype=torch.float32),
                            prefix.hidden.new_zeros((0, PHRASE_MAX, 2, d), dtype=torch.float32),
                            torch.zeros((0, PHRASE_MAX), dtype=torch.bool, device=prefix.hidden.device))
    if prefix.cache.get_seq_length() != prefix.prefix_len or prefix.rope_deltas is None:
        raise ValueError('Incomplete MDG prefix cache or RoPE delta')
    native, outputs = _native(model), []
    previous_delta = model.model.rope_deltas
    try:
        for start in range(0, len(rows), chunk):
            group = rows[start:start + chunk]
            lengths = [len(ids) for ids, _ in group]
            ids = torch.full((len(group), max(lengths)), tokenizer.pad_token_id or 0,
                             dtype=torch.long, device=prefix.hidden.device)
            mask = torch.zeros_like(ids)
            for i, (tokens, _) in enumerate(group):
                ids[i, :len(tokens)] = ids.new_tensor(tokens)
                mask[i, :len(tokens)] = 1
            attention = torch.cat([mask.new_ones((len(group), prefix.prefix_len)), mask], dim=1)
            cache = expand_cache(prefix.cache, len(group))
            model.model.rope_deltas = prefix.rope_deltas.repeat_interleave(len(group), dim=0)
            positions = native._prepare_position_ids_for_generation(ids,
                {'attention_mask': attention, 'past_key_values': cache})[..., -ids.shape[1]:]
            with _SuffixCapture(model) as recorded:
                native(input_ids=ids, attention_mask=attention, position_ids=positions,
                       past_key_values=cache, use_cache=True, return_dict=True, logits_to_keep=1)
            outputs.append(recorded.finish(lengths, [span for _, span in group]))
    finally:
        model.model.rope_deltas = previous_delta
    return SuffixStates(*(torch.cat([getattr(out, key) for out in outputs])
                          for key in ('query', 'phrase', 'phrase_mask')))


@torch.no_grad()
def full_forward_states(model, batch, name):
    tokens, span = suffix_tokens(_tokenizer(model), name)
    ids = batch['input_ids'].new_tensor([tokens])
    full = {**batch, 'input_ids': torch.cat([batch['input_ids'], ids], dim=1),
            'attention_mask': torch.cat([batch['attention_mask'], torch.ones_like(ids)], dim=1)}
    if 'mm_token_type_ids' in batch:
        full['mm_token_type_ids'] = torch.cat([batch['mm_token_type_ids'], torch.zeros_like(ids)], dim=1)
    previous_delta = model.model.rope_deltas
    try:
        with _SuffixCapture(model) as recorded:
            _prefill(model, full, _native(model))
        return recorded.finish([len(tokens)], [span], batch['input_ids'].shape[1])
    finally:
        model.model.rope_deltas = previous_delta


def cache_memory(config, prefix_len=10000, *, dtype=torch.bfloat16):
    text = config.text_config if hasattr(config, 'text_config') else config
    full = text.layer_types.count('full_attention')
    linear = text.layer_types.count('linear_attention')
    size = torch.empty((), dtype=dtype).element_size()
    kv = full * 2 * prefix_len * text.num_key_value_heads * text.head_dim * size
    conv = linear * (2 * text.linear_num_key_heads * text.linear_key_head_dim
                     + text.linear_num_value_heads * text.linear_value_head_dim) * text.linear_conv_kernel_dim * size
    recurrent = linear * text.linear_num_value_heads * text.linear_key_head_dim * text.linear_value_head_dim * size
    return dict(prefix_len=prefix_len, dtype=str(dtype), full_layers=full, linear_layers=linear,
                kv_bytes=kv, conv_bytes=conv, recurrent_bytes=recurrent,
                per_label_bytes=kv + conv + recurrent, per_label_mib=(kv + conv + recurrent) / 2**20)


def compare_parity(model, batch, names, *, chunk=8):
    if not names:
        raise ValueError('Parity requires at least one label')
    device = model.get_input_embeddings().weight.device
    if device.type == 'cuda':
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)
    started = time.perf_counter()
    prefix = capture_prefix(model, batch)
    reference = gh.capture(model, batch)
    equal = torch.equal(prefix.hidden, reference.hidden)
    cached = suffix_states(model, prefix, names, chunk=chunk)
    labels = []
    for i, name in enumerate(names):
        full = full_forward_states(model, batch, name)
        parts = []
        for actual, expected in ((cached.query[i].flatten(), full.query[0].flatten()),
                                 (cached.phrase[i][cached.phrase_mask[i]].flatten(),
                                  full.phrase[0][full.phrase_mask[0]].flatten())):
            difference = float((actual - expected).abs().max())
            scale = float(expected.abs().max())
            cosine = float(F.cosine_similarity(actual, expected, dim=0))
            if bool((actual == 0).all() and (expected == 0).all()):
                cosine = 1.
            relative = difference / max(scale, 1e-30)
            parts.append(dict(max_abs_diff=difference, relative_max_diff=relative, cosine=cosine,
                              passed=cosine >= .999 and relative <= .02))
        labels.append(dict(name=name, query=parts[0], phrase=parts[1],
                           passed=all(p['passed'] for p in parts)
                           and torch.equal(cached.phrase_mask[i], full.phrase_mask[0])))
    if device.type == 'cuda':
        torch.cuda.synchronize(device)
    return dict(prefill_hidden_bitwise_equal=equal, labels=labels,
                passed=equal and all(row['passed'] for row in labels), seconds=time.perf_counter() - started,
                peak_memory_bytes=torch.cuda.max_memory_allocated(device) if device.type == 'cuda' else None,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                expanded_cache=cache_memory(model.config))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    parity = sub.add_parser('parity')
    for key in ('config', 'artifact', 'clips-jsonl', 'frame-root', 'out'):
        parity.add_argument('--' + key, required=True)
    parity.add_argument('--n', type=int, default=2)
    parity.add_argument('--bundle', help='standalone T0 bundle (mdg_runtime); without it the official loader runs')
    parity.add_argument('--max-labels', type=int, default=3, help='full-forward references per clip (each costs one prefill)')
    parity.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    args = parser.parse_args()
    if args.n < 1:
        parser.error('--n must be positive')
    from .carrier_c1_canary import prompt_batch
    from .grounding_train import bind_frames, clip_row
    from .mdg_runtime import load_runtime
    from .grounding_targets import _raster, _visible
    from .p3_provenance import file_pin, write
    cfg = dict(c1_config=args.config, base_artifact=file_pin(args.artifact), frame_root=args.frame_root,
               **({'bundle': args.bundle} if args.bundle else {}))
    bind_frames(cfg)
    device = torch.device(args.device)
    model, processor, native = load_runtime(cfg, device)
    bind_processor(model, processor)
    clips = []
    with Path(args.clips_jsonl).open() as stream:
        for line in stream:
            if not line.strip():
                continue
            clip = json.loads(line)
            source = Path(clip['path'])
            clip['path'] = str(source if source.is_absolute() else Path(args.clips_jsonl).resolve().parent / source)
            _, _, inst, used, aggregation, _ = _raster(clip)
            names = sorted(_visible(inst, used, aggregation)[2])[:args.max_labels]
            if not names:
                raise ValueError('Step-0 clip has no visible labels')
            batch = prompt_batch(processor, clip_row(clip), native)
            batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
            clips.append(dict(qid=str(clip['qid']), **compare_parity(model, batch, names)))
            if len(clips) == args.n:
                break
    report = dict(schema='mdg-step0-parity-v1', clips=clips,
                  passed=len(clips) == args.n and all(c['passed'] for c in clips))
    write(args.out, report)
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
