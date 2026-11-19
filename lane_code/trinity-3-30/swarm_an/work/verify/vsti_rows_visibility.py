import sys, json, random, sqlite3, collections
base = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
idx = json.load(open(base + '/FAMILY_INDEX_RANGES.json'))['families']
db = sqlite3.connect('file:' + base + '/vqa/rows.sqlite?mode=ro', uri=True)
fams = [k for k in idx if 'vsti' in k or k.startswith('camera_obj_rel_dist') or k.startswith('obj_obj_relative_pos')]
print('index keys sample', fams[:8], 'n fam keys', len(idx))
out = {}
for t in ['camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3', 'obj_obj_relative_pos_lr', 'obj_obj_relative_pos_nf', 'obj_obj_relative_pos_ud']:
    keys = [i for a, b in idx[t] for i in range(a, b + 1)]
    ks = sorted(random.Random(77).sample(keys, 200))
    rows = [json.loads(s) for i, s in db.execute('select i,row from rows where i in (' + ','.join('?' * len(ks)) + ')', ks)]
    c = collections.Counter()
    for r in rows:
        p = r['provenance']; sh = p['frame_n_share']; fl = p.get('visibility_floor')
        v = list(sh.values())
        c['rows'] += 1
        c['all_zero'] += all(x == 0 for x in v)
        c['any_zero'] += any(x == 0 for x in v)
        c['all_ge_floor'] += all(x >= fl for x in v) if fl is not None else 0
        c['all_positive'] += all(x > 0 for x in v)
    out[t] = dict(c); print(t, len(keys), dict(c), 'floor', fl)
r = rows[0]; p = r['provenance']
print(json.dumps({k: p[k] for k in ('camera_frame', 'first_seen', 'frame_n_share', 'visibility_floor', 'geometry_values')})[:900])
print(r['target'][:700])
json.dump(out, open('/scratch/jjyeung/orch_n30/swarm_an/work/verify/VSTI_ROWS_VISIBILITY.json', 'w'), indent=1)
