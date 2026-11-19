"""Second export for the staged pack (lane sb_headacc2): R0-dev direct rows with qids; full camera and distance routed records."""
import sys, json, gzip, os
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
OUT = '/scratch/jjyeung/orch_n30/sb_headacc2/work/pack/'
def dump(name, rows):
    p = OUT + name
    with gzip.GzipFile(p, 'wb', mtime=0) as f:
        for r in rows:
            f.write((json.dumps(r, sort_keys=True, default=str) + '\n').encode())
    print(name, len(rows), os.path.getsize(p))
which = sys.argv[1]
if which == 'direct':
    idm = json.load(open(K.IDMAP))
    rows = K.direct('R1', 200, 'R0-dev')
    for r in rows:
        m = idm[r['id']]; r['qid'] = m['source_qid']; r['source_line'] = m['source_line']; r['scene'] = m['scene']; r['room_key'] = m['room']
    assert len({r['source_line'] for r in rows}) == len(rows)
    dump('DIRECT_R1_200_R0dev.jsonl.gz', rows)
else:
    S = K._scorer(); O = S.O
    def slim(o):
        return {k: v for k, v in o.items() if k not in ('tokens', 'entries', 'timings', 'perception_memo', 'audit', 'prompt_tokens', 'decode_budget')}
    for step in (544, 200):
        if step == 200:
            rows, items, _, src = S.load(O.parent / 'out3/A4/ret', O / 'A', 0, 200, 'candidates_argmax'); sets = [(rows, 'candidates_argmax', ('camera', 'distance'))]
        else:
            ra, items, _, s0 = S.load(S.BASE / 'b1/work/ret', S.BASE / 'b1', 0, 544, 'null_argmax')
            rd, _, _, s1 = S.load(S.BASE / 'b1/work/ret', S.BASE / 'b1', 1, 544, 'candidates_argmax'); sets = [(ra, 'null_argmax', ('camera',)), (rd, 'candidates_argmax', ('distance',))]
        cam, dist = [], []
        for rows, rule, want in sets:
            for k in sorted(rows):
                it = items[k]; o = rows[k]['output']; t = it['question_type']
                rec = dict(id=k, step=step, select_rule=rule, type=t, question=it['question'], answer=it.get('answer'), ground_truth=it.get('ground_truth'),
                           room_key=it.get('room_key'), scene=it.get('scene'), dataset=it.get('dataset'),
                           frame_indices=it.get('frame_indices'), source_frame_indices=it.get('source_frame_indices'),
                           frame_paths=it.get('frame_paths'), output=slim(o))
                if t.startswith('camera_') and 'camera' in want: cam.append(rec)
                elif t == 'object_abs_distance' and 'distance' in want: dist.append(rec)
        dump('ROUTED_FULL_%d_devS1_camera.jsonl.gz' % step, cam)
        dump('ROUTED_FULL_%d_devS1_distance.jsonl.gz' % step, dist)
    o = dist[0]['output']; print('distance output keys', sorted(o.keys())); print('heads keys', sorted((o.get('heads') or {}).keys()))
    print('camera heads keys', sorted((cam[0]['output'].get('heads') or {}).keys()), 'scale', cam[0]['output'].get('scale'), 'item frames', str(cam[0]['frame_paths'])[:200])
