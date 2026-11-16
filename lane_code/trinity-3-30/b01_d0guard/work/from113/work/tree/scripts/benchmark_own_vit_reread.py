"""Offline ViT-only CUDA smoke. Writes small JSON/Markdown, never feature caches."""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import statistics
import time
import sys

import numpy as np
import torch
from student_pilot.acceptance_evidence import stage_assertions


def file_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def tensor_sha(value):
    return hashlib.sha256(value.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()


@torch.no_grad()
def native_taps(visual, pixels, grid, layers, chunk_size, *, packed_video=False):
    """Independent direct native forwards at the two compared batch shapes."""
    from student_pilot.point_depth_head import vit_grids_by_row
    pieces = {k: [] for k in layers}
    offset = 0
    for first in range(0, len(grid), chunk_size):
        chunk_grid = grid[first:first+chunk_size]
        count = int(chunk_grid.prod(-1).sum())
        forward_grid = chunk_grid
        if packed_video:
            if not torch.equal(chunk_grid, chunk_grid[:1].expand_as(chunk_grid)):
                raise ValueError('Packed reference requires identical frame grids')
            forward_grid = chunk_grid[:1].clone()
            forward_grid[0, 0] *= len(chunk_grid)
        captured, handles = {}, []
        try:
            for k in layers:
                handles.append(visual.blocks[k-1].register_forward_hook(
                    lambda m, a, o, k=k: captured.__setitem__(k, o.detach().clone())))
            visual(pixels[offset:offset+count], grid_thw=forward_grid)
        finally:
            for handle in handles: handle.remove()
        for k in layers:
            pieces[k].append(torch.cat(vit_grids_by_row(captured[k], chunk_grid, visual.config.spatial_merge_size)))
        offset += count
    if offset != len(pixels): raise ValueError('Reference grid does not cover pixels')
    return {k: torch.cat(v) for k, v in pieces.items()}


def check_feature_parity(reader, report, out):
    from student_pilot.precision_parity import feature_parity
    pixels, grid = reader._prepare((1, 2, 3, 4), (320, 448))
    visual = reader.visual
    start = time.monotonic()
    reference = native_taps(visual, pixels, grid, reader.layers, 4, packed_video=True)
    repeat = native_taps(visual, pixels, grid, reader.layers, reader.chunk_size)
    reference_seconds = time.monotonic()-start
    expected_hashes = []
    offset = 0
    for t, h, w in grid.tolist():
        if t != 1: raise ValueError('Expected four independent image frames')
        expected_hashes.append(tensor_sha(pixels[offset:offset+h*w]))
        offset += h*w
    actual_hashes = []
    def observe(module, args, kwargs):
        offset = 0
        for t, h, w in kwargs['grid_thw'].tolist():
            if t != 1: raise ValueError('Reread frame identity changed')
            actual_hashes.append(tensor_sha(args[0][offset:offset+h*w]))
            offset += h*w
    handle = visual.register_forward_pre_hook(observe, with_kwargs=True)
    try:
        actual = reader.features((1, 2, 3, 4), (320, 448))
    finally:
        handle.remove()
    gate = feature_parity(reference, repeat, actual)
    gate.update(scope='native vision prefill, no LM', reference_seconds=reference_seconds,
        same_card_precision_model=True, dtype=str(pixels.dtype), device=str(pixels.device),
        reference_batch=4, repeat_batch=reader.chunk_size, actual_batch=reader.chunk_size,
        attention_implementation=visual.config._attn_implementation, padding='none',
        slots=[1, 2, 3, 4], grid=grid.tolist(), reference_frame_pixel_hashes=expected_hashes,
        actual_frame_pixel_hashes=actual_hashes, inputs_equal=expected_hashes==actual_hashes)
    gate['passed'] = gate['passed'] and gate['inputs_equal']
    report['bf16_parity'] = gate
    if not gate['passed']: report['status'] = 'feature_parity_failed'
    write_report(out, report)
    print(json.dumps(dict(bf16_parity=gate)), flush=True)
    if not gate['passed']: raise AssertionError('ViT parity failed; inspect LATENCY.json')
    reader.clear_cache()


def load_vision(args):
    from safetensors import safe_open
    from transformers import Qwen3_5Config, Qwen2VLImageProcessorPil
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
    config = Qwen3_5Config.from_dict(json.loads(args.config.read_text()))
    config.vision_config._attn_implementation = 'sdpa'
    index_path = args.weights / 'model.safetensors.index.json'
    index = json.loads(index_path.read_text())['weight_map']
    names = sorted(k for k in index if k.startswith('model.visual.'))
    if not names:
        raise ValueError('Checkpoint has no model.visual weights')
    state, pins = {}, {}
    # Only selected tensors are read; unrelated LM tensor pages stay untouched.
    for shard in sorted(set(index[n] for n in names)):
        if Path(shard).name != shard:
            raise ValueError('Shard name must be a basename')
        with safe_open(args.weights / shard, framework='pt', device='cpu') as handle:
            for name in (n for n in names if index[n] == shard):
                value = handle.get_tensor(name)
                pins[name] = dict(shard=shard, sha256=tensor_sha(value), shape=list(value.shape))
                state[name[len('model.visual.'):]] = value
    visual = Qwen3_5VisionModel(config.vision_config)
    visual.load_state_dict(state, strict=True, assign=True)
    # Native rotary buffers stay FP32, as in the production loader.
    for p in visual.parameters():
        p.data = p.data.to(torch.bfloat16)
    model = torch.nn.Module()
    model.model = torch.nn.Module()
    model.model.visual = visual
    model.to(args.device).eval()
    processor = Qwen2VLImageProcessorPil(**json.loads(args.processor_config.read_text()))
    return model, processor, dict(config_sha256=file_sha(args.config),
        processor_sha256=file_sha(args.processor_config), index_sha256=file_sha(index_path), tensors=pins)


def write_report(out, report):
    out.mkdir(parents=True, exist_ok=True)
    (out / 'LATENCY.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['ViT-only smoke; four synthetic native RGB frames. No evaluation scans are read.',
             'Peak memory covers the loaded ViT and re-read, without the 9B LM or geometry towers.', '',
             '| Width × height | SDPA backend | Seconds/frame | Peak allocated MiB | Extra peak MiB | Observed attention |',
             '|---|---|---:|---:|---:|---|']
    for row in report['rows']:
        if row['status'] == 'ok':
            lines.append(f"| {row['size_hw'][1]} × {row['size_hw'][0]} | {row['backend']} | "
                f"{row['seconds_per_frame']:.6f} | {row['peak_allocated_mib']:.1f} | "
                f"{row['extra_peak_mib']:.1f} | {', '.join(row['attention_events'])} |")
        else:
            lines.append(f"| {row['size_hw'][1]} × {row['size_hw'][0]} | {row['backend']} | "
                         f"{row['status']} | — | — | {row.get('error', '')} |")
    lines += ['', 'Status: ' + report['status'],
              'Every successful row uses one warm-up, three timed reads and one separately profiled read.',
              'Timing includes RGB preparation, copies, four tap captures and cache insertion; cache is cleared before each read.',
              'A failed forced backend is recorded, never silently replaced. OOM stops the run.']
    (out / 'LATENCY.md').write_text('\n'.join(lines) + '\n')


@stage_assertions(5)
def run(args):
    cpu=getattr(sys,"_acceptance_cpu_e2e",None)
    if args.start_check:
        from acceptance_start_check import begin, vision_check
        begin(5,args)
        vision_check(args, load_vision)
        return 0
    from student_pilot.reread import ReRead
    from student_pilot import reread
    from student_pilot.point_depth_head import vit_grids_by_row
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionAttention
    torch.set_num_threads(1 if cpu else 4)
    if not cpu and not torch.cuda.is_available():
        raise RuntimeError('CUDA is required; this runner never substitutes CPU latency')
    if not cpu: torch.cuda.set_device(torch.device(args.device))
    model, processor, inputs = cpu.vision(args) if cpu else load_vision(args)
    rng = np.random.default_rng(130)
    frames = {i: rng.integers(0, 256, (480, 640, 3), dtype=np.uint8) for i in range(1, 5)}
    configuration = dict(seed=130, frames=4, chunk_size=args.chunk_size, layers=[9, 17, 25, 27],
        dtype='bfloat16', sizes_hw=[[480, 640], [768, 1024]], warmups=1, repeats=3,
        profiled_reads=1, backends=['auto', 'math', 'flash', 'efficient', 'cudnn'],
        parity_policy='pooled-reference-floor-r12', max_seconds=600)
    if cpu: configuration.update(dtype='float32',backends=['auto','math'],layers=[1,2,3])
    inputs['synthetic_rgb_sha256'] = {str(i): hashlib.sha256(v.tobytes()).hexdigest() for i, v in frames.items()}
    report = dict(status='running', gpu='cpu' if cpu else torch.cuda.get_device_name(), torch=torch.__version__,
        inputs=inputs, configuration=configuration, rows=[],
        code_sha256={str(Path(__file__).name): file_sha(__file__), 'reread.py':file_sha(reread.__file__)},
        vision_attention_source_sha256=hashlib.sha256(inspect.getsource(Qwen3_5VisionAttention.forward).encode()).hexdigest(),
        config_sha256=hashlib.sha256(json.dumps(configuration, sort_keys=True).encode()).hexdigest())
    started = time.monotonic()
    reader = ReRead(model, chunk_size=args.chunk_size, layers=configuration["layers"])
    reader.bind_clip('a'*64, frames, processor=processor)
    check_feature_parity(reader, report, args.out)
    for size in configuration['sizes_hw']:
        for backend in configuration['backends']:
            if time.monotonic() - started > configuration['max_seconds']:
                report['status'] = 'time_budget_exhausted'
                write_report(args.out, report)
                return 2
            reader.sdpa_backend = backend
            row = dict(size_hw=size, backend=backend, status='running')
            try:
                reader.clear_cache()
                reader.features((1, 2, 3, 4), tuple(size))
                cpu.sync() if cpu else torch.cuda.synchronize()
                times, peaks, extras, reserved = [], [], [], []
                for _ in range(3):
                    reader.clear_cache()
                    cpu.sync() if cpu else torch.cuda.synchronize()
                    baseline = 0 if cpu else torch.cuda.memory_allocated()
                    cpu.sync() if cpu else torch.cuda.reset_peak_memory_stats()
                    at = time.perf_counter()
                    reader.features((1, 2, 3, 4), tuple(size))
                    cpu.sync() if cpu else torch.cuda.synchronize()
                    times.append(time.perf_counter() - at)
                    peaks.append(0 if cpu else torch.cuda.max_memory_allocated() / 2**20)
                    extras.append(0 if cpu else (torch.cuda.max_memory_allocated() - baseline) / 2**20)
                    reserved.append(0 if cpu else torch.cuda.max_memory_reserved() / 2**20)
                reader.clear_cache()
                with (cpu.profile() if cpu else torch.profiler.profile(activities=[
                        torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA])) as prof:
                    reader.features((1, 2, 3, 4), tuple(size))
                    cpu.sync() if cpu else torch.cuda.synchronize()
                events = sorted({e.key for e in prof.key_averages()
                    if 'scaled_dot_product' in e.key or 'flash_attn' in e.key})
                if not any('scaled_dot_product_attention' in e for e in events):
                    raise RuntimeError('Profiler did not observe torch SDPA')
                row.update(status='ok', seconds_per_frame=statistics.median(times) / 4,
                    trial_seconds=times, peak_allocated_mib=max(peaks), extra_peak_mib=max(extras),
                    peak_reserved_mib=max(reserved), attention_events=events)
            except torch.cuda.OutOfMemoryError as exc:
                row.update(status='oom_stop', error=str(exc))
                report['rows'].append(row)
                report['status'] = 'oom_stop_no_retry'
                write_report(args.out, report)
                return 2
            except RuntimeError as exc:
                message = str(exc)
                if not any(s in message.lower() for s in ('no available kernel', 'no viable backend',
                                                          'not supported', 'not compiled')):
                    raise
                row.update(status='unsupported', error=message)
            report['rows'].append(row)
            write_report(args.out, report)
    report['status'] = 'complete_vision_only'
    report['elapsed_seconds'] = time.monotonic() - started
    report['successful_vision_forwards'] = reader.forward_calls + 1 + (4+args.chunk_size-1)//args.chunk_size
    write_report(args.out, report)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start-check', action='store_true')
    parser.add_argument('--weights', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--processor-config', type=Path, required=True)
    parser.add_argument('--device', default='cuda:0')
    parser.add_argument('--chunk-size', type=int, default=1)
    parser.add_argument('--out', type=Path, required=True)
    raise SystemExit(run(parser.parse_args()))
