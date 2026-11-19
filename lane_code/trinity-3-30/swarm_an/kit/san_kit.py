"""san_kit: read-in-place loaders for the trace-analysis swarm (lane swarm_an, trinity-3-30). Read-only; nothing is copied.

Usage (python /usr/bin/python3 for direct/facing/vsti; /scratch/jjyeung/envs/planner_local_v1/bin/python for routed):
    import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
    rows = K.direct('R1', 200, 'dev-S1')          # list of dicts, one per item
    rows = K.direct('S1', 544, 'R0-dev', types=['object_counting'])
    pairs = K.paired(K.direct('S1',544,'dev-S1'), K.direct('R1',200,'dev-S1'))   # [(row544,row200)] on shared ids
    K.SOURCES                                        # every file each loader reads

Row fields (direct, facing, VSTI):
    id, set, run, step, type, question, options (list of 'A. ...' strings or []), gt (the truth the score uses: the item's
    `answer` field), gt_released (the item's `ground_truth` field; differs slightly from gt on some numeric dev-S1 items),
    pred / score      : the SCORED arm B2048 (thinking force-closed at 2,048 tokens, then the answer is generated)
    pred_on / score_on: the full 16k generation (ON16k); None when that file was not returned
    text              : the model's full generated text (chain of thought, '</think>', answer) from ON16k when present,
                        else the B2048 text.  For a force-closed item B2048's own text is only the answer, so text is ON16k.
    forced_close      : B2048 closed the think block at 2,048 tokens (a "runaway")
    think_tokens      : think tokens in B2048 (2048 when force-closed); out_tokens: tokens of the ON16k generation
    hit_cap           : ON16k ran into 16,384 tokens; finish: ON16k finish reason
    room, subtype, unit, level, pair_id, count_kind  (None when the set does not carry them)
Routed rows (K.routed): id, set, step, type, question, options, gt, text (with <tool_response> blocks), finish
    ('eos' | 'max_calls' | 'max_new_tokens' | 'length'), calls (list of dicts: call, family, served, response),
    ncalls, answer (the scorer's parsed answer), score (task accuracy: MRA for numeric types, accuracy for choice), scale.
    gt is the truth the accepted scorer uses; gt_released is the released label (distance and room items carry both and they differ slightly).
"""
import json, os, sys
C = '/scratch/jjyeung/orch_n30/cont_ops16/work/c15'
HB = C + '/h1read/kit/build'
EV = '/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged'
IDMAP = C + '/h1read/evidence/ID_MAP.json'
FAM = {'dev-S1': 'main', 'R0-dev': 'a7', 'away': 'away', 'forward': 'forward', 'vsti': 'r6'}
# (run, step) -> fetched/x root.  S1 = the sealed leg at step 544 (run 469ddece), R1 = continuation leg R1 (run 673bc60f),
# D0 = leg D0 (run 359fcc3c), H1-1 = leg H1-1 (run 17c4ffa4).
X = {
    ('R1', 200): HB + '/a8102c3207b/fetched/x',      # dev-S1 (main) + R0-dev (a7)
    ('R1', 100): HB + '/a5d2d909067/fetched/x',      # dev-S1 + R0-dev
    ('S1', 544): HB + '/adff67f7ae9/fetched/x',      # R0-dev only (ON16k text; scores in ITEMS.jsonl)
    ('D0', 200): HB + '/ae470417b41/fetched/x',      # R0-dev (2,169 items incl. distance and room)
    ('H1-1', 100): HB + '/a24ea1a1936/fetched/x',    # dev-S1, away, forward, R0-dev
    ('D0', 100): HB + '/af35386aa3e/fetched/x',      # dev-S1, away, forward, R0-dev
}
XFACE = {('R1', 200): C + '/h1face/kit/build/a2e46c0504e/fetched/x'}
XVSTI = {('R1', 200): C + '/h1vsti/kit/build/a35f73e87f0/fetched/x', ('S1', 544): C + '/h1vsti/kit/build/acb2faedd41/fetched/x'}
S1_544 = {  # step-544 files that exist only as the B2048 arm
    'dev-S1': EV + '/main/results/budget_2048/0/items_leg_m544_main.jsonl',
    'away': EV + '/away/results/budget_2048/0/items_leg_m544_away.jsonl',
    'forward': EV + '/forward/results/budget_2048/0/items_leg_m544_forward.jsonl',
}
SOURCES = []
KEEP = ('room', 'subtype', 'unit', 'level', 'pair_id', 'count_kind', 'stratum')

