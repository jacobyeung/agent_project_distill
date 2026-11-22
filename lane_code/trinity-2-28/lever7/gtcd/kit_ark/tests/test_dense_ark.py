"""kit_ark dense.py and track.py unit isolation (SAM 3 interpreter, cv2 4.10; no torch import, no GPU):
  1. an ARKit run (synthetic frames dir for arkitscenes/43828324: every anchor is its served PNG, read from FRAMES_GTC and
     sha-checked; every other dense frame repeats the previous anchor's bytes) writes <out>/DENSE_D_ARK.json, status OK, 32/32
     anchors, plus DENSE_D_ARK.json.sha256 that sha256sum accepts; the ScanNet dense/DENSE_D.json keeps its bytes and mtime, and
     no dense/arkit folder appears;
  2. dense.py refuses an ARKit run into the ScanNet dense/ folder (default --out, or --manifest-name DENSE_D.json there) and an
     ARKit run mixed with ScanNet datasets;
  3. track.py --forecast plans only the ARKit capture of that manifest; its pairing check refuses the ARKit manifest into
     out/track and the ScanNet manifest into out_ark/track, and accepts both units' own pairs.
Writes only under gtcd/work/test_dense_ark (the manifest there is reused by test_launch_dry_ark.sh)."""
import json, os, subprocess, sys, contextlib, io
from pathlib import Path
KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT))
import gtc_common as G
import dense as D
import track as T

W = G.ROOT/'work/test_dense_ark'; W.mkdir(parents=True, exist_ok=True)
CAP = 'arkitscenes/43828324'; CID = CAP.split('/', 1)[1]
sn_sha, sn_mtime = G.sha256_file(G.DENSE_MANIFEST), G.DENSE_MANIFEST.stat().st_mtime_ns
assert not (G.DENSE_ROOT/'arkit').exists()

frames = G.read_frames_index(); summary = json.loads(G.SUMMARY.read_text())
c = D.captures_for(frames, summary, ['arkit'], [CAP])[0]
served = {f['index']: f for f in next(x for x in frames['captures'] if x['capture'] == CAP)['frames']}
fd = W/'frames'/CID; fd.mkdir(parents=True, exist_ok=True)
last = None
for i in c['indices']:
    if i in served:
        last = Path(served[i]['path']).read_bytes()
        assert G.sha256_bytes(last) == served[i]['sha256']
    p = fd/('%06d.png' % i)
    if not p.is_file():
        p.write_bytes(last)

out = W/'dense_ark'
assert D.main(['--datasets', 'arkit', '--captures', CAP, '--workers', '1', '--out', str(out),
               '--frames-dir', 'arkit=%s/{id}' % (W/'frames')]) == 0
man = out/'DENSE_D_ARK.json'
m = G.read_json(man)
e = m['captures'][0]
assert m['datasets'] == ['arkit'] and e['status'] == 'OK' and e['anchor_sha_equal'] == 32 and e['dense_frames'] == len(c['indices'])
assert not (out/'DENSE_D.json').exists()
subprocess.run(['sha256sum', '--quiet', '-c', 'DENSE_D_ARK.json.sha256'], cwd=out, check=True)
assert G.sha256_file(G.DENSE_MANIFEST) == sn_sha and G.DENSE_MANIFEST.stat().st_mtime_ns == sn_mtime
assert not (G.DENSE_ROOT/'arkit').exists()
print('PASS ARKit run writes DENSE_D_ARK.json (OK, 32/32 anchors, %d frames) and its sha256 file; ScanNet DENSE_D.json untouched'
      % e['dense_frames'], flush=True)

fdir = ['--frames-dir', 'arkit=%s/{id}' % (W/'frames')]
for argv, word in ((['--datasets', 'arkit', '--captures', CAP]+fdir, 'own --out'),
                   (['--datasets', 'arkit', '--captures', CAP, '--out', str(G.DENSE_ROOT), '--manifest-name', 'DENSE_D.json']+fdir, 'own --out'),
                   (['--datasets', 'scannet,arkit', '--out', str(W/'mixed')]+fdir, 'runs alone')):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            D.main(argv)
        raise AssertionError('accepted '+' '.join(argv))
    except SystemExit as x:
        assert word in str(x), str(x)
assert G.sha256_file(G.DENSE_MANIFEST) == sn_sha and G.DENSE_MANIFEST.stat().st_mtime_ns == sn_mtime
assert not (G.DENSE_ROOT/'arkit').exists() and not (W/'mixed').exists()
print('PASS dense.py refuses ARKit into dense/ (default --out, or DENSE_D.json there) and ARKit mixed with ScanNet', flush=True)

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    assert T.main(['--forecast', '--dense', str(man)]) == 0
f = json.loads(buf.getvalue())
assert f['captures'] == 1 and f['dense_frames'] == len(c['indices'])
seeds = G.read_json(G.SEEDS_B); want = len([u for x in seeds['captures'] if x['capture'] == CAP for u in x['units'] if u['arm'] == 'b'])
assert f['seeds'] == want
for dense, outd, ok in ((man, G.OUT/'track', False), (G.DENSE_MANIFEST, G.OUT_ARK/'track', False),
                        (man, G.OUT_ARK/'track', True), (G.DENSE_MANIFEST, G.OUT/'track', True)):
    try:
        T.pairing_check(dense, outd); assert ok, 'pairing accepted: %s -> %s' % (dense, outd)
    except SystemExit:
        assert not ok, 'pairing refused: %s -> %s' % (dense, outd)
print('PASS track.py plans the ARKit manifest alone (1 capture, %d seeds) and refuses crossed manifest/output pairs' % want, flush=True)
print(json.dumps(dict(status='PASS')))
