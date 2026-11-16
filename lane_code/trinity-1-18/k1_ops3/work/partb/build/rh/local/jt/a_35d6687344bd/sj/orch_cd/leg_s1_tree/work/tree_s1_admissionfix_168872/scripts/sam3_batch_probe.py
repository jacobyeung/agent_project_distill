"""Compare native image batches, singleton encoding, and precision on real frames."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
import os
from pathlib import Path
import time
import traceback
from unittest.mock import patch
import sys

import torch
from PIL import Image

from student_pilot.sam3_tower import Sam3Tower, ClipFeatures, _map_tensors
from scripts.sam3_validate import compare, compare_noise_aware, dump, prediction, sha256


def difference(a, b):
    return {'max_abs': float((a.float() - b.float()).abs().max()),
            'equal': bool(torch.equal(a, b)), 'shape': list(a.shape),
            'dtype': str(a.dtype)}


def compare_results(a, b, *, legacy=True):
    result = compare(prediction(a), b)
    result['noise_aware'] = compare_noise_aware(prediction(a), b, gate=.3 if legacy else .2,
                                               joint_gate=not legacy)
    result['all_score_max_abs_error'] = float((a.all_scores-b.all_scores).abs().max())
    result['query_sets_match'] = set(a.query_ids.tolist()) == set(b.query_ids.tolist())
    old = {q: mask for q, mask in zip(a.query_ids.tolist(), a.masks)}
    ious = []
    for q, mask in zip(b.query_ids.tolist(), b.masks):
        if q in old:
            union = (old[q] | mask).sum().item()
            ious.append((old[q] & mask).sum().item()/union if union else 1.)
    result['matched_id_mask_min_iou'] = min(ious, default=None)
    result['matched_id_masks_compared'] = len(ious)
    return result


@torch.inference_mode()
def native_encode(tower, frames):
    """Diagnostic only: exactly the original wrapper's batched backbone path."""
    with tower._autocast():
        backbone = tower._backend.set_image_batch(frames)['backbone_out']
    values = {k: backbone[k] for k in ('backbone_fpn', 'vision_pos_enc')}
    return ClipFeatures(tuple(_map_tensors(values, lambda t: t[i:i+1].cpu().clone())
                              for i in range(len(frames))),
                        tuple((im.height, im.width) for im in frames), tower._owner)


