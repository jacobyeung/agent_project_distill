"""K1 tower pass: 64 dense K1 frames in, one candidate tower's prediction out, per capture, resumable.

Runs inside the sealed geometry bake-off kit's runtime (source kit_env.sh first). The model code is the
kit's unchanged geo_bakeoff.backends.Backend; this file only binds K1 inputs and writes outputs.

Per capture it writes OUT/<digest16>/pred.npz and OUT/<digest16>/DONE.json:
  frame_indices (64), anchor_slots (32), anchor_indices (32), depth_grid64 (64,51,51) optical-axis depth
  sampled on the 0..1000 endpoint canvas grid (kit contract.sample_grid), intrinsics (64,3,3) in source
  pixels, c2w (64,4,4) OpenCV camera-to-world in the tower's own world (absent for MoGe-2), source_hw.
No GT is read. Writes only under --out.
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TOWER_FILES = ('raw_pose', 'frame_indices', 'anchor_slots')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def digest(value):
    # Same canonical digest as the K1 kit and E3's harness (json default separators, sorted keys).
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def tower_index(towers):
    index = {}
    for p in sorted(Path(towers).glob('*/PHASE_COMPLETE.json')):
        key = json.loads(p.read_text())['capture_sha256']
        if key in index:
            raise ValueError('duplicate tower receipt ' + key)
        index[key] = p.parent
    return index


def select(manifest, args):
    caps = manifest['captures']
    if args.captures:
        want = set(args.captures)
        caps = [c for c in caps if c['canonical'] in want]
        if len(caps) != len(want):
            raise ValueError('a requested capture is absent from the manifest')
    elif args.gt_only:
        caps = [c for c in caps if c.get('gt') and Path(c['gt']['path']).is_file()]
    if args.shard:
        i, n = map(int, args.shard.split('/'))
        caps = caps[i::n]
    return caps[:args.limit] if args.limit else caps


def bind(c, folder):
    """Check frame identities and return the 64 verified PNG paths in tower order."""
    with np.load(folder / 'tower.npz', allow_pickle=False) as z:
        frames, slots = z['frame_indices'].astype(int), z['anchor_slots'].astype(int)
    dense = c['dense_frames']
    if len(dense) != 64 or len(frames) != 64 or len(slots) != 32:
        raise ValueError('expected 64 dense frames and 32 anchors')
    if [int(f['index']) for f in dense] != frames.tolist():
        raise ValueError('manifest dense frame order differs from the tower frame_indices')
    if frames[slots].tolist() != list(c['anchor_indices']):
        raise ValueError('tower anchors differ from the manifest anchor_indices')
    paths, hashes = [], []
    for f in dense:
        p = Path(f['path'])
        h = sha(p)
        if h != f['sha256']:
            raise ValueError('dense frame sha256 mismatch: ' + str(p))
        paths.append(str(p))
        hashes.append(h)
    return paths, hashes, frames, slots


def done_ok(dest):
    d = dest / 'DONE.json'
    if not d.is_file() or not (dest / 'pred.npz').is_file():
        return False
    try:
        return json.loads(d.read_text())['pred_sha256'] == sha(dest / 'pred.npz')
    except (KeyError, ValueError):
        return False


def install_device_gate(go_file):
    """Replace the kit's inbox-bound GPU gate with this lane's: an ORCH card note with a GO line."""
    import geo_bakeoff.backends as backends

    def gate(device, go=None):
        if device == 'cpu':
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
            return
        if device != 'cuda' or not go_file:
            raise PermissionError('GPU use needs --go-file naming the orchestrator card note')
        lines = [x.strip() for x in Path(go_file).read_text().splitlines()]
        if not any(x == 'GO' or x.startswith('GO ') for x in lines):
            raise PermissionError('card note has no GO line')
        visible = os.environ.get('CUDA_VISIBLE_DEVICES', '')
        if not visible or ',' in visible or visible in ('-1', 'all'):
            raise PermissionError('exactly one GPU must be visible')
    backends.validate_device = gate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', choices=('moge2', 'mapanything', 'da3', 'pi3x'), required=True)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--towers', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    ap.add_argument('--go-file')
    ap.add_argument('--threads', type=int, default=8)
    ap.add_argument('--captures', nargs='+')
    ap.add_argument('--gt-only', action='store_true', help='only captures whose GT raster exists (the 296 priced)')
    ap.add_argument('--shard')
    ap.add_argument('--limit', type=int)
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if not str(out).startswith('/scratch/'):
        raise PermissionError('output must be node-local /scratch')
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text())
    index = tower_index(args.towers)
    caps = select(manifest, args)
    install_device_gate(args.go_file)
    from geo_bakeoff.backends import Backend
    from geo_bakeoff.contract import sample_grid
    code = {p.name: sha(p) for p in sorted(HERE.glob('*.py'))}
    import geo_bakeoff
    kit_code = {p.name: sha(p) for p in sorted(Path(geo_bakeoff.__file__).parent.glob('*.py'))}
    backend = None
    log = (out / 'progress.jsonl').open('a')
    for n, c in enumerate(caps):
        key = digest(c)
        if key not in index:
            raise ValueError('capture digest not in tower cache: ' + c['canonical'])
        dest = out / key[:16]
        if done_ok(dest):
            log.write(json.dumps(dict(capture=c['canonical'], state='resumed', n=n + 1, total=len(caps))) + '\n')
            log.flush()
            continue
        dest.mkdir(exist_ok=True)
        start = time.monotonic()
        try:
            paths, hashes, frames, slots = bind(c, index[key])
            if backend is None:
                backend = Backend(args.model, args.device, args.threads, args.go_file)
            if args.device == 'cuda':
                backend.torch.cuda.reset_peak_memory_stats()
            pred = backend.predict(paths)
            arrays = dict(frame_indices=frames, anchor_slots=slots, anchor_indices=np.asarray(c['anchor_indices']),
                          depth_grid64=sample_grid(pred.depth).astype(np.float32),
                          intrinsics=pred.intrinsics.astype(np.float64), source_hw=np.asarray(pred.source_hw),
                          raster_hw=np.asarray(pred.depth.shape[-2:]))
            if pred.c2w is not None:
                arrays['c2w'] = pred.c2w.astype(np.float64)
            tmp = dest / 'pred.tmp.npz'
            np.savez_compressed(tmp, **arrays)
            tmp.rename(dest / 'pred.npz')
            meta = dict(pred.metadata)
            receipt = dict(capture=c['canonical'], capture_sha256=key, model=args.model, device=args.device,
                           seconds=time.monotonic() - start, frame_sha256=hashes, tower_dir=str(index[key]),
                           manifest=str(manifest_path), manifest_sha256=sha(manifest_path),
                           pred_sha256=sha(dest / 'pred.npz'), code_sha256=code, kit_code_sha256=kit_code,
                           metadata=json.loads(json.dumps(meta, default=str)), gt_used=False,
                           host=os.uname().nodename, cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES', ''))
            if args.device == 'cuda':
                receipt.update(peak_allocated_bytes=backend.torch.cuda.max_memory_allocated(),
                               peak_reserved_bytes=backend.torch.cuda.max_memory_reserved())
            (dest / 'DONE.json').write_text(json.dumps(receipt, indent=1))
            state = 'done'
        except Exception as exc:  # recorded per capture; the capture's rows later score 0 for this arm
            (dest / f'FAILED_{int(time.time())}.json').write_text(json.dumps(dict(
                capture=c['canonical'], error=f'{type(exc).__name__}: {exc}', seconds=time.monotonic() - start)))
            state = 'failed:' + type(exc).__name__
            if isinstance(exc, (PermissionError, MemoryError)) or 'out of memory' in str(exc).lower():
                log.write(json.dumps(dict(capture=c['canonical'], state=state, fatal=True)) + '\n')
                log.flush()
                raise
        log.write(json.dumps(dict(capture=c['canonical'], state=state, n=n + 1, total=len(caps),
                                  seconds=round(time.monotonic() - start, 1))) + '\n')
        log.flush()
    print('COMPLETE', len(caps), flush=True)


if __name__ == '__main__':
    main()
