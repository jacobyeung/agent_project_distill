"""GTC-D step 1 (CPU, trinity-2-28): dense frames for arm d, decoded by the served rule, with an anchor sha256 check.

For each capture of the chosen datasets in lever6/gtc/out/FRAMES_GTC.json the dense set is the native frames from the first to
the last anchor at the dataset stride (scannet 5, scannetpp 24, arkit 2; P1_REPORT), plus every anchor (gtc_common.dense_indices;
counts must equal lists/SUMMARY.json).
Source kinds:
  mp4 (scannet, scannetpp): the VSI-590K mp4 from the governed stream, dense_src/<dataset>/<absolute source path>. Decode rule
    (k6 wd.py, reproduced in work/vid_rule.py): cv2.VideoCapture, sequential grab, frame j = native index j, INTER_AREA to 640x480
    only if the size differs, cv2.imencode PNG at IMWRITE_PNG_COMPRESSION 3. The PNG bytes are written unchanged.
  frames_dir (optional, e.g. arkit): --frames-dir <dataset>=<template>, where <template> contains {id} (the capture id after the
    slash) and names a directory of <native index:06d>.png files already produced by wa.py's rule (orient, 2.5x INTER_CUBIC,
    PNG compression 3). The selected files are copied byte for byte; nothing is re-encoded.
Check: every anchor's PNG bytes must reproduce its served sha256 (FRAMES_GTC). A capture with any mismatch (or a missing source
or frame) gets status SHA_MISMATCH / SOURCE_MISSING and is listed; it is reported, not substituted, and track.py skips it.
Output: dense/<dataset>/<capture stub>/<native index:06d>.png, a MANIFEST.json per capture, and dense/DENSE_D.json (per frame:
native index, position, is_anchor, slot, sha256, bytes, file). Size: --estimate prints the forecast from the served anchor sizes;
a run refuses when the forecast exceeds 60 GB or would leave under 200 GB free on /scratch.
Usage (SAM 3 interpreter, cv2 4.10: /scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python):
  python dense.py --estimate
  python dense.py [--datasets scannet,scannetpp] [--captures a,b] [--workers 8] [--out DIR] [--frames-dir arkit=/scratch/.../{id}]
"""
import argparse, hashlib, json, os, shutil, sys, time
from multiprocessing import Pool
from pathlib import Path
KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
import gtc_common as G

MAX_BYTES = 60e9
MIN_FREE = 200e9
SCHEMA = 'gtcd-dense-v1'
RULE = ('mp4: cv2.VideoCapture sequential grab, frame j = native index j, INTER_AREA to 640x480 only if the size differs, '
        'cv2.imencode PNG compression 3 (k6 wd.py); frames_dir: <index:06d>.png from wa.py\'s rule copied byte for byte; '
        'dense = first..last anchor at the dataset stride plus every anchor; each anchor must reproduce its served sha256')


def captures_for(frames, summary, datasets, only):
    per = {c['capture']: c for c in summary['per_capture']}
    out = []
    for c in frames['captures']:
        ds = G.DATASET_OF[c['native'][:2]]
        if ds not in datasets or (only and c['capture'] not in only):
            continue
        s = per[c['capture']]
        idx = G.dense_indices(c['anchor_indices'], G.STRIDE[ds])
        if s['stride'] != G.STRIDE[ds] or s['dense_frames'] != len(idx):
            raise ValueError('dense rule differs from lists/SUMMARY.json: '+c['capture'])
        out.append(dict(capture=c['capture'], native=c['native'], dataset=ds, stride=G.STRIDE[ds], indices=idx,
                        anchors={f['index']: dict(slot=f['slot'], sha256=f['sha256'], bytes=f['bytes']) for f in c['frames']},
                        summary=s))
    if only and {c['capture'] for c in out} != set(only):
        raise SystemExit('--captures names captures outside the chosen datasets')
    return out


def estimate(caps):
    rows = []
    for c in caps:
        mean = sum(a['bytes'] for a in c['anchors'].values())/len(c['anchors'])
        rows.append(dict(capture=c['capture'], dataset=c['dataset'], frames=len(c['indices']), bytes=int(mean*len(c['indices']))))
    tot = {}
    for r in rows:
        t = tot.setdefault(r['dataset'], dict(captures=0, frames=0, bytes=0))
        t['captures'] += 1; t['frames'] += r['frames']; t['bytes'] += r['bytes']
    return dict(by_dataset=tot, frames=sum(r['frames'] for r in rows), bytes=sum(r['bytes'] for r in rows),
                note='forecast = dense frame count x the capture\'s mean served anchor PNG size')


