"""Independent checks of the 6,000 camera training rows against the raw recovered source TEXT."""
import copy, gzip, hashlib, json, math, random, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

TREE = '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1'
OUT = Path('/scratch/jjyeung/orch_n30/sb_rowA/out')
SRC = Path('/scratch/jjyeung/orch_n30/sb_evidence/aws_sources/ap__8865619b__runs__469ddece__inputs__prepare_dd26bb95f37a43789206c6e4d4cd94bd__routing__rows.camera_rows.jsonl.gz')
ME = Path('/scratch/jjyeung/orch_n30/sb_arev2/scratch')
sys.path.insert(0, TREE)
from student_pilot import row_text_audit, r1_training, r2_contract, carrier_c1_routing as cr, s1_routing, extent_receipt, r0_exclusion  # noqa
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity  # noqa
CAM = ('camera_displacement', 'camera_rotation', 'camera_movement_direction')
c = Counter(); bad = defaultdict(list)


def flag(k, v):
    c['BAD:' + k] += 1
    if len(bad[k]) < 8: bad[k].append(v)


def sha(b): return hashlib.sha256(b).hexdigest()


rows = [json.loads(l) for l in open(OUT/'CAMERA_ROWS.jsonl')]
lin = [json.loads(l) for l in open(OUT/'CAMERA_LINEAGE.jsonl')]
assert len(rows) == len(lin) == 6000
need = {l['source_i'] for l in lin}
src = {}; src_qids = Counter(); src_types = Counter(); n = 0
with gzip.open(SRC, 'rt') as f:
    for line in f:
        x = json.loads(line); n += 1
        q = re.search(r'"qid": ?"([^"]+)"', x['row'])[1]; src_qids[q] += 1
        if x['i'] in need: src[x['i']] = x
c['extract_lines'] = n; c['extract_dup_qids'] = sum(v > 1 for v in src_qids.values())
W = json.loads((OUT/'WORDINGS.json').read_text())
PAT = dict(i=r'(?P<i>\d+)', j=r'(?P<j>\d+)', n=r'(?P<n>\d+)', unit=r'(?P<unit>[A-Za-z]+)', options=r'(?P<options>.+?)')


def tregex(t):
    parts = re.split(r'\{(i|j|n|unit|options)\}', t); s = ''; seen = set()
    for k, p in enumerate(parts):
        if k % 2 == 0: s += re.escape(p)
        else: s += f'(?P={p})' if p in seen else PAT[p]; seen.add(p)
    return re.compile('^' + s + '$', re.S)


TR = {t: [tregex(x) for x in W['training'][t]] for t in CAM}
HO = {t: [tregex(x) for x in W['heldout'][t]] for t in CAM}


def diff(a, b, p=''):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            q = p + '.' + k if p else k
            if k not in a: out.append(('missing_in_new', q))
            elif k not in b: out.append(('added', q))
            else: out += diff(a[k], b[k], q)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for k, (u, v) in enumerate(zip(a, b)): out += diff(u, v, f'{p}[{k}]')
    elif not (type(a) is type(b) and a == b): out.append(('changed', p))
    return out


def my_cid(r):
    si, rt = r['student_input'], r['routing']
    payload = [r['qid'], r['scene'], si['frame_indices'], rt['question_type'], si['question'], si['options'], [], rt['trace_revision'], 'phrases-v3']
    return 'ground-' + sha(json.dumps(payload, ensure_ascii=False).encode())


def quat(q):
    x, y, z, w = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([[w*w+x*x-y*y-z*z, 2*(x*y-w*z), 2*(x*z+w*y)], [2*(x*y+w*z), w*w-x*x+y*y-z*z, 2*(y*z-w*x)], [2*(x*z-w*y), 2*(y*z+w*x), w*w-x*x-y*y+z*z]])


def geom(s, i, j):
    """Camera centres/axes in frame-1 OpenCV coords; gravity-levelled pair quantities."""
    P = np.asarray(s['routing']['gt_pose9'], float); up = np.asarray(s['routing']['gt_up'], float); up /= np.linalg.norm(up); down = -up
    def cam(k):
        if k == 1: return np.zeros(3), np.eye(3)
        RE = quat(P[k-1, 3:7]); return -RE.T @ P[k-1, :3], RE.T
    (ci, Ai), (cj, Aj) = cam(i), cam(j)
    def lev(A):
        f = A[:, 2] - (A[:, 2] @ down) * down; f /= np.linalg.norm(f); return np.cross(down, f), f
    ri, fi = lev(Ai); rj, fj = lev(Aj); d = cj - ci
    dx, dy, dz = d @ ri, d @ up, d @ fi
    turn = math.degrees(math.atan2(-(fj @ ri), fj @ fi))
    return dict(dx=dx, dy=dy, dz=dz, dist=float(np.linalg.norm(d)), turn=turn)


