"""Run the pinned AWS G3T inference source on verified 32-PNG selections."""
import argparse
from contextlib import contextmanager
import fcntl
import gc
import hashlib
import importlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import time

import numpy as np

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

VENDOR = Path(__file__).parent / 'vendor/g3t'
CONFIG_SHA256 = '5aeb2acd008d41a1cac52e10216fbf35e8dfeb2ce26b89bb24e7ccc4ee0817d7'
WEIGHTS_SHA256 = 'd460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702'


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def save_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.part')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    os.replace(temporary, path)


@contextmanager
def vendor_source():
    """Isolate the upstream absolute imports (u0, e, p) from other adapters."""
    pins = json.loads((VENDOR / 'SOURCES.json').read_text())
    for name, expected in pins['files'].items():
        if sha256(VENDOR / name) != expected:
            raise ValueError('Vendored source changed: ' + name)
    def owned(name):
        return name in ('e', 'p', 'u0', 'rk.vendor.g3t.n') or name.startswith('u0.')
    previous = {k: v for k, v in sys.modules.items() if owned(k)}
    for name in previous:
        sys.modules.pop(name)
    search = sys.path[:]
    sys.path.insert(0, str(VENDOR))
    try:
        yield importlib.import_module('rk.vendor.g3t.n')
    finally:
        for name in list(sys.modules):
            if owned(name):
                sys.modules.pop(name)
        sys.modules.update(previous)
        sys.path[:] = search


def manifest_entries(path):
    """Read mdg_eval.manifest_entries' schema and canonical selection identities."""
    value = json.loads(Path(path).read_text())
    rows = value if isinstance(value, list) else value.get('selections', value.get('entries', value.get('items')))
    if not isinstance(rows, list) or not rows:
        raise ValueError('Manifest requires a nonempty selections/entries/items list')
    result, scenes = {}, set()
    for original in rows:
        row = dict(original)
        video = Path(row['video_rel'])
        row.setdefault('scene', str(video.with_suffix('')))
        indices, fps, total = row['frame_indices'], row['fps'], row['total_num_frames']
        if (video.is_absolute() or '..' in video.parts or len(indices) != 32 or indices != sorted(indices)
                or type(total) is not int or total < 1 or type(fps) not in (int, float)
                or not math.isfinite(fps) or fps <= 0
                or any(type(i) is not int or not 0 <= i < total for i in indices)
                or len(row['frames']) != 32):
            raise ValueError('Invalid anchor selection')
        for pin, index in zip(row['frames'], indices):
            if 'index' in pin and pin['index'] != index:
                raise ValueError('PNG index differs from selection')
        for name in ('anchor_pixel_sha256', 'duplicate_pixel_sha256'):
            if not re.fullmatch('[0-9a-f]{64}', row[name]):
                raise ValueError('Invalid anchor pixel pin')
        if not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+', row['scene']):
            raise ValueError('Require dataset/scene identity')
        key = digest({k: row[k] for k in ('video_rel', 'frame_indices', 'fps', 'total_num_frames')})
        if key in result or row['scene'] in scenes:
            raise ValueError('Duplicate selection or multiple selections for one output scene')
        result[key] = row
        scenes.add(row['scene'])
    return result


def pixel_digest(arrays):
    stream = io.BytesIO()
    np.save(stream, arrays, allow_pickle=False)
    return hashlib.sha256(stream.getbuffer()).hexdigest()


def load_images(entry, root):
    from PIL import Image
    root = Path(root).resolve(strict=True)
    images, arrays = [], []
    for pin in entry['frames']:
        path = Path(pin.get('path', pin.get('png')))
        path = (path if path.is_absolute() else root / path).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError('PNG escaped supplied root')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != pin['sha256']:
            raise ValueError('PNG sha256 mismatch: ' + str(path))
        with Image.open(io.BytesIO(data)) as image:
            if image.mode != 'RGB' or image.format != 'PNG':
                raise ValueError('Require lossless RGB PNG')
            arrays.append(np.array(image))
        images.append(data)
    arrays = np.stack(arrays)
    if (pixel_digest(arrays) != entry['anchor_pixel_sha256'] or
            pixel_digest(np.repeat(arrays, 2, axis=0)) != entry['duplicate_pixel_sha256']):
        raise ValueError('Decoded anchor/duplicate pixels differ')
    return images, arrays.shape[1:3]


