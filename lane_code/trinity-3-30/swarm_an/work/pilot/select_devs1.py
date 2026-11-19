"""Labelling pilot, part 3: choose dev-S1 clips and items for the frontier-headroom read (40 items per direct type, fewest clips).
Writes work/pilot/devs1_clips.json = {alias: {room, anchors, items: [{id, type, question, options, gt, student_score, student_pred}]}}.
No R0-dev and no official item is read. usage: /usr/bin/python3 select_devs1.py [per_type=40] [cap per clip and type=3]"""
import sys, json, collections, random
sys.dont_write_bytecode = True
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
PER = int(sys.argv[1]) if len(sys.argv) > 1 else 40
CAP = int(sys.argv[2]) if len(sys.argv) > 2 else 3
rows = K.direct('R1', 200, 'dev-S1')
raw = [p for p in K.SOURCES if p.endswith('/main/a0/results/0/items_a0.jsonl')][0]
media = {}
with open(raw) as f:
    for l in f:
        r = json.loads(l); m = r.get('media') or {}
        media[r['id']] = (m.get('plan_alias'), m.get('anchor_indices'), r.get('dataset'))
types = sorted(set(r['type'] for r in rows))
byroom = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    if media.get(r['id'], (None,))[0]: byroom[media[r['id']][0]][r['type']].append(r)   # one clip = one plan alias (a room can have several captures)
random.seed(20261119)
for rm_ in byroom.values():
    for v in rm_.values(): random.shuffle(v)
need = dict((t, PER) for t in types); chosen = collections.OrderedDict()
rooms = sorted(byroom)
while any(v > 0 for v in need.values()) and len(chosen) < len(rooms):
    best, gain = None, 0
    for room in rooms:
        if room in chosen: continue
        g = sum(min(CAP, len(byroom[room][t]), need[t]) for t in types if need[t] > 0)
        if g > gain: best, gain = room, g
    if best is None: break
    pick = []
    for t in types:
        k = min(CAP, len(byroom[best][t]), max(0, need[t]))
        pick += byroom[best][t][:k]; need[t] -= k
    chosen[best] = pick
out = collections.OrderedDict(); n = collections.Counter(); ds = collections.Counter()
for room, pick in chosen.items():
    al, anchors, d = media[pick[0]['id']]
    assert all(media[r['id']][0] == al for r in pick), room
    ds[d] += 1
    out[al] = dict(room=pick[0]['room'], dataset=d, anchors=anchors, items=[dict(id=r['id'], type=r['type'], question=r['question'], options=r['options'], gt=r['gt'],
                   student_score=r['score'], student_pred=r['pred']) for r in pick])
    for r in pick: n[r['type']] += 1
json.dump(out, open('/scratch/jjyeung/orch_n30/swarm_an/work/pilot/devs1_clips.json', 'w'), indent=0)
print('clips', len(out), 'items', sum(n.values()), dict(n)); print('datasets of the clips', dict(ds), '| unmet', dict((t, v) for t, v in need.items() if v > 0))
print('clips in dev-S1', len(rooms), '| anchors per clip', collections.Counter(len(v['anchors']) for v in out.values()))
