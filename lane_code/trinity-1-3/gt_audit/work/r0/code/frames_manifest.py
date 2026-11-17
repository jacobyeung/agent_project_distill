"""Collect per-scene frame manifests (out/frame_manifests/<scene>.json) into out/FRAMES_MANIFEST.json with sha256 per manifest."""
import hashlib, json, os, sys
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(L, 'out', 'R0_SCENES.json')))['captures']
DEF = json.load(open(os.path.join(L, 'out', 'DEFERRED.json')))['deferred']
scenes = sorted(os.listdir(os.path.join(L, 'data_cache', 'scannetpp')))
out, problems = {}, []
for s in scenes:
    p = os.path.join(L, 'out', 'frame_manifests', s + '.json')
    if not os.path.exists(p):
        problems.append((s, 'no manifest')); continue
    b = open(p, 'rb').read(); m = json.loads(b)
    if not m.get('count_match') or m.get('missing'):
        problems.append((s, 'count/missing'))
    n_png = len(os.listdir(os.path.join(L, 'frames', 'scannetpp', s)))
    if n_png != len(m['frames']):
        problems.append((s, 'png %d != manifest %d' % (n_png, len(m['frames']))))
    bad = [k for k, v in m['frames'].items()
           if hashlib.sha256(open(os.path.join(L, 'frames', 'scannetpp', s, '%06d.png' % int(k)), 'rb').read()).hexdigest() != v]
    if bad:
        problems.append((s, 'on-disk sha differs for %d frames' % len(bad)))
    out['scannetpp/' + s] = dict(r0_split=R['scannetpp/' + s]['r0_split'], manifest_sha256=hashlib.sha256(b).hexdigest(),
                                 frames=len(m['frames']), total_frames=m.get('total_pose'), deferred='scannetpp/' + s in DEF)
rec = dict(rule='32- and 64-frame layouts floor(linspace(0, total-1, n)), union decoded from iphone/rgb.mkv with PyAV 15.1.0, '
                'swscale bicubic to 640x480 PNG (code/decode_frames.py); frames/scannetpp/<scene>/<frame:06d>.png',
           scenes=out, n_scenes=len(out), n_frames=sum(v['frames'] for v in out.values()), problems=problems)
json.dump(rec, open(os.path.join(L, 'out', 'FRAMES_MANIFEST.json'), 'w'), indent=1, sort_keys=True)
print(json.dumps(dict(n_scenes=rec['n_scenes'], n_frames=rec['n_frames'], problems=problems)))
sys.exit(1 if problems else 0)
