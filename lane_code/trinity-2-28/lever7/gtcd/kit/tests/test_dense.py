"""dense.py tests (SAM 3 interpreter, cv2 4.10): the mp4 decode is deterministic against DENSE_D.json; the frames_dir source kind
(the ARKit hook: wa.py-rule PNGs named <index:06d>.png) copies bytes and passes the anchor check; an anchor whose PNG bytes differ
(same pixels, other compression) makes the capture SHA_MISMATCH with the slot listed; a missing source is SOURCE_MISSING; the CLI
refuses ARKit without --frames-dir, more than 8 workers and output off /scratch. Writes only under gtcd/work/test_dense."""
import json, shutil, sys
from pathlib import Path
import numpy as np, cv2
KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import gtc_common as G
import dense as D

W = G.ROOT/'work/test_dense'; W.mkdir(parents=True, exist_ok=True)
CAP = 'scannet/scene0380_01'
frames = G.read_frames_index(); summary = json.loads(G.SUMMARY.read_text())
c = D.captures_for(frames, summary, ['scannet'], [CAP])[0]
ref = next(x for x in G.read_json(G.DENSE_MANIFEST)['captures'] if x['capture'] == CAP)
key = lambda e: [(f['native_index'], f['is_anchor'], f['slot'], f['sha256']) for f in e['frames']]

e = D.one((c, str(W/'mp4'), {}))
assert e['status'] == 'OK' and e['anchor_sha_equal'] == 32 and key(e) == key(ref) and e['decoded_equals_raw_n']
print('PASS mp4 decode reproduces DENSE_D.json frame for frame (%d frames, 32/32 anchors)' % len(e['frames']), flush=True)

src = G.DENSE_MANIFEST.parent/ref['dir']; fd = W/'fd'/'scene0380_01'
if not fd.exists():
    shutil.copytree(src, fd, ignore=shutil.ignore_patterns('MANIFEST.json'))
e2 = D.one((c, str(W/'fdout'), {'scannet': str(W/'fd'/'{id}')}))
assert e2['status'] == 'OK' and e2['source_kind'] == 'frames_dir' and key(e2) == key(ref)
print('PASS frames_dir source copies bytes and passes the anchor check', flush=True)

bad = W/'fdbad'/'scene0380_01'
if not bad.exists():
    shutil.copytree(fd, bad)
a5 = next(f for f in ref['frames'] if f['slot'] == 5)
img = cv2.imread(str(fd/a5['file']), cv2.IMREAD_COLOR)
ok, enc = cv2.imencode('.png', img, [cv2.IMWRITE_PNG_COMPRESSION, 4]); (bad/a5['file']).write_bytes(enc.tobytes())
e3 = D.one((c, str(W/'fdbadout'), {'scannet': str(W/'fdbad'/'{id}')}))
assert e3['status'] == 'SHA_MISMATCH' and [m['slot'] for m in e3['mismatches']] == [5] and e3['mismatches'][0]['max_abs'] == 0
assert e3['anchor_sha_equal'] == 31
print('PASS an anchor with other PNG bytes (same pixels) makes the capture SHA_MISMATCH, slot listed', flush=True)

e4 = D.one((c, str(W/'none'), {'scannet': str(W/'absent'/'{id}')}))
assert e4['status'] == 'SOURCE_MISSING'
print('PASS a missing source is SOURCE_MISSING', flush=True)

for argv, word in ((['--datasets', 'arkit', '--estimate'], 'frames-dir'), (['--workers', '9', '--estimate'], 'workers'),
                   (['--out', '/tmp/x', '--captures', CAP], '/scratch')):
    try:
        D.main(argv); raise AssertionError('accepted '+' '.join(argv))
    except SystemExit as x:
        assert word in str(x), str(x)
print('PASS CLI refuses ARKit without --frames-dir, 9 workers, output off /scratch', flush=True)
print(json.dumps(dict(status='PASS')))