def nat(fn, *a):
    try: fn(*a); return None
    except Exception as e: return type(e).__name__ + ':' + str(e)[:160]


def native(r):
    errs = {}
    for name, fn in (('text_audit', lambda: row_text_audit.check(r, 'routing')), ('row_check', lambda: r1_training.row_check(r, 'routing')),
                     ('frame_metadata', lambda: r2_contract.frame_metadata(r['student_input'])), ('legacy_replay', lambda: s1_routing.legacy_replay(r)),
                     ('extents', lambda: extent_receipt.Extents(None).check(r, 'routing')), ('reserve', lambda: r0_exclusion.reserve().check(r, 'routing'))):
        e = nat(fn)
        if e: errs[name] = e
    rt, si = r['routing'], r['student_input']
    raw = dict(copy.deepcopy(rt), schema='derivgen-row-v2', infrastructure_only=False, target=r['target'], question=si['question'], options=si['options'],
               provenance=dict(canonical=rt['canonical'], physical_group=rt['physical_group'], alias=r['dataset'] + '/' + r['scene'],
                               frame_indices=si['frame_indices'], source_row_sha256=rt['source_row_sha256']))
    e = nat(cr.check_row, raw)
    if e: errs['check_row'] = e
    try:
        rgb = dict(si, frames=[dict(p, source_index=k) for p, k in zip(si['frames'], si['frame_indices'])])
        p = cr.c1_row(raw, rgb)
        d = diff(r, {k: p[k] for k in r if k in p})
        if d: errs['c1_row_pack_diff'] = d[:5]
    except Exception as ex: errs['c1_row'] = str(ex)[:160]
    return errs


