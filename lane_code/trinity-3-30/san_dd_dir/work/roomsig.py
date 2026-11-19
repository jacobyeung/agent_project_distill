"""Video signatures (fps, total_num_frames) of store-v7 direction rows vs dev-S1 / R0-dev rooms (primary-key reads only)."""
import json, sqlite3, sys, ast, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dir/work'); import dirparse as P
K = P.K
S = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
F = json.load(open(S + '/FAMILY_INDEX_RANGES.json'))['families']
db = sqlite3.connect('file:' + S + '/vqa/rows.sqlite?mode=ro', uri=True)
sig = collections.Counter(); scenes = collections.defaultdict(set)
for t in P.T:
    ids = [i for lo, hi in F[t] for i in range(lo, hi + 1)]
    for k in range(0, len(ids), 200):
        for i, row in db.execute('select i,row from rows where i in (%s)' % ','.join(map(str, ids[k:k + 200]))):
            r = json.loads(row); si = r['student_input']; si = si if isinstance(si, dict) else ast.literal_eval(si)
            s = (float(si['fps']), int(float(si['total_num_frames']))); sig[s] += 1; scenes[s].add(r['scene'])
print('training direction videos: distinct (fps,total_frames) signatures', len(sig), 'distinct scenes', len(set().union(*scenes.values())))
def test(name, rows, T):
    rooms = {}
    for r in rows:
        t = T.get(r['id'])
        if t: rooms[r['room']] = (float(t['fps']), int(float(t['total_frames'])))
    hit = [k for k, s in rooms.items() if s in sig]
    print(name, 'rooms', len(rooms), 'signature found in training', len(hit))
    return rooms, set(hit)
D = K.direct('R1', 200, 'dev-S1', types=P.T); R = K.direct('R1', 200, 'R0-dev', types=P.T)
rd, hd = test('dev-S1', D, K.timing('R1', 200, 'dev-S1'))
rr, hr = test('R0-dev', R, K.timing('R1', 200, 'R0-dev'))
# chance: shift total_frames by +-1..3 and count matches
for name, rooms in (('dev-S1', rd), ('R0-dev', rr)):
    c = sum(((f, n + d) in sig) for (f, n) in rooms.values() for d in (-3, -2, -1, 1, 2, 3)) / 6.0
    print(name, 'chance proxy (matches at total_frames +-1..3, mean per shift)', round(c, 1))
acc = lambda g: '%d/%d' % (sum(r['score'] == 1 for r in g), len(g))
print('R0 toward items in rooms whose signature is in training:', acc([r for r in R if r['subtype'] == 'toward' and r['room'] in hr]), '| not:', acc([r for r in R if r['subtype'] == 'toward' and r['room'] not in hr]))
print('dev-S1 items in rooms whose signature is in training:', acc([r for r in D if r['room'] in hd]), '| not:', acc([r for r in D if r['room'] not in hd]))
