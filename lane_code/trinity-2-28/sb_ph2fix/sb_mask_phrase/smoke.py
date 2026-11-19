"""One-capture smoke test: setup time, capture time, P0 against the published A0 predictions."""
import json, sys, time
import kit as K

t = time.monotonic()
caps, ctx = K.setup()
print('setup', round(time.monotonic()-t, 1), 'captures', len(caps), flush=True)
name = sys.argv[1]
c = next(c for c in caps if c['canonical'] == name)
want = {r['id'] for r in c['rows'] if r['id'] in ctx[1]}
a0 = {}
with K.PER_ITEM.open() as f:
    for line in f:
        if '"A0_deployed"' in line[:40]:
            r = json.loads(line)
            if r['row_id'] in want:
                a0[r['row_id']] = r['prediction']
t = time.monotonic()
res = K.capture(c, ctx)
print('capture', round(time.monotonic()-t, 1), 'arms', res['arms_built'], 'builder', all(b['passed'] for b in res['builder_parity']), flush=True)
for n, d in res['names'].items():
    print(n, d['variants'], {k: (v['choice'], v['category'], v['on_target'], v['pool_recall']) for k, v in d['keys'].items()}, d['prompts'])
for it in res['items']:
    k0 = all(v == 'k0' for v in it['keys'].values())
    print(it['row_id'][:20], it['keys'], it['prediction'], 'A0', a0.get(it['row_id']), 'P0==A0' if k0 and it['prediction'] == a0.get(it['row_id']) else '')
