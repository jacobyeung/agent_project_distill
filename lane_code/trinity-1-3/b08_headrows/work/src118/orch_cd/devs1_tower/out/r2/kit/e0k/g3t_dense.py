"""G3T on each E0 clip's dense frames (DENSE.json from e0k.anchors), heads read at the 32 clip anchors.
Writes ttower's n64 schema (raw_pose over all frames, raw_pose32 at the anchor slots, frame_indices, anchor_slots), so
rk.geom heads turns it into G3T x s heads unchanged. Reuses rkit's pinned G3T source and weight checks.
usage: python -m e0k.g3t_dense --dense DENSE.json --weights G3T_DIR --device cuda:0 --rank R --world W --out DIR
"""
import argparse
import fcntl
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np

from rk import g3t as R  # noqa: E402


def run(dense, weights, device, rank, world, out, chunk=8):
    import torch
    spec = json.loads(Path(dense).read_text())
    root = Path(spec['render_root'])
    weights, out = Path(weights).resolve(), Path(out).resolve()
    pins = {name: R.sha256(weights/name) for name in ('config.json', 'model.safetensors')}
    if pins != {'config.json': R.CONFIG_SHA256, 'model.safetensors': R.WEIGHTS_SHA256}:
        raise ValueError('G3T config/weight sha256 mismatch')
    out.mkdir(parents=True, exist_ok=True)
    request = dict(dense_sha256=R.sha256(dense), weights=pins, source_sha256=R.sha256(R.VENDOR/'SOURCES.json'))
    counts, model, log = dict(completed=0, resumed=0, failures={}), None, out/f'journal_{rank}.jsonl'
    with R.vendor_source() as native:
        for scene, clip in sorted(spec['clips'].items())[rank::world]:
            key = scene.replace('/', '__')
            dest, receipt = out/(key+'.npz'), out/(key+'.json')
            fingerprint = R.digest(dict(request, scene=scene))
            with (out/(key+'.lock')).open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                try:
                    if receipt.exists() and dest.exists():
                        previous = json.loads(receipt.read_text())
                        if previous.get('request_sha256') == fingerprint and previous.get('npz_sha256') == R.sha256(dest):
                            counts['resumed'] += 1
                            continue
                    images = []
                    for pin in clip['frames']:
                        raw = (root/pin['path']).read_bytes()
                        if hashlib.sha256(raw).hexdigest() != pin['sha256']:
                            raise ValueError('PNG sha256 mismatch: '+pin['path'])
                        images.append(raw)
                    slots, hw = list(clip['anchor_slots']), tuple(clip['hw'])
                    if len(slots) != 32 or slots[0] != 0 or any(b <= a for a, b in zip(slots, slots[1:])):
                        raise ValueError('Anchor slots must be 32 increasing positions starting at 0')
                    if model is None:
                        model = native.N1(None, weights, device)
                    started = time.monotonic()
                    for size in ([chunk, 1] if chunk != 1 else [1]):
                        try:
                            with R.ExitBuffers(images) as buffers:
                                values = model.extract(buffers, slots, hw, size)
                            break
                        except torch.cuda.OutOfMemoryError:
                            if size == 1:
                                raise
                            gc.collect()
                            torch.cuda.empty_cache()
                    raw_pose = np.asarray(values['raw_pose'])
                    if raw_pose.shape != (len(images), 9):
                        raise ValueError(f'Expected one pose per dense frame, got {raw_pose.shape}')
                    values.update(raw_pose32=raw_pose[slots].copy(), anchor_slots=np.asarray(slots, np.int64),
                                  frame_indices=np.asarray(clip['frame_indices'], np.int64),
                                  source_hw=np.asarray(hw, np.int64), seconds=np.array(time.monotonic()-started),
                                  dpt_chunk_size=np.array(size), encoded_input_frames=np.array(len(images)))
                    for name, shape in dict(raw_pose32=(32, 9), gravity_up=(3,), depth_grid=(32, 51, 51),
                                            depth_conf_grid=(32, 51, 51), grid_uv=(51,)).items():
                        if np.shape(values[name]) != shape:
                            raise ValueError(f'Invalid {name} shape: {np.shape(values[name])}')
                    temporary = dest.with_suffix('.npz.part')
                    with temporary.open('wb') as stream:
                        np.savez(stream, **values)
                    os.replace(temporary, dest)
                    record = dict(key=key, request_sha256=fingerprint, npz_sha256=R.sha256(dest), frames=len(images),
                                  seconds=float(values['seconds']), chunk=size,
                                  peak_memory={n: int(values[n]) for n in ('peak_allocated_bytes', 'peak_reserved_bytes')})
                    R.save_json(receipt, record)
                    R.journal(log, dict(event='complete', **record))
                    counts['completed'] += 1
                    print(json.dumps(dict(event='complete', key=key, frames=len(images), seconds=record['seconds'])), flush=True)
                except Exception as error:
                    counts['failures'][key] = f'{type(error).__name__}: {error}'
                    R.journal(log, dict(event='failed', key=key, error=counts['failures'][key]))
    R.save_json(out/f'rank_{rank}.json', counts)
    return counts


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('dense', 'weights', 'out'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--device', required=True)
    p.add_argument('--rank', type=int, default=0)
    p.add_argument('--world', type=int, default=1)
    p.add_argument('--chunk', type=int, default=8)
    a = p.parse_args(argv)
    print(json.dumps(run(a.dense, a.weights, a.device, a.rank, a.world, a.out, a.chunk)))


if __name__ == '__main__':
    main()