def source_of(c, frames_dirs):
    if c['dataset'] in frames_dirs:
        return 'frames_dir', Path(frames_dirs[c['dataset']].format(id=c['capture'].split('/', 1)[1]))
    if c['dataset'] in ('scannet', 'scannetpp'):
        return 'mp4', G.DENSE_SRC/c['dataset']/c['summary']['source'].lstrip('/')
    return None, None


def write_atomic(path, data):
    tmp = path.with_name(path.name+'.tmp')
    tmp.write_bytes(data); os.replace(tmp, path)


def one(job):
    """Decode one capture; returns its manifest entry (without raising for a sha mismatch or a missing source)."""
    c, out_root, frames_dirs = job
    import cv2, numpy as np
    cv2.setNumThreads(1)
    t0 = time.monotonic()
    kind, src = source_of(c, frames_dirs)
    d = Path(out_root)/c['dataset']/G.stub(c['capture']); d.mkdir(parents=True, exist_ok=True)
    entry = dict(capture=c['capture'], native=c['native'], dataset=c['dataset'], source_kind=kind, source=str(src) if src else None,
                 stride=c['stride'], dir=str(d.relative_to(out_root)), anchors=len(c['anchors']), frames=[], mismatches=[],
                 cv2=cv2.__version__)
    want = set(c['indices'])
    if src is None or not src.exists():
        entry.update(status='SOURCE_MISSING', seconds=time.monotonic()-t0); return entry
    entry['source_bytes'] = src.stat().st_size if src.is_file() else None
    entry['source_sha256'] = G.sha256_file(src) if src.is_file() else None
    got = {}
    if kind == 'mp4':
        cap = cv2.VideoCapture(str(src))
        entry['fps'] = cap.get(cv2.CAP_PROP_FPS); entry['meta_frames'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        j, last, dims = 0, max(want), None
        while cap.grab():
            if j in want:
                ok, img = cap.retrieve()
                if not ok:
                    break
                dims = (img.shape[1], img.shape[0])
                if dims != (640, 480):
                    img = cv2.resize(img, (640, 480), interpolation=cv2.INTER_AREA)
                ok, enc = cv2.imencode('.png', img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
                if not ok:
                    raise RuntimeError('imencode failed')
                got[j] = enc.tobytes()
            j += 1
        cap.release()
        entry.update(decoded_frames=j, src_wh=dims, raw_n=c['summary'].get('raw_n'), decoded_equals_raw_n=j == c['summary'].get('raw_n'))
    else:
        for i in sorted(want):
            p = src/('%06d.png' % i)
            if p.is_file():
                got[i] = p.read_bytes()
    missing = sorted(want-set(got))
    for pos, i in enumerate(c['indices']):
        if i not in got:
            continue
        data = got[i]; sha = G.sha256_bytes(data); a = c['anchors'].get(i)
        name = '%06d.png' % i; f = d/name
        if not (f.is_file() and f.stat().st_size == len(data) and G.sha256_file(f) == sha):
            write_atomic(f, data)
        rec = dict(native_index=i, position=pos, is_anchor=a is not None, slot=a['slot'] if a else None, sha256=sha, bytes=len(data),
                   file=name)
        entry['frames'].append(rec)
        if a is not None and sha != a['sha256']:
            mine = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            entry['mismatches'].append(dict(native_index=i, slot=a['slot'], sha256=sha, served_sha256=a['sha256'],
                                            max_abs=_max_abs(c, i, mine)))
    entry['missing_indices'] = missing
    entry['anchor_sha_equal'] = sum(1 for r in entry['frames'] if r['is_anchor'] and r['sha256'] == c['anchors'][r['native_index']]['sha256'])
    entry['dense_frames'] = len(entry['frames']); entry['bytes'] = sum(r['bytes'] for r in entry['frames'])
    if missing and any(i in c['anchors'] for i in missing):
        entry['status'] = 'SOURCE_MISSING'
    elif entry['mismatches'] or entry['anchor_sha_equal'] != len(c['anchors']):
        entry['status'] = 'SHA_MISMATCH'
    elif missing:
        entry['status'] = 'FRAMES_MISSING'
    else:
        entry['status'] = 'OK'
    entry['seconds'] = time.monotonic()-t0
    G.write_json(d/'MANIFEST.json', entry)
    return entry


SERVED = {}


def _max_abs(c, i, mine):
    """Max abs pixel difference of a mismatched anchor against its served PNG (path from FRAMES_GTC); None if unreadable."""
    import cv2, numpy as np
    if not SERVED:
        SERVED.update({(x['capture'], f['index']): f['path'] for x in G.read_frames_index()['captures'] for f in x['frames']})
    p = SERVED.get((c['capture'], i))
    s = cv2.imread(p, cv2.IMREAD_COLOR) if p else None
    if s is None or mine is None or s.shape != mine.shape:
        return None
    return int(np.abs(s.astype(int)-mine.astype(int)).max())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--datasets', default='scannet,scannetpp')
    ap.add_argument('--captures', default='')
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--out', default=str(G.DENSE_ROOT))
    ap.add_argument('--frames-dir', action='append', default=[], help='<dataset>=<dir template with {id}> (wa.py-rule PNGs)')
    ap.add_argument('--estimate', action='store_true')
    args = ap.parse_args(argv)
    datasets = [d for d in args.datasets.split(',') if d]
    if set(datasets)-set(G.STRIDE):
        raise SystemExit('--datasets takes scannet, scannetpp, arkit')
    if not 1 <= args.workers <= 8:
        raise SystemExit('--workers must be 1..8')
    frames_dirs = dict(x.split('=', 1) for x in args.frames_dir)
    if 'arkit' in datasets and 'arkit' not in frames_dirs:
        raise SystemExit('arkit needs --frames-dir arkit=<template>: the /data3 3dod PNGs do not reproduce the served anchors')
    if any('{id}' not in v for v in frames_dirs.values()):
        raise SystemExit('--frames-dir template needs {id}')
    out = Path(args.out).resolve()
    if not str(out).startswith('/scratch/'):
        raise SystemExit('dense frames go to /scratch only')
    frames = G.read_frames_index(); summary = json.loads(G.SUMMARY.read_text())
    caps = captures_for(frames, summary, datasets, [x for x in args.captures.split(',') if x])
    est = estimate(caps)
    free = shutil.disk_usage('/scratch').free
    print(json.dumps(dict(estimate=est, scratch_free_bytes=free)), flush=True)
    if args.estimate:
        return 0
    if est['bytes'] > MAX_BYTES or free-est['bytes'] < MIN_FREE:
        raise SystemExit('dense frames would exceed 60 GB or leave under 200 GB free on /scratch')
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    jobs = [(c, str(out), frames_dirs) for c in sorted(caps, key=lambda c: -c['summary'].get('raw_n', len(c['indices'])))]
    with Pool(min(args.workers, len(jobs))) as pool:
        entries = pool.map(one, jobs, chunksize=1)
    entries.sort(key=lambda e: e['capture'])
    for e in entries:
        print(json.dumps(dict(capture=e['capture'], status=e['status'], frames=e.get('dense_frames'), bytes=e.get('bytes'),
                              anchor_sha_equal=e.get('anchor_sha_equal'), mismatches=len(e['mismatches']),
                              seconds=round(e['seconds'], 1))), flush=True)
    by_ds = {}
    for e in entries:
        t = by_ds.setdefault(e['dataset'], dict(captures=0, ok=0, frames=0, bytes=0, anchors_checked=0, anchor_sha_equal=0))
        t['captures'] += 1; t['ok'] += e['status'] == 'OK'; t['frames'] += e.get('dense_frames', 0); t['bytes'] += e.get('bytes', 0)
        t['anchors_checked'] += sum(1 for r in e['frames'] if r['is_anchor']); t['anchor_sha_equal'] += e.get('anchor_sha_equal', 0)
    manifest = dict(schema=SCHEMA, created=G.utc(), host=os.uname().nodename, rule=RULE, strides={d: G.STRIDE[d] for d in datasets},
                    datasets=datasets, frames_dirs=frames_dirs, root=str(out),
                    inputs={str(p): G.sha256_file(p) for p in (G.FRAMES_PATH, G.SUMMARY, Path(__file__))},
                    totals=by_ds, not_ok=[dict(capture=e['capture'], status=e['status'], mismatches=e['mismatches'],
                                               missing_indices=e.get('missing_indices', [])) for e in entries if e['status'] != 'OK'],
                    seconds=time.monotonic()-t0, captures=entries)
    sha = G.write_json(out/'DENSE_D.json', manifest)
    print(json.dumps(dict(status='done', manifest=str(out/'DENSE_D.json'), sha256=sha, totals=by_ds,
                          not_ok=[x['capture'] for x in manifest['not_ok']])), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