def journal(path, event):
    with path.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.write(json.dumps(event, sort_keys=True, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def run(manifest, png_root, weights, device, rank, world, out, chunk=8):
    import torch
    if world < 1 or not 0 <= rank < world or chunk < 1:
        raise ValueError('Invalid rank/world/chunk')
    if not re.fullmatch(r'cpu|cuda:[0-9]+', str(device)):
        raise ValueError('Device must be cpu or cuda:N')
    weights, out = Path(weights).resolve(), Path(out).resolve()
    pins = {name: sha256(weights / name) for name in ('config.json', 'model.safetensors')}
    if pins != {'config.json': CONFIG_SHA256, 'model.safetensors': WEIGHTS_SHA256}:
        raise ValueError('G3T config/weight sha256 mismatch')
    entries = manifest_entries(manifest)
    out.mkdir(parents=True, exist_ok=True)
    request = dict(manifest_sha256=sha256(manifest), weights=pins,
                   source_sha256=sha256(VENDOR / 'SOURCES.json'))
    counts = dict(completed=0, resumed=0, failures={})
    log = out / f'journal_{rank}.jsonl'
    model = None
    with vendor_source() as native:
        for selection, entry in list(entries.items())[rank::world]:
            key = entry['scene'].replace('/', '__')
            dest = out / (key + '.npz')
            receipt = dest.with_suffix('.json')
            fingerprint = digest(dict(request, selection=selection))
            with (out / (key + '.lock')).open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                try:
                    images, hw = load_images(entry, png_root)
                    if receipt.exists() and dest.exists():
                        previous = json.loads(receipt.read_text())
                        if previous.get('request_sha256') == fingerprint and previous.get('npz_sha256') == sha256(dest):
                            counts['resumed'] += 1
                            journal(log, dict(event='resume', key=key))
                            continue
                    journal(log, dict(event='start', key=key, request_sha256=fingerprint))
                    if model is None:
                        model = native.N1(None, weights, device)
                    started, attempts = time.monotonic(), []
                    for size in ([chunk, 1] if chunk != 1 else [1]):
                        try:
                            # Fresh buffers also reset file positions after an OOM.
                            with ExitBuffers(images) as buffers:
                                values = model.extract(buffers, list(range(32)), hw, size)
                            break
                        except torch.cuda.OutOfMemoryError as error:
                            attempts.append(dict(chunk=size, error_sha256=hashlib.sha256(str(error).encode()).hexdigest()))
                            if size == 1:
                                raise
                            gc.collect()
                            if str(device).startswith('cuda:'):
                                with torch.cuda.device(device):
                                    torch.cuda.empty_cache()
                    values.update(raw_pose32=np.asarray(values['raw_pose']).copy(),
                                  frame_indices=np.asarray(entry['frame_indices'], dtype=np.int64),
                                  anchor_slots=np.arange(32, dtype=np.int64), source_hw=np.asarray(hw, dtype=np.int64),
                                  seconds=np.array(time.monotonic() - started), dpt_chunk_size=np.array(size))
                    expected = dict(raw_pose32=(32, 9), gravity_up=(3,), depth_grid=(32, 51, 51),
                                    depth_conf_grid=(32, 51, 51), points_grid=(32, 51, 51, 3), grid_uv=(51,))
                    for name, shape in expected.items():
                        if np.shape(values[name]) != shape:
                            raise ValueError(f'Invalid {name} shape: {np.shape(values[name])}')
                    temporary = dest.with_suffix('.npz.part')
                    with temporary.open('wb') as stream:
                        np.savez(stream, **values)
                    os.replace(temporary, dest)
                    record = dict(key=key, selection=selection, request_sha256=fingerprint, inputs=request,
                                  npz_sha256=sha256(dest), seconds=float(values['seconds']), chunk=size, retries=attempts,
                                  peak_memory={n: int(values[n]) for n in ('peak_allocated_bytes', 'peak_reserved_bytes')})
                    save_json(receipt, record)
                    journal(log, dict(event='complete', **record))
                    counts['completed'] += 1
                    print(json.dumps(dict(event='complete', key=key, seconds=record['seconds'])), flush=True)
                    del values
                except Exception as error:
                    counts['failures'][key] = f'{type(error).__name__}: {error}'
                    journal(log, dict(event='failed', key=key, error=counts['failures'][key]))
    save_json(out / f'rank_{rank}.json', counts)
    return counts


class ExitBuffers:
    def __init__(self, data):
        self.buffers = [io.BytesIO(value) for value in data]

    def __enter__(self):
        return self.buffers

    def __exit__(self, *args):
        for buffer in self.buffers:
            buffer.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('run')
    for name in ('manifest', 'png-root', 'weights', 'out'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--device', required=True)
    p.add_argument('--rank', required=True, type=int)
    p.add_argument('--world', required=True, type=int)
    p.add_argument('--chunk', default=8, type=int)
    a = parser.parse_args(argv)
    result = run(a.manifest, a.png_root, a.weights, a.device, a.rank, a.world, a.out, a.chunk)
    return int(bool(result['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