rng = random.Random(20261119); sample = set(rng.sample(range(6000), 200))
ALLOWED = {('changed', 'qid'), ('changed', 'routing.qid'), ('changed', 'student_input.question'), ('added', 'candidate_id'), ('added', 'routing.candidate_id')}
cells = Counter(); used = Counter(); qids = Counter(); cids = Counter(); gt = Counter(); quote = Counter(); diffpaths = Counter()
for k, (r, l) in enumerate(zip(rows, lin)):
    x = src[l['source_i']]; s = json.loads(x['row']); kind = r['routing']['question_type']
    if l['qid'] != r['qid'] or l['type'] != kind: flag('lineage_align', k)
    if sha(x['row'].encode()) != l['source_row_sha256']: flag('lineage_src_sha', k)
    if s['qid'] != l['source_qid']: flag('lineage_src_qid', k)
    if x['target'] != '{}': flag('src_target_col', x['target'][:50])
    used[l['source_i']] += 1; cells[(kind, l['wording_id'])] += 1; qids[r['qid']] += 1; cids[r['candidate_id']] += 1
    if r['qid'] != s['qid'] + '-sbca-' + l['wording_id']: flag('qid_form', r['qid'])
    if r['qid'] in src_qids: flag('qid_collides_extract', r['qid'])
    # field diff vs source
    d = diff(r, s)
    for q in d: diffpaths[q] += 1
    if set(d) - ALLOWED: flag('diff_outside_allowed', (k, sorted(set(d) - ALLOWED)[:4]))
    if r['candidate_id'] != r['routing']['candidate_id'] or r['candidate_id'] != my_cid(r): flag('cid_formula', k)
    if 'candidate_id' in s or 'candidate_id' in s['routing']: c['src_has_cid'] += 1
    # template and frame binding
    ev = r['routing']['events']; dec = [e for e in ev if e['kind'] == 'decision']; tc = [e for e in ev if e['kind'] == 'tool_call']
    b = dec[0]['binding']; i, j = b['i'], b['j']
    if len(dec) != 1 or len(tc) != 1 or tc[0]['arguments'] != {'from': i, 'to': j} or b['M'] != 32: flag('binding', k)
    m = TR[kind][int(l['wording_id'][1:])].match(r['student_input']['question'])
    if not m: flag('template_mismatch', (k, l['wording_id'], r['student_input']['question'])); continue
    if (int(m['i']), int(m['j']), int(m['n'])) != (i, j, 32): flag('question_frames', (k, m.groupdict(), i, j))
    if tuple(l['frame_pair']) != (i, j): flag('lineage_pair', k)
    if 'unit' in m.groupdict() and m['unit'] not in ('meters', 'metres'): flag('unit', m['unit'])
    if 'options' in m.groupdict():
        opts = s['student_input']['options']; want = '; '.join(opts)
        c['opt_form:' + ('exact_join' if m['options'] == want else 'other')] += 1
        if m['options'] != want and len(bad['opt_render']) < 3: bad['opt_render'].append((m['options'], opts))
    if any(rx.match(r['student_input']['question']) for rx in HO[kind]): flag('matches_heldout_template', k)
    sq = s['student_input']['question']
    if (s['student_input']['question'] in r['target']) or any(sq in e.get('text', '') for e in ev): quote['source_question_verbatim_in_trace'] += 1
    if r['student_input']['question'] in r['target']: quote['new_question_verbatim_in_trace'] += 1
    # ground truth, independent geometry, against source fields
    if k in sample or True:
        g = geom(s, i, j); ans = s['routing']['gt_answer']; tag = 'S200' if k in sample else 'ALL'
        resp = [e for e in s['routing']['events'] if e['kind'] == 'tool_response'][0]['text']
        if kind == 'camera_displacement':
            ok = abs(g['dist'] - float(ans)) <= 0.005 + 1e-6; ok_s = f"{round(g['dist'], 2):.2f}" == ans
        elif kind == 'camera_rotation':
            t = g['turn']; ok = abs(((t - float(ans) + 180) % 360) - 180) <= 0.5 + 1e-6; ok_s = str(int(round(t))) == ans
        else:
            sc = dict(left=-g['dx'], right=g['dx'], forward=g['dz'], backward=-g['dz'])
            opts = {o.split('. ', 1)[0]: sc[o.split('. ', 1)[1].lower()] for o in s['student_input']['options']}
            best = max(opts, key=opts.get); srt = sorted(opts.values()); ok = best == ans; ok_s = ok
            if not ok: flag('direction_gt', (k, best, ans, opts))
        nums = [float(v) for v in re.findall(r'[+-]?\d+\.\d+|[+-]?\d+', resp)]
        if kind == 'camera_rotation': rok = abs(nums[0] - g['turn']) <= 0.5 + 1e-6
        else: rok = all(abs(a - b) <= 0.005 + 1e-6 for a, b in zip(nums, (g['dx'], g['dy'], g['dz'], g['dist'])))
        gt[(tag, kind, 'answer_ok')] += ok; gt[(tag, kind, 'answer_string_exact')] += ok_s; gt[(tag, kind, 'response_ok')] += rok; gt[(tag, kind, 'n')] += 1
        if not ok: flag('gt_answer', (k, kind, ans, g))
        if r['routing']['gt_answer'] != ans or r['routing']['answer'] != ans or not r['target'].endswith('\n\n' + ans): flag('row_answer_vs_source', k)
        if resp not in r['target']: flag('response_not_in_target', k)
    # N's validators on the new row and on its source
    for who, rr in (('row', r), ('src', s)):
        e = native(rr)
        if e: flag('native_' + who, (k, e))
        else: c['native_pass_' + who] += 1

c['rows'] = len(rows); c['unique_qids'] = len(qids); c['unique_cids'] = len(cids); c['sources_used'] = len(used); c['max_source_use'] = max(used.values())
c['cells'] = len(cells); c['cell_min'] = min(cells.values()); c['cell_max'] = max(cells.values())
c['unique_source_qids'] = len({l['source_qid'] for l in lin})
res = dict(counts=dict(c), bad=dict(bad), gt={'|'.join(k): v for k, v in sorted(gt.items())}, quote=dict(quote),
           diff_paths={f'{a}:{b}': v for (a, b), v in diffpaths.most_common(20)},
           per_type_cells={t: sorted(v for (kk, w), v in cells.items() if kk == t) == [50]*40 for t in CAM},
           sample_indices_sha256=sha(json.dumps(sorted(sample)).encode()),
           inputs={str(p): sha(Path(p).read_bytes()) for p in (OUT/'CAMERA_ROWS.jsonl', OUT/'CAMERA_LINEAGE.jsonl', SRC, OUT/'WORDINGS.json')})
json.dump(res, open(ME/'rows_check.json', 'w'), indent=1, default=str)
print(json.dumps(res, indent=1, default=str)[:6000])
