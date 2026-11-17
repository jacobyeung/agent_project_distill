"""Decode determinism on real data: re-decode N R0 scenes into work/redecode/ and compare PNG sha256 with their manifests.
usage: check_redecode.py [N]   -> out/REDECODE_CHECK.json"""
import json, os, sys, time
L = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(L, 'code'))
import decode_frames  # noqa: E402
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
mans = sorted(os.listdir(os.path.join(L, 'out', 'frame_manifests')))[:n]
res = {}
for m in mans:
    s = m[:-5]; ref = json.load(open(os.path.join(L, 'out', 'frame_manifests', m)))
    d = os.path.join(L, 'work', 'redecode', '%s_%d' % (s, int(time.time())))
    rec = decode_frames.main(os.path.join(L, 'data_cache', 'scannetpp', s), d, d + '.json')
    res[s] = dict(equal={str(k): v for k, v in rec['frames'].items()} == ref['frames'], n=len(ref['frames']))
json.dump(res, open(os.path.join(L, 'out', 'REDECODE_CHECK.json'), 'w'), indent=1)
print(res)
