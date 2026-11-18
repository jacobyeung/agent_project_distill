"""Find how the opaque d2/d3 scene tokens (v + 12 hex) derive from canonical captures, from the known alias pairs."""
import json, hashlib, itertools
a = json.load(open('/scratch/jjyeung/orch_n30/rows_a2/work/alias_map.json'))
a.update(json.load(open('/scratch/jjyeung/orch_n30/b12_cntapp/work/d3_token_map.json')))
pairs = [(k.split('/', 1)[1], v) for k, v in a.items() if k.split('/', 1)[1].startswith('v') and len(k.split('/', 1)[1]) == 13][:40]
print(len(pairs), pairs[:3])
found = set()
for tok, can in pairs:
    ds, nid = can.split('/', 1)
    cands = {can, nid, ds + ':' + nid, can + '\n', nid + '\n', 'scannetpp/' + nid, 'scannetpp_v2/' + nid, ds + '_' + nid,
             'd2/' + nid, 'd2/' + can, 'd3/' + nid, 'd3/' + can, can + '.mp4', nid + '.mp4', ds + '/' + nid + '.mp4'}
    for s in cands:
        for h in ('sha256', 'sha1', 'md5', 'blake2b', 'sha512'):
            d = hashlib.new(h, s.encode()).hexdigest()
            if d[:12] == tok[1:] or d[-12:] == tok[1:]:
                found.add((h, s.replace(nid, '<id>').replace(ds, '<ds>'), 'head' if d[:12] == tok[1:] else 'tail'))
print('found', found)
