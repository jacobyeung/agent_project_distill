"""Category-point pricing (ORCH NOTE 0433Z ask 1). Run with the planner python (routed loaders).
Mapping: VSI-Bench = mean of 8 tasks (direction = mean of 3 levels); ReVSI = mean of 7 categories, each the equal mean of its
subtype means (counting single/multiple; direction forward/backward x easy/hard; relative distance closest/farthest);
VSTI primary = mean of 5 subtasks (camera-object relative distance v1-v3, object relative position lr/nf/ud, camera displacement,
camera movement direction, camera-object absolute distance)."""
import sys, re, json, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
STEP = int(sys.argv[1]) if len(sys.argv) > 1 else 200; RUN = 'R1'
D = {('dev-S1', s): K.direct(r, s, 'dev-S1') for r, s in ((RUN, STEP), ('S1', 544))}
D.update({('R0-dev', s): K.direct(r, s, 'R0-dev') for r, s in ((RUN, STEP), ('S1', 544))})
V = {s: K.vsti(r, s) for r, s in ((RUN, STEP), ('S1', 544))}
RA = {}; RB = {}
for _s in (STEP, 544):
    try: RA[_s] = K.routed(_s, part='A'); RB[_s] = K.routed(_s, part='B')
    except Exception as e: RA[_s] = []; RB[_s] = []; print('no routed read at step', _s, repr(e)[:80])
def num(x):
    try: return float(str(x).strip())
    except Exception: return None
def unit(q):
    q = q.lower()
    if re.search(r'centimet|\bcm\b', q): return 'cm'
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b', q): return 'ft'
    if re.search(r'\binch', q): return 'in'
    return 'm'
def noturn(r):
    t = (r['text'] or '').split('</think>')[0].lstrip()
    return t.startswith('Step 1') and not re.search(r'half turn|flip forward', t)
def mode(r):
    t = r['type']
    if r['score'] is not None and r['score'] >= 1: return None
    if t == 'object_counting':
        if r['forced_close']: return 'runaway'
        p, g = num(r['pred']), num(r['gt'])
        if p is None or g is None: return 'no count'
        return 'overcount' if p > g else 'undercount'
    if t.startswith('object_rel_direction'):
        if r.get('subtype') == 'away': return 'away: turn omitted' if noturn(r) else 'away: forward relation wrong'
        return 'wrong relation facing the reference'
    if t == 'object_size_estimation':
        p, g = num(r['pred']), num(r['gt'])
        if p is None or g is None: return 'no size'
        return 'overestimate' if p > g else 'underestimate'
    return 'wrong'
# leaves: name -> list of rows (step STEP) ; old rows by id
def leaf(setname, typ, sub=None):
    return [r for r in D[(setname, STEP)] if r['type'] == typ and (sub is None or r.get('subtype') == sub)]
def vleaf(typ): return [r for r in V[STEP] if r['type'] == typ]
def rleaf(typ, u=None, part='A'):
    src = RA if part == 'A' else RB
    return [r for r in src[STEP] if r['type'] == typ and (u is None or unit(r['question']) == u)]
OLD = {}
for k, rs in D.items():
    if k[1] == 544: OLD.update({(k[0], r['id']): r for r in rs})
