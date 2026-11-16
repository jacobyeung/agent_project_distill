G=/scratch/jjyeung/orch_n30/geo_k1; K=/scratch/jjyeung/geo_bakeoff_kit; cd $G; date -u
cat > $G/k1towers/k1_infer.py.new <<'PYEOF'
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
    ap.add_argument('--smoke-anchors', type=int,
                    help='CPU code-path smoke only: run on N evenly spaced anchors; output root must contain /smoke')
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if not str(out).startswith('/scratch/'):
        raise PermissionError('output must be node-local /scratch')
    if args.smoke_anchors and '/smoke' not in str(out):
        raise ValueError('smoke outputs must live under a /smoke path so pricing never reads them')
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
            anchor_indices = np.asarray(c['anchor_indices'])
            smoke = {}
            if args.smoke_anchors:
                pos = np.linspace(0, 31, args.smoke_anchors).round().astype(int)
                sel = slots[pos]
                paths, hashes, frames = [paths[i] for i in sel], [hashes[i] for i in sel], frames[sel]
                slots, anchor_indices = np.arange(len(pos)), anchor_indices[pos]
                smoke = dict(smoke_anchor_pos=pos)
            if backend is None:
                backend = Backend(args.model, args.device, args.threads, args.go_file)
            if args.device == 'cuda':
                backend.torch.cuda.reset_peak_memory_stats()
            pred = backend.predict(paths)
            arrays = dict(frame_indices=frames, anchor_slots=slots, anchor_indices=anchor_indices, **smoke,
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
PYEOF
mv $G/k1towers/k1_infer.py.new $G/k1towers/k1_infer.py
cat > $G/k1towers/cpu_check.py.new <<'PYEOF'
"""Diagnostic for a CPU first pass: anchor depth and relative pose of one tower prediction against K1 GT.
Usage: python cpu_check.py MANIFEST PRED_ROOT CAPTURE   (reads GT; diagnostic only, never a decision input)"""
import hashlib, json, sys
from pathlib import Path
import numpy as np
man, root, cap = sys.argv[1:4]
c = next(c for c in json.loads(Path(man).read_text())['captures'] if c['canonical'] == cap)
key = hashlib.sha256(json.dumps(c, sort_keys=True, allow_nan=False).encode()).hexdigest()[:16]
for d in sorted(Path(root).glob("*/" + key)):
    if not (d / "pred.npz").is_file(): print(d.parent.name, "no pred"); continue
    z = np.load(d / 'pred.npz'); g = np.load(c['gt']['path'])
    if 'smoke_anchor_pos' in z.files:
        pos = z['smoke_anchor_pos'].astype(int); g = {k: g[k][pos] for k in ('depth', 'valid', 'K_frames', 'c2w')}
    slots = z['anchor_slots'].astype(int); depth = z['depth_grid64'][slots].astype(float)
    H, W = g['depth'].shape[1:]; ax = np.linspace(0, 1000, 51)
    x = np.clip(np.floor(ax / 1000 * W).astype(int), 0, W - 1); y = np.clip(np.floor(ax / 1000 * H).astype(int), 0, H - 1)
    t = g['depth'][:, y[:, None], x[None, :]].astype(float); valid = g['valid'].astype(bool); t[~valid] = np.nan
    ok = np.isfinite(t) & (t > 0) & np.isfinite(depth) & (depth > 0)
    r = np.median(t[ok] / depth[ok])
    out = dict(model=d.parent.name, n=int(ok.sum()), absrel=float(np.mean(np.abs(depth[ok] - t[ok]) / t[ok])),
               gt_over_pred_median=float(r), absrel_aligned=float(np.mean(np.abs(r * depth[ok] - t[ok]) / t[ok])),
               source_hw=z['source_hw'].tolist(), raster_hw=z['raster_hw'].tolist(), gt_hw=[int(H), int(W)],
               fx_pred_over_gt=float(np.median(z['intrinsics'][slots][valid, 0, 0] * W / z['source_hw'][1] / g['K_frames'][valid, 0, 0])),
               seconds=json.loads((d / 'DONE.json').read_text())['seconds'])
    if 'c2w' in z.files:
        P, G = z['c2w'][slots][valid], g['c2w'][valid]
        rel = lambda A: np.einsum('ij,njk->nik', np.linalg.inv(A[0]), A)
        Rp, Rg = rel(P)[:, :3, :3], rel(G)[:, :3, :3]
        ang = np.degrees(np.arccos(np.clip((np.einsum('nij,nij->n', Rp, Rg) - 1) / 2, -1, 1)))
        tp, tg = rel(P)[:, :3, 3], rel(G)[:, :3, 3]
        s = np.sum(tp * tg) / max(np.sum(tp * tp), 1e-12)
        out.update(rot_err_deg_median=float(np.median(ang)), trans_scale_gt_over_pred=float(s),
                   trans_err_m_median_after_scale=float(np.median(np.linalg.norm(s * tp - tg, axis=1))),
                   trans_err_m_median_native=float(np.median(np.linalg.norm(tp - tg, axis=1))))
    print(json.dumps(out))
PYEOF
mv $G/k1towers/cpu_check.py.new $G/k1towers/cpu_check.py
sha256sum -c <<"S"
17dcd557de74a3d5b708593b6bf470c034b00baa66b782aad3bd2b753be367ef  k1towers/k1_infer.py
e27275c562c4822d4d0000b7f09fff45eaf9845cac00c5474de35a0918966eae  k1towers/cpu_check.py
S
M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json; T=/scratch/jjyeung/k1/run_tower_sam_2
cat > logs/smoke_pi3x.sh <<EOS
source $K/work/kit_env.sh; set +e
export TMPDIR=$G/tmp XDG_CACHE_HOME=$G/tmp/cache HF_HOME=$G/tmp/hf TORCH_HOME=$G/tmp/torch CUDA_VISIBLE_DEVICES=
cd $G/tmp
/usr/bin/time -v $K/runtime/base/bin/python3 $G/k1towers/k1_infer.py --model pi3x --manifest $M --towers $T --out $G/smoke/pi3x --device cpu --threads 8 --captures scannet/scene0201_02 --smoke-anchors 16 > $G/logs/smoke_pi3x.log 2>&1
echo EXIT \$? >> $G/logs/smoke_pi3x.log
EOS
tmux new-window -t b14 -n smoke_pi3x "bash $G/logs/smoke_pi3x.sh"
/scratch/jjyeung/envs/planner_local_v1/bin/python -B k1towers/cpu_check.py $M pred_cpu scannet/scene0201_02
