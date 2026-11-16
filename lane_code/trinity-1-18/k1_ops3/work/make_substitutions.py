"""Write SUBSTITUTIONS_k6_replica.jsonl from pinned PNGs that are present in the store and hash to their pins.
usage: make_substitutions.py MISMATCH.jsonl STORE OUT.jsonl [HELD.json]
MISMATCH rows: {canonical, s, index, pin, built}; HELD (optional): list of pins not to substitute."""
import collections, hashlib, json, os, sys
mis, store, out = sys.argv[1:4]
held = set(json.load(open(sys.argv[4]))) if len(sys.argv) > 4 else set()
rows = collections.defaultdict(list); n = skipped = 0
for line in open(mis):
    r = json.loads(line)
    if r['pin'] in held: skipped += 1; continue
    p = os.path.join(store, r['pin'][:2], r['pin'] + '.png')
    if hashlib.sha256(open(p, 'rb').read()).hexdigest() != r['pin']:
        raise SystemExit('store file does not hash to its pin: ' + p)
    rows[r['s']].append([r['index'], r['pin']]); n += 1
with open(out, 'x') as f:
    for s in sorted(rows):
        f.write(json.dumps({'s': s, 'frames': sorted(rows[s]), 'misses': [], 'substitution': 'k6_replica_pinned_png'}) + '\n')
print(json.dumps({'substituted': n, 'held': skipped, 'tokens': len(rows)}))