def detect(tower, features, phrase, *, legacy=False):
    # CPU tensors need no page locking or asynchronous host-to-GPU transfer.
    context = (patch.object(torch.Tensor, 'pin_memory', lambda t, *a, **kw: t)
               if tower.device.type == 'cpu' else nullcontext())
    with context:
        return tower._detect(features, phrase, legacy=legacy)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('manifest', 'checkpoint', 'source-root', 'receipt', 'out'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    p.add_argument('--threads', type=int, default=8)
    p.add_argument('--frames', type=int, choices=range(4, 9), default=4)
    p.add_argument('--precisions', nargs='+', choices=('bf16', 'float32'), default=['bf16', 'float32'])
    p.add_argument('--mode', choices=('native', 'safe', 'all'), default='all')
    p.add_argument('--names', type=int, default=2, help='First N cached names; default couch and lamp')
    p.add_argument('--paired-names', action='store_true', help='Assign one name to each frame, cyclically')
    p.add_argument('--skip-safe-bf16', action='store_true', help='Measure guarded batching in float32 only')
    p.add_argument('--warmup-only', action='store_true', help='Synthetic grounding preflight; no image encodes')
    args = p.parse_args()
    if not 1 <= args.threads <= 8:
        p.error('Use at most eight CPU threads')
    if args.device == 'cuda' and (not os.environ.get('CUDA_VISIBLE_DEVICES') or torch.cuda.device_count() != 1):
        p.error('The orchestrator must select exactly one GPU under its GPU wrapper')
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    row = json.loads(args.manifest.read_text())['scenes'][0]
    if not 1 <= args.names <= len(row['phrases']):
        p.error('names must select at least one available cached phrase')
    phrases = row['phrases'][:args.names]
    slots = [i*32//args.frames for i in range(args.frames)]
    images = []
    for slot in slots:
        path = row['frames'][slot]
        if sha256(path) != row['frame_sha256'][slot]:
            raise ValueError('Input RGB hash differs')
        with Image.open(path) as im:
            images.append(im.convert('RGB'))
    tower = Sam3Tower(dict(checkpoint_path=str(args.checkpoint), source_root=str(args.source_root),
                           receipt_path=str(args.receipt), device=args.device, precision='bf16',
                           image_batch_size=args.frames))
    start = time.monotonic()
    # Upstream precomputes two coordinate caches on CUDA even for device='cpu'.
    # Defer these caches so their normal forward paths use the input's device.
    if args.device == 'cpu':
        sys.path.insert(0, str(args.source_root.resolve()))
        import sam3.model_builder as builder
        position, decoder = builder.PositionEmbeddingSine, builder.TransformerDecoder
        def cpu_position(*a, **kw):
            kw['precompute_resolution'] = None
            return position(*a, **kw)
        def cpu_decoder(*a, **kw):
            kw['resolution'] = None
            return decoder(*a, **kw)
        with patch.object(builder, 'PositionEmbeddingSine', cpu_position), \
                patch.object(builder, 'TransformerDecoder', cpu_decoder):
            tower._load()
    else:
        tower._load()
    report = dict(scene=row['scene'], slots=slots, names=phrases, device=args.device,
                  torch_version=torch.__version__, threads=args.threads,
                  cuda_version=torch.version.cuda,
                  device_name=torch.cuda.get_device_name() if args.device == 'cuda' else 'CPU',
                  mode=args.mode, paired_names=args.paired_names, skip_safe_bf16=args.skip_safe_bf16,
                  requested_image_batch_size=args.frames,
                  float32_control='fused MLP without unconditional bf16 casts; TF32 disabled on CUDA',
                  cpu_wrappers=['deferred positional caches', 'pin_memory no-op'] if args.device == 'cpu' else [],
                  diagnostic_sha256=sha256(__file__),
                  tower_sha256=sha256(Path(__file__).parents[1]/'student_pilot/sam3_tower.py'),
                  checkpoint_sha256=tower.receipt['checkpoint_sha256'],
                  model_load_seconds=time.monotonic()-start, precisions={})
    print(json.dumps({'loaded_seconds': report['model_load_seconds']}), flush=True)
    if args.warmup_only:
        for precision in args.precisions:
            tower.precision = precision
            dtype = torch.bfloat16 if precision == 'bf16' else torch.float32
            tensors = [torch.zeros(1, 256, side, side, dtype=dtype) for side in (288, 144, 72)]
            features = ClipFeatures((dict(backbone_fpn=tensors, vision_pos_enc=tensors),), ((16, 16),), tower._owner)
            result = detect(tower, features, row['phrases'][0])[0]
            print(json.dumps(dict(synthetic_grounding_preflight=precision, presence=result.presence)), flush=True)
        return
    # Probe module boundaries in execution order. Retain only the first image.
    observed = {}
    trace = []
    phase = ['off']
    def hook(name):
        def save(module, inputs, output):
            if phase[0] == 'off' or not isinstance(output, torch.Tensor):
                return
            if phase[0] == 'single':
                observed[name] = output.detach().cpu().clone()
            elif name in observed:
                a = observed[name]
                b = output[:a.shape[0]].detach().cpu()
                trace.append(dict(module=name, **difference(a, b)))
        return save
    trunk = tower._backend.model.backbone.vision_backbone.trunk
    handles = [trunk.patch_embed.proj.register_forward_pre_hook(
        lambda module, inputs: hook('preprocessed_pixels')(module, inputs, inputs[0]))]
    for name, module in trunk.named_modules():
        if ((name in {'patch_embed.proj', 'patch_embed', 'ln_pre'} or
                name.startswith('blocks.0.') or (name.startswith('blocks.') and name.count('.') == 1))
                and name not in {'blocks.0.drop_path', 'blocks.0.dropout'}):
            handles.append(module.register_forward_hook(hook(name)))
    predictions = {}
    tf32 = (torch.backends.cuda.matmul.allow_tf32, torch.backends.cudnn.allow_tf32)
    for precision in args.precisions:
        tower.precision = precision
        if args.device == 'cuda':
            torch.backends.cuda.matmul.allow_tf32 = tf32[0] if precision == 'bf16' else False
            torch.backends.cudnn.allow_tf32 = tf32[1] if precision == 'bf16' else False
        observed.clear()
        trace.clear()
        detail = {'status': 'started', 'tf32_matmul': torch.backends.cuda.matmul.allow_tf32,
                  'tf32_cudnn': torch.backends.cudnn.allow_tf32}
        report['precisions'][precision] = detail
        try:
            begin = time.monotonic()
            singles = []
            for i, im in enumerate(images):
                phase[0] = 'single' if i == 0 else 'off'
                singles.extend(tower.encode([im]).frames)
                print(json.dumps(dict(precision=precision, single=i, seconds=time.monotonic()-begin)), flush=True)
            detail['single_encode_seconds'] = time.monotonic()-begin
            singles = ClipFeatures(tuple(singles), tuple((im.height, im.width) for im in images), tower._owner)
            variants = {}
            modes = ('native', 'safe') if args.mode == 'all' else (args.mode,)
            if precision == 'bf16' and args.skip_safe_bf16:
                modes = tuple(n for n in modes if n != 'safe')
                if not modes:
                    raise ValueError('Cannot skip the only requested batch variant')
            for name in modes:
                phase[0] = 'batch' if name == 'native' else 'off'
                begin = time.monotonic()
                variants[name] = native_encode(tower, images) if name == 'native' else tower.encode(images)
                detail[name+'_batch_encode_seconds'] = time.monotonic()-begin
            phase[0] = 'off'
            detail['backbone_trace_first_frame'] = list(trace)
            detail['feature_differences'] = [dict(variant=name, frame=slots[i], key=k, level=j, **difference(a, b))
                for name, batch in variants.items() for i, (x, y) in enumerate(zip(singles.frames, batch.frames))
                for k in x for j, (a, b) in enumerate(zip(x[k], y[k]))]
            observed.clear()
            print(json.dumps(dict(precision=precision, batch_seconds={n: detail[n+'_batch_encode_seconds'] for n in variants},
                                  first_divergence=next((r for r in trace if not r['equal']), None))), flush=True)
            checks = []
            predictions[precision] = {}
            for phrase_index, phrase in enumerate(phrases):
                indices = [i for i in range(len(images))
                           if not args.paired_names or i % len(phrases) == phrase_index]
                def subset(features):
                    return ClipFeatures(tuple(features.frames[i] for i in indices),
                                        tuple(features.sizes[i] for i in indices), features.owner)
                left = detect(tower, subset(singles), phrase, legacy=None)
                for name, batch in variants.items():
                    right = detect(tower, subset(batch), phrase, legacy=None)
                    for i, pair_a, pair_b in zip(indices, left, right):
                        for legacy, a, b in zip((False, True), pair_a, pair_b):
                            key = f'{slots[i]}:{phrase}:{legacy}'
                            predictions[precision][key] = a
                            checks.append(dict(variant=name, frame=slots[i], phrase=phrase, legacy=legacy,
                                               **compare_results(a, b, legacy=legacy)))
                print(json.dumps(dict(precision=precision, phrase=phrase,
                                      max_score_error=max(c['all_score_max_abs_error'] for c in checks))), flush=True)
            detail['checks'] = checks
            if 'safe' in variants:
                detail['safe_batch_exact'] = (
                    all(c['equal'] for c in detail['feature_differences'] if c['variant'] == 'safe') and
                    all(c['all_score_max_abs_error'] == 0 and c['presence_abs_error'] == 0 and
                        c['query_ids_match'] and c['mask_min_iou'] == 1
                        for c in checks if c['variant'] == 'safe'))
            detail['status'] = 'ok'
            dump(args.out/f'{precision}_single_predictions.json',
                 {k: prediction(v) for k, v in predictions[precision].items()})
            del singles, batch, variants, left, right
        except (RuntimeError, TypeError, AssertionError) as e:
            phase[0] = 'off'
            detail.update(status='unsupported', error=str(e), traceback=traceback.format_exc())
            print(json.dumps(dict(precision=precision, error=str(e))), flush=True)
        dump(args.out/f'{precision}.json', detail)
    if all(report['precisions'].get(p, {}).get('status') == 'ok' for p in ('bf16', 'float32')):
        report['cross_precision_checks'] = [dict(key=k, **compare_results(predictions['float32'][k], v,
                                                                         legacy=k.endswith(':True')))
                                             for k, v in predictions['bf16'].items()]
    for handle in handles:
        handle.remove()
    report['total_seconds'] = time.monotonic()-start
    dump(args.out/'REPORT.json', report)
    print(json.dumps({'complete_seconds': report['total_seconds']}), flush=True)
    if any(d.get('safe_batch_exact') is False for d in report['precisions'].values()):
        raise SystemExit('Safe image batching differs from singles')
    if report['precisions'].get('bf16', {}).get('status') == 'unsupported':
        raise SystemExit('The bf16 probe failed; inspect the recorded exception')


if __name__ == '__main__':
    main()
