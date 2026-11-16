"""Acceptance (ruling 19:09Z): every frame identity in the staged manifest equals its pin, and its store file hashes to it."""
import hashlib, json, sys
m = json.load(open(sys.argv[1])); base = json.load(open(sys.argv[2])); par = json.load(open(sys.argv[3]))
pins = {(c['canonical'], f['index']): f['sha256'] for c in base['captures'] for f in c['dense_frames']}
new = {(cn, x['index']): x['sha256'] for cn, xs in par['new'].items() for x in xs}
n = dict(pinned_ok=0, new_ok=0, bad=[], anchors_ok=0)
for c in m['captures']:
    for f in c['dense_frames']:
        k = (c['canonical'], f['index']); want = pins.get(k) or new.get(k)
        good = want is not None and f['sha256'] == want and f['path'] == '/scratch/jjyeung/k1_frames/%s/%s.png' % (want[:2], want) \
            and hashlib.sha256(open(f['path'], 'rb').read()).hexdigest() == want
        if not good: n['bad'].append(list(k)); continue
        n['pinned_ok' if k in pins else 'new_ok'] += 1
    si = c['model_row']['student_input']['frames']
    if [x['sha256'] for x in si] == [c['dense_frames'][i]['sha256'] for i in c['anchor_slots']]: n['anchors_ok'] += 1
n.update(captures=len(m['captures']), pinned_total=len(pins), new_total=len(new), unresolved=len(m['unresolved_dense_sources']),
         frames_per_capture=sorted({len(c['dense_frames']) for c in m['captures']}))
print(json.dumps(n)); sys.exit(1 if n['bad'] else 0)