def _jl(p):
    with open(p) as f:
        for l in f:
            if l.strip():
                yield json.loads(l)

def _files(root, fam):
    on = '%s/%s/a0/results/0/items_a0.jsonl' % (root, fam)
    b = '%s/%s/a0/results/budget_2048/0/items_a0.jsonl' % (root, fam)
    it = '%s/%s/ITEMS.jsonl' % (root, fam)
    return (on if os.path.isfile(on) else None, b if os.path.isfile(b) else None, it if os.path.isfile(it) else None)

def _load(on, b, items, setname, run, step, types=None):
    rows = {}; order = []
    def base(r):
        d = dict(id=r['id'], set=setname, run=run, step=step, type=r['question_type'], question=r['question'],
                 options=r.get('options') or [], gt=r.get('answer', r.get('ground_truth')), gt_released=r.get('ground_truth'))
        for k in KEEP: d[k] = r.get(k)
        d.update(pred=None, score=None, pred_on=None, score_on=None, text=None, forced_close=None, think_tokens=None,
                 out_tokens=None, hit_cap=None, finish=None)
        return d
    if on:
        SOURCES.append(on)
        for r in _jl(on):
            if types and r['question_type'] not in types: continue
            d = base(r); d.update(pred_on=r.get('extracted_answer'), score_on=r.get('score'), text=r.get('raw_generation'),
                                  out_tokens=r.get('output_tokens'), hit_cap=r.get('hit_token_cap'), finish=r.get('finish_reason'))
            rows[r['id']] = d; order.append(r['id'])
    if b:
        SOURCES.append(b)
        for r in _jl(b):
            if types and r['question_type'] not in types: continue
            d = rows.get(r['id'])
            if d is None:
                d = base(r); rows[r['id']] = d; order.append(r['id'])
                d.update(text=r.get('raw_generation'), out_tokens=r.get('output_tokens'), finish=r.get('finish_reason'))
            d.update(pred=r.get('extracted_answer'), score=r.get('score'), forced_close=bool(r.get('forced_close')),
                     think_tokens=r.get('think_tokens'))
    elif items:  # scored arm only in ITEMS.jsonl (ids may be the r0_ form: map through ID_MAP)
        SOURCES.append(items)
        idm = json.load(open(IDMAP)) if os.path.isfile(IDMAP) else {}
        back = {v['id']: k for k, v in idm.items()}
        for r in _jl(items):
            i = r['id'] if r['id'] in rows else back.get(r['id'])
            if i in rows:
                rows[i].update(pred=r.get('prediction'), score=r.get('score'))
                for k in ('level', 'pair_id', 'count_kind'):
                    if rows[i].get(k) is None: rows[i][k] = r.get(k)
    return [rows[i] for i in order]

def direct(run, step, setname, types=None):
    """Direct (no tool served) read. setname: 'dev-S1' | 'R0-dev'. types: optional list of question types."""
    if (run, step) == ('S1', 544) and setname == 'dev-S1':
        return _load(None, S1_544['dev-S1'], None, setname, run, step, types)
    on, b, it = _files(X[(run, step)], FAM[setname])
    return _load(on, b, it, setname, run, step, types)

def facing(run, step, twin, types=None):
    """Facing twins. twin: 'away' | 'forward'. (R1,200), (S1,544), (H1-1,100), (D0,100)."""
    if (run, step) == ('S1', 544):
        return _load(None, S1_544[twin], None, twin, run, step, types)
    root = XFACE.get((run, step)) or X[(run, step)]
    on, b, it = _files(root, twin)
    return _load(on, b, it, twin, run, step, types)

def vsti(run, step, types=None):
    """VSTI relative dev set (900 items, six types). (R1,200) or (S1,544)."""
    on, b, it = _files(XVSTI[(run, step)], 'r6')
    return _load(on, b, it, 'vsti', run, step, types)

def paired(a, b):
    m = {r['id']: r for r in b}
    return [(r, m[r['id']]) for r in a if r['id'] in m]

