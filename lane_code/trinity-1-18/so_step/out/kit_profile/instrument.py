"""Temporary instrumentation of the imported, real optimize_step; no source-file edits."""
import ast
import contextlib
import functools
import inspect
import json
from pathlib import Path
import threading
import time

import torch


class Phases:
    def __init__(self, device):
        self.device = device
        self.records = []
        self.local = threading.local()

    @contextlib.contextmanager
    def scope(self, name):
        old = getattr(self.local, 'phase', '')
        self.local.phase = name
        tick = time.perf_counter()
        begin = end = None
        # Only main-thread ranges use CUDA events. CPU prefetch must stay CPU-only.
        if self.device.type == 'cuda' and threading.current_thread() is threading.main_thread():
            begin, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            begin.record()
        try:
            with torch.profiler.record_function('so/' + name):
                yield
        finally:
            if end is not None:
                end.record()
            self.records.append((name, time.perf_counter() - tick, begin, end))
            self.local.phase = old

    def table(self, destination):
        if self.device.type == 'cuda':
            torch.cuda.synchronize(self.device)
        sums = {}
        for name, wall, begin, end in self.records:
            row = sums.setdefault(name, dict(calls=0, host_seconds=0., stream_elapsed_seconds=0.))
            row['calls'] += 1
            row['host_seconds'] += wall
            row['stream_elapsed_seconds'] += begin.elapsed_time(end) / 1000 if begin else 0.
        Path(destination).write_text(json.dumps(sums, indent=2) + '\n')
        print('phase\tcalls\thost_s\tCUDA_stream_elapsed_s', flush=True)
        for name, row in sorted(sums.items()):
            print(f"{name}\t{row['calls']}\t{row['host_seconds']:.6f}\t{row['stream_elapsed_seconds']:.6f}", flush=True)
        return sums


def _with(name, body):
    return ast.With(items=[ast.withitem(context_expr=ast.Call(
        func=ast.Attribute(value=ast.Name(id='_so_phases', ctx=ast.Load()), attr='scope', ctx=ast.Load()),
        args=[ast.Constant(name)], keywords=[]))], body=body)


def instrument_step(run, phases):
    """Wrap existing statements, preserving their order and their actual implementation."""
    tree = ast.parse(inspect.getsource(run.optimize_step))
    function = tree.body[0]
    micro = next(n for n in function.body if isinstance(n, ast.For) and ast.unparse(n.target).startswith('(microstep,'))
    body = []
    metric_start = None
    for node in micro.body:
        text = ast.unparse(node)
        label = None
        if text.startswith('fetched = next('):
            label = 'data_wait_including_admission'
        elif text.startswith('batch, targets = (move(') or text.startswith('batch, targets = move('):
            label = 'host_to_device'
        elif text.startswith('result = model('):
            label = 'forward_total'
        elif isinstance(node, ast.Expr) and '.backward()' in text:
            label = 'backward_including_recompute_and_fsdp'
        elif 'torch.cuda.synchronize(device)' in text:
            label = 'explicit_preforward_sync'
        if text.startswith('for key, value in result['):
            metric_start = len(body)
        body.append(_with(label, [node]) if label else node)
    if metric_start is not None:
        body[metric_start:] = [_with('metrics_and_shapes', body[metric_start:])]
    micro.body = body
    post_start = next(i for i,n in enumerate(function.body) if ast.unparse(n).startswith('reduced = torch.tensor('))
    opt = next(i for i,n in enumerate(function.body) if ast.unparse(n) == 'optimizer.step()')
    function.body[post_start:opt + 1] = [
        _with('gradient_reduce_norm_clip_and_lr', function.body[post_start:opt]),
        _with('optimizer', [function.body[opt]])]
    ast.fix_missing_locations(tree)
    namespace = dict(run.__dict__, _so_phases=phases)
    exec(compile(tree, '<so-profile-optimize_step>', 'exec'), namespace)
    return namespace['optimize_step']


@contextlib.contextmanager
def hooks(run, model, phases):
    """Includes original forward and checkpoint re-entry; restores every wrapper."""
    changes = []

    def wrap(owner, name, label):
        original = getattr(owner, name)
        @functools.wraps(original)
        def call(*args, **kwargs):
            name_now = label
            if label == 'lm_layer':
                name_now += ('_recompute' if getattr(phases.local, 'phase', '') ==
                             'backward_including_recompute_and_fsdp' else '_forward')
            with phases.scope(name_now):
                return original(*args, **kwargs)
        changes.append((owner, name, original))
        setattr(owner, name, call)

    # FSDP may wrap children, so identify native module classes, not wrapper names.
    for name, module in model.named_modules():
        kind = type(module).__name__
        if kind in ('Qwen3_5DecoderLayer', 'Qwen3NextDecoderLayer'):
            wrap(module, 'forward', 'lm_layer')
        elif kind == 'Qwen3_5VisionModel':
            wrap(module, 'forward', 'private_vision' if 'auxiliary_heads' in name else 'base_vision')
        elif kind in ('CameraSupervision', 'PrivateDepth'):
            wrap(module, 'forward', 'head/' + kind)
    for name in ('check_row', 'move', 'memory_stats', 'own_values'):
        wrap(run, name, name)
    from torch.distributed.fsdp import _runtime_utils as runtime
    for name in ('_unshard', '_reduce_grad', '_prefetch_handle'):
        wrap(runtime, name, 'fsdp/' + name)
    try:
        yield
    finally:
        for owner, name, original in reversed(changes):
            setattr(owner, name, original)


def profiler_table(profiler, path):
    rows = []
    for event in profiler.key_averages():
        if event.key.startswith('so/') or any(s in event.key.lower() for s in ('nccl', 'memcpy', 'synchronize', '_local_scalar_dense')):
            rows.append(dict(name=event.key, count=event.count,
                             host_total_seconds=event.cpu_time_total / 1e6,
                             host_self_seconds=event.self_cpu_time_total / 1e6,
                             device_total_seconds=event.device_time_total / 1e6,
                             device_self_seconds=event.self_device_time_total / 1e6))
    Path(path).write_text(json.dumps(rows, indent=2) + '\n')
    print('PROFILE_TABLE ' + json.dumps(rows), flush=True)