for r in V[544]: OLD[('vsti', r['id'])] = r
for r in RA[544]: OLD[('dev-S1-routed', r['id'])] = r
for r in RB[544]: OLD[('room134', r['id'])] = r
BENCH = {
 'VSI-Bench': (8, {
   'counting': [leaf('dev-S1', 'object_counting')],
   'relative direction': [leaf('dev-S1', 'object_rel_direction_' + l) for l in ('easy', 'medium', 'hard')],
   'relative distance': [leaf('dev-S1', 'object_rel_distance')],
   'object size': [leaf('dev-S1', 'object_size_estimation')],
   'route planning': [leaf('dev-S1', 'route_planning')],
   'appearance order (R0-dev items)': [leaf('R0-dev', 'obj_appearance_order')],
   'absolute distance (routed, metre items)': [rleaf('object_abs_distance', 'm')],
   'room size (routed read, 36 dev-S1 rooms)': [rleaf('room_size_estimation')]}),
 'ReVSI': (7, {
   'counting': [leaf('R0-dev', 'object_counting', 'single'), leaf('R0-dev', 'object_counting', 'multiple')],
   'direction': [leaf('R0-dev', 'object_rel_direction_easy', 'toward'), leaf('R0-dev', 'object_rel_direction_hard', 'toward'),
                 leaf('R0-dev', 'object_rel_direction_easy', 'away'), leaf('R0-dev', 'object_rel_direction_hard', 'away')],
   'relative distance': [leaf('R0-dev', 'object_rel_distance', 'closest'), leaf('R0-dev', 'object_rel_distance', 'farthest')],
   'object size': [leaf('R0-dev', 'object_size_estimation')],
   'route (proxy: dev-S1 items)': [leaf('dev-S1', 'route_planning')],
   'absolute distance (proxy: dev-S1 routed, metre items)': [rleaf('object_abs_distance', 'm')],
   'room (routed read, 134 rooms)': [rleaf('room_size_estimation', part='B')]}),
 'VSTI': (5, {
   'camera-object relative distance': [vleaf('camera_obj_rel_dist_v%d' % i) for i in (1, 2, 3)],
   'object relative position': [vleaf('obj_obj_relative_pos_' + s) for s in ('lr', 'nf', 'ud')],
   'camera displacement (routed)': [rleaf('camera_displacement')],
   'camera movement direction (routed)': [rleaf('camera_movement_direction')]}),
}
out = {}
def sc(rs): return 100.0 * sum((r['score'] or 0.0) for r in rs) / max(1, len(rs))
def old_sc(rs):
    o = [OLD.get((r['set'], r['id'])) for r in rs]; o = [x for x in o if x is not None and x.get('score') is not None]
    return (100.0 * sum(x['score'] for x in o) / len(o)) if o else None
print('%-9s | %-52s | %5s | %6s | %6s | %6s | %s' % ('bench', 'category (leaves)', 'items', '544', str(STEP), 'lost', 'lost in benchmark points'))
for b, (ncat, cats) in BENCH.items():
    out[b] = {}
    for c, leaves in cats.items():
        if not all(leaves): print('%-9s | %-52s | no items at this step' % (b, c)); continue
        n = sum(len(l) for l in leaves); w = 1.0 / len(leaves)
        s = sum(w * sc(l) for l in leaves); olds = [old_sc(l) for l in leaves]
        so = sum(w * x for x in olds) if all(x is not None for x in olds) else None
        modes = collections.defaultdict(lambda: [0, 0.0])
        for l in leaves:
            for r in l:
                m = mode(r) if 'forced_close' in r else (None if r['score'] >= 1 else 'wrong')
                if m is None: continue
                modes[m][0] += 1; modes[m][1] += w * 100.0 * (1 - (r['score'] or 0.0)) / len(l)
        out[b][c] = dict(items=n, leaves=[len(l) for l in leaves], score=round(s, 2), score_544=None if so is None else round(so, 2), lost=round(100 - s, 2),
                         lost_benchmark_points=round((100 - s) / ncat, 2),
                         modes={m: dict(wrong=v[0], category_points=round(v[1], 2), benchmark_points=round(v[1] / ncat, 2)) for m, v in sorted(modes.items(), key=lambda kv: -kv[1][1])})
        print('%-9s | %-52s | %5d | %6s | %6.2f | %6.2f | %5.2f' % (b, c + ' ' + str([len(l) for l in leaves]), n, '-' if so is None else '%.2f' % so, s, 100 - s, (100 - s) / ncat))
        for m, v in sorted(modes.items(), key=lambda kv: -kv[1][1]):
            if len(modes) > 1: print('%-9s |    %-49s | %5d | %6s | %6s | %6.2f | %5.2f' % ('', m, v[0], '', '', v[1], v[1] / ncat))
json.dump(out, open('/scratch/jjyeung/orch_n30/swarm_an/work/verify/CATEGORY_POINTS_m%d.json' % STEP, 'w'), indent=1)