def summary(rows):
    from collections import defaultdict
    t = defaultdict(lambda: [0, 0.0, 0])
    for r in rows:
        x = t[r['type']]; x[0] += 1; x[1] += (r['score'] or 0.0); x[2] += int(bool(r['forced_close']))
    return {k: dict(items=v[0], score_pct=round(100 * v[1] / v[0], 2), forced_close=v[2]) for k, v in sorted(t.items())}

def timing(run, step, setname):
    """id -> dict(fps, total_frames, source_frame_indices (32 ints), spacing_s (seconds between sampled frames),
    timestamps_s (list of 32 seconds)) for a direct set ('dev-S1', 'R0-dev'), a facing twin or 'vsti'; read from the ON16k file."""
    if setname == 'vsti': root = XVSTI[(run, step)]
    elif setname in ('away', 'forward'): root = XFACE.get((run, step)) or X[(run, step)]
    else: root = X[(run, step)]
    on, b, it = _files(root, FAM[setname]); out = {}
    for r in _jl(on or b):
        m = r.get('media') or {}
        idx = r.get('source_frame_indices') or m.get('source_frame_indices') or r.get('anchor_indices')
        fps = r.get('fps') or (m.get('metadata') or {}).get('fps')
        if not idx or not fps: continue
        ts = [i / float(fps) for i in idx]
        out[r['id']] = dict(fps=fps, total_frames=r.get('total_num_frames') or (m.get('metadata') or {}).get('total_num_frames'),
                            source_frame_indices=idx, spacing_s=(ts[-1] - ts[0]) / (len(ts) - 1), timestamps_s=ts)
    return out

# ---------------- routed (G3T arm) ----------------
_S = None
def _scorer():
    global _S
    if _S is None:
        O = '/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3s'
        sys.path.insert(0, O); av = sys.argv; sys.argv = ['x']
        import score_r5 as S
        sys.argv = av; _S = S
    return _S

def routed(step, types=None, part='A'):
    """Routed read, G3T arm. step 200 or 544. part 'A': the 636 dev-S1 routed items (camera_displacement, camera_rotation,
    camera_movement_direction, object_abs_distance, room_size_estimation(36)); at 544 camera and room(36) come from read 0
    (null_argmax) and distance from read 1 (candidates_argmax), as in the accepted scorer. part 'B': the 134 room items
    (step 200: out3/B5/ret; step 544: bases/b2). Needs numpy: run with /scratch/jjyeung/envs/planner_local_v1/bin/python."""
    S = _scorer(); sc = S.scorers; O = S.O
    if part == 'A':
        if step == 200:
            rows, items, _, src = S.load(O.parent / 'out3/A4/ret', O / 'A', 0, 200, 'candidates_argmax')
        else:
            ra, items, _, s0 = S.load(S.BASE / 'b1/work/ret', S.BASE / 'b1', 0, 544, 'null_argmax')
            rd, _, _, s1 = S.load(S.BASE / 'b1/work/ret', S.BASE / 'b1', 1, 544, 'candidates_argmax')
            rows = {**ra, **rd}; src = s0 + s1
    else:
        if step == 200:
            rows, items, _, src = S.load(O.parent / 'out3/B5/ret', O / 'B', 0, 200, 'candidates_argmax')
        else:
            rows, items, _, src = S.load(S.BASE / 'b2/work/ret', S.BASE / 'b2', 0, 544, 'null_argmax')
    SOURCES.extend(s['path'] for s in src)
    out = []
    for k in sorted(rows):
        it = items[k]; r = rows[k]; o = r['output']
        if types and it['question_type'] not in types: continue
        recs = sc.records(o)
        out.append(dict(id=k, set='dev-S1-routed' if part == 'A' else 'room134', step=step, type=it['question_type'],
                        question=it['question'], options=it.get('options') or [], gt=it.get('answer', it.get('ground_truth')),
                        gt_released=it.get('released_answer'), gt_item_field=it.get('ground_truth'), room=it.get('room_key'), text=o.get('text', ''), finish=o.get('finish'),
                        calls=[dict(call=c.get('call'), family=c.get('family'), served=c.get('served'), response=c.get('response')) for c in recs],
                        ncalls=len(recs), answer=sc.answer_text(o), score=float(sc.accuracy(o, it)['task_accuracy']),
                        scale=o.get('scale'), tokens=len(o.get('tokens') or [])))
    return out
