"""Gate: every pinned k6 frame of the K1 manifest was rebuilt byte-identical; report new-frame pins.

usage: frame_parity.py MANIFEST_TEMPLATE STORE WA_OUT.jsonl WD_OUT.jsonl MISSING_DENSE_INDICES.json FRAME_SOURCES.jsonl OUT.json
"""
import hashlib, json, os, sys
man, store, wa_out, wd_out, missing, sources, out = sys.argv[1:8]
m = json.load(open(man)); tok = {}
for line in open(sources):
    r = json.loads(line); tok.setdefault(r['canonical'], r['s'])
built = {}
for p in (wa_out, wd_out):
    for line in open(p):
        r = json.loads(line)
        if 'error' in r: raise SystemExit('builder error: ' + json.dumps(r)[:300])
        if r.get('misses'): raise SystemExit('builder misses: ' + r['s'])
        for row in r['frames']: built[(r['s'], row[0])] = row[1]
need_new = {x['canonical']: x['new_indices'] for x in json.load(open(missing))}
bad, new, nbytes = [], {}, 0
only = os.environ.get('K1_ONLY', '')
for c in m['captures']:
    if not c['canonical'].startswith(only): continue
    s = tok[c['canonical']]
    for f in c['dense_frames']:
        if built.get((s, f['index'])) != f['sha256']: bad.append([c['canonical'], f['index']])
    for k in need_new.get(c['canonical'], []):
        h = built.get((s, k))
        if h is None: bad.append([c['canonical'], k, 'new missing']); continue
        new.setdefault(c['canonical'], []).append(dict(index=k, sha256=h))
for (s, k), h in built.items():
    p = os.path.join(store, h[:2], h + '.png'); nbytes += os.path.getsize(p)
    if hashlib.sha256(open(p, 'rb').read()).hexdigest() != h: bad.append([s, k, 'file hash'])
res = dict(pass_=not bad, pinned_checked=sum(len(c['dense_frames']) for c in m['captures'] if c['canonical'].startswith(only)), new_frames=sum(map(len, new.values())), store_bytes=nbytes, failures=bad[:50], n_failures=len(bad), new=new)
json.dump(res, open(out, 'w')); print(json.dumps({k: v for k, v in res.items() if k != 'new'})[:600])
sys.exit(0 if not bad else 1)
