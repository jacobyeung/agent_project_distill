G=/scratch/jjyeung/orch_n30/geo_k1
cat > $G/k1towers/k1_infer.py <<'PYEOF'
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


def bind(c, folder, prefix=None):
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
        p = f['path']
        if prefix:
            old, new = prefix
            if not p.startswith(old):
                raise ValueError('frame path outside --frame-prefix: ' + p)
            p = new + p[len(old):]
        p = Path(p)
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
    ap.add_argument('--frame-prefix', help='OLD=NEW: read manifest frame paths from a staged copy (sha256 still checked)')
    ap.add_argument('--smoke-anchors', type=int,
                    help='CPU code-path smoke only: run on N evenly spaced anchors; output root must contain /smoke')
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if not str(out).startswith(('/scratch/', '/dev/shm/')):
        raise PermissionError('output must be node-local (/scratch or /dev/shm)')
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
            paths, hashes, frames, slots = bind(c, index[key], args.frame_prefix and args.frame_prefix.split('=', 1))
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
cat > $G/k1towers/decide.py <<'PYEOF'
"""Apply the pre-registered C-rule (GEO_TOWERS_K1_PREREG_20261116.md) to k1_price output via E3's agg.py.

Usage: python decide.py CAPTURES_DIR FITS OUT.json [--heldout-go FILE]
Train tables are always computed. Held-out tables are computed only with --heldout-go naming an ORCH note that
holds a line 'GO heldout' (written after the independent review). Reference: S4+G1 (distance), S4+G1+R0 (room).
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMARY = {'moge2': 'moge2_scale', 'mapanything': 'mapanything_native', 'da3': 'da3_native', 'pi3x': 'pi3x_native'}
REF = 'S4+G1'
LINE = re.compile(r'^(\S+)\s+(-?[\d.]+) \[\s*(-?[\d.]+),\s*(-?[\d.]+)\] ref=(\d+)(.*)$')
DIFF = re.compile(r'\| vs (\S+): ([-+][\d.]+) \[([-+][\d.]+),([-+][\d.]+)\]')


def table(caps, split, fits, agg):
    text = subprocess.run([sys.executable, '-B', str(agg), caps, split, fits, REF], check=True,
                          capture_output=True, text=True).stdout
    out, typ = {}, None
    for line in text.splitlines():
        if line.startswith('## '):
            typ = line.split()[1]
            out[typ] = dict(header=line, arms={})
            continue
        m = LINE.match(line)
        if m and typ:
            arm = dict(mean=float(m[2]), lo=float(m[3]), hi=float(m[4]), refusals=int(m[5]))
            d = DIFF.search(m[6])
            if d:
                arm.update(vs=d[1], diff=float(d[2]), diff_lo=float(d[3]), diff_hi=float(d[4]))
            out[typ]['arms'][m[1]] = arm
    return text, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('captures'); ap.add_argument('fits'); ap.add_argument('out')
    ap.add_argument('--agg', default=str(HERE / 'agg.py'))
    ap.add_argument('--heldout-go')
    a = ap.parse_args()
    splits = ['train']
    if a.heldout_go:
        if not any(l.strip() == 'GO heldout' for l in Path(a.heldout_go).read_text().splitlines()):
            raise PermissionError('held-out tables need an ORCH note with a "GO heldout" line')
        splits.append('heldout')
    res = dict(prereg_sha256='dd40e6d26a723300547c84b72add275bd2488993c2f70cd1b64fba7ae29b5c88', reference=REF, tables={}, raw={})
    for s in splits:
        res['raw'][s], res['tables'][s] = table(a.captures, s, a.fits, a.agg)
    tr = res['tables']['train']; ho = res['tables'].get('heldout')
    keys = {'object_abs_distance': '', 'room_size_estimation': '+R0'}
    dec = {}
    for m, arm in PRIMARY.items():
        d = {}
        for typ, suf in keys.items():
            t = tr.get(typ, {}).get('arms', {}).get(arm + suf)
            if not t:
                d[typ] = dict(status='absent'); continue
            row = dict(train_mean=t['mean'], train_diff=t.get('diff'), train_diff_lo=t.get('diff_lo'))
            if ho:
                h = ho.get(typ, {}).get('arms', {}).get(arm + suf, {})
                ref = ho.get(typ, {}).get('arms', {}).get(REF + suf, {})
                row.update(heldout_mean=h.get('mean'), heldout_diff=h.get('diff'))
                row['qualifies'] = bool(row['train_diff_lo'] is not None and row['train_diff_lo'] > 0
                                        and h.get('diff') is not None and h['diff'] > 0)
                if typ == 'object_abs_distance':
                    row['bar'] = (ref.get('mean') or 0) + 5
                else:
                    row['bar'], row['bar_sensitivity'] = 73.4, 79.0
                row['clears_bar'] = h.get('mean') is not None and h['mean'] >= row['bar']
            d[typ] = row
        if ho:
            q = [t for t in keys if d[t].get('qualifies')]
            other_ok = all((d[o].get('train_diff_lo') or -1e9) >= -2 for t in q for o in keys if o != t)
            d['replaces_g3t_candidate'] = bool(q) and other_ok
        dec[m] = d
    if ho:
        cands = [m for m in dec if dec[m].get('replaces_g3t_candidate')]
        res['winner'] = max(cands, key=lambda m: max(dec[m][t]['train_mean'] for t in keys if dec[m][t].get('qualifies')),
                            default='G3T')
    res['decision'] = dec
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(dec, indent=1)); print(res.get('winner', 'heldout not read'))


if __name__ == '__main__':
    main()
PYEOF
set -u
S=/dev/shm/jjyeung/b14; M=/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json
W=/scratch/jjyeung/orch_n30/geo_k1/stage; mkdir -p $W/code $W/k1/run_tower_sam_2; date -u
/scratch/jjyeung/envs/planner_local_v1/bin/python - <<PY
import json, glob, os, shutil, numpy as np
m = json.load(open('$M'))
fr = sorted({f['path'][len('/scratch/jjyeung/'):] for c in m['captures'] for f in c['dense_frames']})
assert all(p.startswith('k1_frames/') for p in fr)
n = 0
for d in sorted(glob.glob('/scratch/jjyeung/k1/run_tower_sam_2/*/PHASE_COMPLETE.json')):
    src = os.path.dirname(d); dst = '$W/k1/run_tower_sam_2/' + os.path.basename(src); os.makedirs(dst, exist_ok=True)
    shutil.copy2(d, dst)
    with np.load(src + '/tower.npz', allow_pickle=False) as z:
        np.savez(dst + '/tower.npz', frame_indices=z['frame_indices'], anchor_slots=z['anchor_slots'])
    n += 1
kit = ['geo_bakeoff_kit/' + x for x in ['KIT_SEAL.json', 'PAYLOAD.json', 'runtime', 'work', 'assets/downloads.jsonl', 'assets/moge2']]
kit += sorted(x[len('/scratch/jjyeung/'):] for x in glob.glob('/scratch/jjyeung/geo_bakeoff_kit/assets/*-src'))
open('$W/files_common.txt', 'w').write('\n'.join(kit + fr) + '\n')
print('towers', n, 'frames', len(fr), 'frame_GB', sum(os.path.getsize('/scratch/jjyeung/' + p) for p in fr) / 1e9)
PY
cp -p /scratch/jjyeung/orch_n30/geo_k1/k1towers/*.py $W/code/ && cp -p $M $W/
du -sh $W/k1
cd /scratch/jjyeung
time (tar cf - -T $W/files_common.txt -C $W code k1 K1_MANIFEST.arkit_timing.json | timeout 900 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-13.ib "mkdir -p $S && tar xf - -C $S && du -sh $S && du -sh /dev/shm/jjyeung/* | grep -v '^[0-9.]*[KM]'") 2>&1 | tail -12
