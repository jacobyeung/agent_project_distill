"""Pooled harm rule of leg R1: reference implementation v2 (H1 on eight direct types over dev-S1 and R0-dev, H2 on their mean).

One decision per boundary (steps 200, 400, 600, 800), an R1 export against step 544 (artifact 1d6eeb28), paired by item.
  set S = dev-S1, family `main`  : 1,050 items, 72 physical rooms, baseline A544.jsonl (sha256 8347cd84...)
  set R = R0-dev, family `a7`    : 1,781 items, 98 physical rooms, baseline ITEMS.jsonl of Orchard 171197 (a05c2318...)
Rooms: every item resolves to its physical room through ROOM_CROSSWALK.json (pinned by sha256); an item the crosswalk does
  not map, or a row whose room or scene label names another physical room, is refused.  Rooms are drawn in the crosswalk's
  registered order.
Provenance: every read of a set comes with a manifest (PROVENANCE_SCHEMA.md).  The tool refuses a read whose manifest is
  missing, inconsistent with its receipts, its read file or its rows, or different from the registered step-544 manifest of
  the set anywhere in `config`; only the `run` block (run, artifact, step and the read job that carries them) may differ.
  Both manifests of a read name one export.  A decision read is logged in the read ledger; a second read of the same
  boundary and arm whose read file or manifest differs is refused.
Per type t and set d: D[d,t] = mean over the set's items of (score of the export - score of step 544).
Statistic of a type both sets hold: P[t] = w[t] * D[S,t] + (1 - w[t]) * D[R,t], with w[t] = n[S,t] / (n[S,t] + n[R,t]).
Route planning exists on dev-S1 only: P = D[S,route].  Appearance order exists on R0-dev only: P = D[R,appearance].
Bootstrap: 10,000 joint draws, seed 20261118, random.Random; each draw takes 72 dev-S1 rooms with replacement, then
  98 R0-dev rooms with replacement (rng.choices on the index range), recomputes every D, every P and the unweighted mean of
  the eight P from the same draw.  A draw in which a set holds no item of some type is rejected and redrawn (the next two
  rng.choices calls); only accepted draws count toward the 10,000.
Intervals: percentile, linear interpolation (numpy.quantile default), two-sided.  STOP tests compare the unrounded bounds
  with zero; rounding is for display only.
  H1 fires when the interval of some type lies wholly below zero: level 1 - 0.05/8 at step 200, 1 - 0.05/32 later.
  H2 fires when the interval of the mean of the eight lies wholly below zero: level 0.95 at step 200, 0.9875 later.
Printed beside the rule and stopping nothing: each set's own difference with its 95% interval, a mark when one set's
  interval lies wholly below zero while the pooled test of that type is silent, and object size split into dev-S1 metric
  (72 items), dev-S1 imperial (78) and R0-dev (293, centimetres only), each with its 95% interval from the same draws.

usage: pooled_harm_rule_v2.py --step STEP --read ITEMS.jsonl [ITEMS.jsonl] --manifest-s1 M.json --manifest-r0 M.json
                              --output OUT.json (--ledger READ_LEDGER.jsonl | --calibration)
`--calibration` reads an export of another run at any step and decides nothing; it checks manifests but writes no ledger."""
import argparse, datetime, hashlib, json, math, os, random, re, sys, tarfile
import numpy as np

EVD = '/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/pooled_rule/'
C = '/scratch/jjyeung/orch_n30/cont_ops/work'
BASE = dict(
    S=dict(name='dev-S1', family='main', path=C + '/d0/readk/evidence/A544.jsonl',
           sha256='8347cd843f47fe637e770e47544ad49b03e60909e5312260a305319150edb8be',
           items_sha256='22ad2765e8e9a69b7395ff98ff578aaa2fb36d454f5ed4cf47f6b935166412a4', items=1050, rooms=72,
           manifest=EVD + 'BASE_MANIFEST_dev-S1_544.json',
           manifest_sha256='e08a1d3427cf2adc31c96544d08913ed5ca173f7a08129a57f2d8759592a584b'),
    R=dict(name='R0-dev', family='a7', path=C + '/h1read/kit/build/adff67f7ae9/fetched/x/ITEMS.jsonl',
           sha256='a05c2318e038d6e19c368c309d8cba2cd31047fc6fd7ef124a7b8ac943565233',
           items_sha256='630cd8691a2c36ce5c7f6d58e8d7fcbfff1c01521105b926f2f82c8d16e73e71', items=1781, rooms=98,
           manifest=EVD + 'BASE_MANIFEST_R0-dev_544.json',
           manifest_sha256='86c8f993b5b799fc29f183bb295db136f2a4cac43c4ce8dbe10deb6656f530a1'))
CROSSWALK, CROSSWALK_SHA256 = EVD + 'ROOM_CROSSWALK.json', '994902af7647a52f7c288c975226305d91ea4875fdcc312456e8db79c4140c3b'
SIZE_UNITS, SIZE_UNITS_SHA256 = EVD + 'SIZE_UNITS_DEV_S1.json', '2a0d756bdb65093e6e55e508ba12b022fd5805e5274d4b45fb6c629400b2867f'
R1_RUN, BASE_ARTIFACT = '673bc60f', '1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef'
SHARED = ('object_counting', 'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard',
          'object_rel_distance', 'object_size_estimation')
TYPES = SHARED + ('route_planning', 'obj_appearance_order')          # route: dev-S1 only; appearance: R0-dev only
N_ITEMS = dict(S=dict(zip(SHARED + ('route_planning',), (150,) * 7)),
               R=dict(zip(SHARED + ('obj_appearance_order',), (385, 192, 194, 192, 279, 293, 246))))
NON_RULE = ('object_abs_distance', 'room_size_estimation')           # the only types the `direct` filter removes
SEED, DRAWS = 20261118, 10000
LEVELS = {200: (1 - 0.05 / 8, 0.95), 400: (1 - 0.05 / 32, 0.9875), 600: (1 - 0.05 / 32, 0.9875), 800: (1 - 0.05 / 32, 0.9875)}
META = ('task_type', 'room', 'scene', 'scoring_basis', 'level', 'pair_id', 'count_kind')
SIZE = SHARED.index('object_size_estimation')


class Refused(Exception):
    pass


def refuse(msg):
    raise Refused(msg)


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def pinned_json(path, digest, what):
    if not os.path.exists(path) or sha(path) != digest:
        refuse('%s is missing or not the registered file (%s)' % (what, path))
    return json.load(open(path))


def load(path, family, types):
    rows = {}
    for line in open(path):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get('family') != family or r.get('task_type') not in types:
            continue
        if r['id'] in rows:
            refuse('duplicate item %s in family %s' % (r['id'], family))
        s = r.get('score')
        if r.get('budget') != 2048 or type(s) not in (int, float) or not math.isfinite(s) or not 0 <= s <= 1:
            refuse('invalid scored item %s' % r['id'])
        rows[r['id']] = r
    return rows


def field(d, dotted):
    for k in dotted.split('.'):
        if isinstance(d, list) and k.isdigit() and int(k) < len(d):
            d = d[int(k)]
        elif isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return KeyError
    return d


def decoded_member(arch, member, id_map):
    """The read file a kit writes from its fetched archive: the archive's ITEMS.jsonl with a7 / r0dev ids decoded
    through the identifier map, re-serialised with sorted keys (tools/item_ids.py decode_inventories)."""
    raw = tarfile.open(arch).extractfile(member).read().decode()
    rows = [json.loads(l) for l in raw.splitlines() if l.strip()]
    dec = []
    for r in rows:
        if r.get('family') in ('a7', 'r0dev'):
            src = id_map.get(r['id'])
            if src is None:
                if re.fullmatch(r'[0-9a-f]{24}', r['id']):
                    refuse('archive item %s is absent from the identifier map' % r['id'])
            else:
                x = dict(r, id=src['id'], source_qid=src['source_qid'], source_line=src['source_line'])
                if x.get('example_id') == r['id']:
                    x['example_id'] = src['id']
                r = x
        dec.append(r)
    return ''.join(json.dumps(r, sort_keys=True) + '\n' for r in dec).encode() if dec != rows else raw.encode()


def check_manifest(m, d, read_by_sha, base_m, id_map):
    """Internal consistency of one manifest; returns the read path it names."""
    b = BASE[d]
    if m.get('schema') != 'pooled-rule-read-manifest-v1' or m.get('set') != b['name'] or m.get('family') != b['family']:
        refuse('%s manifest has the wrong schema, set or family' % b['name'])
    for k in ('run', 'config', 'type_filter', 'read_file', 'receipts'):
        if k not in m:
            refuse('%s manifest lacks %s' % (b['name'], k))
    run = m['run']
    mm = re.search(r'/runs/([0-9a-f]+)/m(\d+)/artifact\.json$', str(run.get('artifact_path')))
    if not mm or mm.group(1) != run.get('run_id') or int(mm.group(2)) != run.get('step'):
        refuse('%s manifest: artifact path does not name its run and step' % b['name'])
    if m['config'] != base_m['config']:
        diff = sorted(k for k in set(m['config']) | set(base_m['config']) if m['config'].get(k) != base_m['config'].get(k))
        refuse('%s manifest differs from the registered step-544 manifest in %s' % (b['name'], diff))
    if m['type_filter'] not in ('none', 'direct'):
        refuse('%s manifest: unknown type filter %r' % (b['name'], m['type_filter']))
    path = read_by_sha.get(m['read_file'].get('sha256'))
    if path is None:
        refuse('%s manifest names a read file that is not among --read' % b['name'])
    arch = m['read_file'].get('archive')
    if arch:
        if not os.path.exists(arch['path']) or sha(arch['path']) != arch['sha256']:
            refuse('%s manifest: fetched archive missing or changed' % b['name'])
        if hashlib.sha256(decoded_member(arch['path'], arch['member'], id_map)).hexdigest() != m['read_file']['sha256']:
            refuse('%s manifest: the read file is not the decoded ITEMS.jsonl of the fetched archive' % b['name'])
    if not m['receipts']:
        refuse('%s manifest has no receipt' % b['name'])
    for rc in m['receipts']:
        if not os.path.exists(rc['path']) or sha(rc['path']) != rc['sha256']:
            refuse('%s manifest: receipt missing or changed: %s' % (b['name'], rc['path']))
        doc = json.load(open(rc['path']))
        for src, dst in rc['binds']:
            v, w = field(doc, src), field(m, dst)
            if v is KeyError or w is KeyError or v != w:
                refuse('%s manifest: %s of %s does not match %s' % (b['name'], src, os.path.basename(rc['path']), dst))
    return path


def check_rows_against_manifest(m, rows, all_rows_path, d):
    b = BASE[d]
    pop = {t: 0 for t in N_ITEMS[d]}
    for r in rows.values():
        pop[r['task_type']] += 1
    if pop != m['config']['rule_population']:
        refuse('%s read population differs from its manifest' % b['name'])
    steps = sorted({r['step'] for r in rows.values()})
    if steps != [m['run']['step']]:
        refuse('%s rows carry steps %s, manifest says %s' % (b['name'], steps, m['run']['step']))
    if m['type_filter'] == 'direct':
        for line in open(all_rows_path):
            if line.strip():
                r = json.loads(line)
                if r.get('family') == b['family'] and r.get('task_type') in NON_RULE:
                    refuse('%s manifest says type filter direct, the read holds %s' % (b['name'], r['task_type']))


def prepare(read_paths, manifests, step, calibration, crosswalk=CROSSWALK, size_units=SIZE_UNITS, base_paths=None):
    """Every check of the rule, then the room matrices of both sets."""
    xw = pinned_json(crosswalk, CROSSWALK_SHA256, 'room crosswalk')
    su = pinned_json(size_units, SIZE_UNITS_SHA256, 'size-unit list')['items']
    idp = xw['sources']['id_map']
    id_map = pinned_json(idp['path'], idp['sha256'], 'identifier map')
    read_by_sha = {sha(p): p for p in read_paths}
    if len(read_by_sha) != len(read_paths):
        refuse('the same read file is named twice')
    data, used = {}, set()
    for d in 'SR':
        b = BASE[d]
        bpath = (base_paths or {}).get(d, b['path'])
        if sha(bpath) != b['sha256']:
            refuse('%s baseline is not the registered step-544 read' % b['name'])
        base_m = pinned_json(b['manifest'], b['manifest_sha256'], '%s baseline manifest' % b['name'])
        if base_m['read_file']['sha256'] != b['sha256'] or base_m['run']['artifact_sha256'] != BASE_ARTIFACT or base_m['run']['step'] != 544:
            refuse('%s baseline manifest does not describe the registered baseline' % b['name'])
        check_manifest(base_m, d, {b['sha256']: bpath}, base_m, id_map)
        m = manifests.get(d)
        if m is None:
            refuse('%s read has no manifest' % b['name'])
        path = check_manifest(m, d, read_by_sha, base_m, id_map)
        used.add(path)
        types = tuple(N_ITEMS[d])
        base = load(bpath, b['family'], types)
        check_rows_against_manifest(base_m, base, bpath, d)
        ids = sorted(base)
        key = ''.join('%s\t%s\t%s\n' % (i, base[i]['room'], base[i]['task_type']) for i in ids)
        if hashlib.sha256(key.encode()).hexdigest() != b['items_sha256'] or len(ids) != b['items']:
            refuse('%s item set differs from the registered one' % b['name'])
        read = load(path, b['family'], types)
        check_rows_against_manifest(m, read, path, d)
        if set(read) != set(ids):
            refuse('%s: item keys differ (read only %d, baseline only %d)' % (b['name'], len(set(read) - set(ids)), len(set(ids) - set(read))))
        for i in ids:
            for f in META:
                if base[i].get(f) != read[i].get(f):
                    refuse('%s: paired metadata differs on %s (%s)' % (b['name'], i, f))
        if not calibration and read[ids[0]]['step'] != step:
            refuse('%s: read is of step %s, not %d' % (b['name'], read[ids[0]]['step'], step))
        cw = xw['sets'][b['name']]
        order = cw['room_order']
        if len(order) != b['rooms'] or len(set(order)) != len(order):
            refuse('%s crosswalk room order is not %d distinct rooms' % (b['name'], b['rooms']))
        ri = {r: k for k, r in enumerate(order)}
        Smat, Nmat = np.zeros((len(order), len(types))), np.zeros((len(order), len(types)))
        SZ, NZ = np.zeros((len(order), 2)), np.zeros((len(order), 2))
        for i in ids:
            room = cw['items'].get(i)
            if room is None or room not in ri:
                refuse('%s: item %s has no physical room in the crosswalk' % (b['name'], i))
            for row in (base[i], read[i]):
                if cw['label_to_room'].get(row['room']) != room or cw['scene_to_room'].get(row['scene']) != room:
                    refuse('%s: item %s carries a room or scene label of another physical room' % (b['name'], i))
            t = types.index(base[i]['task_type'])
            delta = float(read[i]['score']) - float(base[i]['score'])
            Smat[ri[room], t] += delta
            Nmat[ri[room], t] += 1
            if d == 'S' and t == SIZE:
                u = su.get(i)
                if u not in ('metric', 'imperial'):
                    refuse('dev-S1 size item %s has no registered unit' % i)
                SZ[ri[room], int(u == 'imperial')] += delta
                NZ[ri[room], int(u == 'imperial')] += 1
        if [int(x) for x in Nmat.sum(0)] != [N_ITEMS[d][t] for t in types]:
            refuse('%s per-type item counts differ' % b['name'])
        data[d] = dict(S=Smat, N=Nmat, SZ=SZ, NZ=NZ, K=len(order), types=types, steps=sorted({read[i]['step'] for i in ids}),
                       base_pct=[100 * sum(float(base[i]['score']) for i in ids if base[i]['task_type'] == t) / N_ITEMS[d][t] for t in types],
                       rooms_per_type=[int((Nmat[:, k] > 0).sum()) for k in range(len(types))])
    if used != set(read_paths):
        refuse('a --read file is named by no manifest')
    mS, mR = manifests['S']['run'], manifests['R']['run']
    if (mS['run_id'], mS['artifact_sha256'], mS['step']) != (mR['run_id'], mR['artifact_sha256'], mR['step']):
        refuse('the two manifests name different exports')
    if not calibration and (mS['run_id'] != R1_RUN or mS['step'] != step):
        refuse('decision read is not of run %s at step %d' % (R1_RUN, step))
    if mS['artifact_sha256'] == BASE_ARTIFACT:
        refuse('the read is of the baseline artifact itself')
    return data


W = np.array([N_ITEMS['S'][t] / (N_ITEMS['S'][t] + N_ITEMS['R'][t]) for t in SHARED])


def stat(dS, dR):                           # per-type differences of each set (7,) -> eight P
    return np.concatenate([W * dS[:6] + (1 - W) * dR[:6], dS[6:7], dR[6:7]])


def draws(data):
    """The rule's 10,000 accepted joint draws (seed 20261118, random.Random, rejection of draws missing a type)."""
    KS, KR = data['S']['K'], data['R']['K']
    rng = random.Random(SEED)
    P, DS, DR, ZS = np.zeros((DRAWS, 8)), np.zeros((DRAWS, 7)), np.zeros((DRAWS, 7)), np.full((DRAWS, 2), np.nan)
    redrawn = b = 0
    while b < DRAWS:
        cS = np.bincount(rng.choices(range(KS), k=KS), minlength=KS)
        cR = np.bincount(rng.choices(range(KR), k=KR), minlength=KR)
        nS, nR = cS @ data['S']['N'], cR @ data['R']['N']
        if (nS == 0).any() or (nR == 0).any():
            redrawn += 1
            continue
        DS[b], DR[b] = (cS @ data['S']['S']) / nS, (cR @ data['R']['S']) / nR
        P[b] = stat(DS[b], DR[b])
        nz = cS @ data['S']['NZ']
        ZS[b] = np.where(nz > 0, (cS @ data['S']['SZ']) / np.maximum(nz, 1), np.nan)
        b += 1
    return P, DS, DR, ZS, redrawn


def ci(x, level):
    lo, hi = np.nanquantile(x, [(1 - level) / 2, (1 + level) / 2])
    return [float(lo), float(hi)]


def r3(v):
    return [round(100 * x, 3) for x in v] if isinstance(v, list) else round(100 * v, 3)


def decide(data, step):
    """Statistics and verdict of one read (unrounded bounds decide)."""
    P, DS, DR, ZS, redrawn = draws(data)
    dS = data['S']['S'].sum(0) / data['S']['N'].sum(0)
    dR = data['R']['S'].sum(0) / data['R']['N'].sum(0)
    p = stat(dS, dR)
    L1, L2 = LEVELS[step]
    types = []
    for t, name in enumerate(TYPES):
        iv = ci(P[:, t], L1)
        row = dict(type=name, weight_dev_s1=round(float(W[t]), 6) if t < 6 else (1.0 if t == 6 else 0.0),
                   pooled_delta=float(p[t]), interval=iv, ci95=ci(P[:, t], 0.95), fires=iv[1] < 0)
        for k, nm, D, dd in (('S', 'dev_s1', DS, dS), ('R', 'r0_dev', DR, dR)):
            if name in data[k]['types']:
                i = data[k]['types'].index(name)
                row[nm] = dict(items=N_ITEMS[k][name], rooms=data[k]['rooms_per_type'][i], step544_pct=data[k]['base_pct'][i],
                               delta=float(dd[i]), ci95=ci(D[:, i], 0.95))
        types.append(row)
    miv = ci(P.mean(1), L2)
    mean = dict(delta=float(p.mean()), interval=miv, ci95=ci(P.mean(1), 0.95), fires=miv[1] < 0)
    SZ, NZ = data['S']['SZ'].sum(0), data['S']['NZ'].sum(0)
    size_split = [dict(part='dev-S1 metric', items=int(NZ[0]), delta=float(SZ[0] / NZ[0]), ci95=ci(ZS[:, 0], 0.95),
                       draws_without_items=int(np.isnan(ZS[:, 0]).sum())),
                  dict(part='dev-S1 imperial', items=int(NZ[1]), delta=float(SZ[1] / NZ[1]), ci95=ci(ZS[:, 1], 0.95),
                       draws_without_items=int(np.isnan(ZS[:, 1]).sum())),
                  dict(part='R0-dev (cm)', items=N_ITEMS['R']['object_size_estimation'], delta=float(dR[SIZE]), ci95=ci(DR[:, SIZE], 0.95),
                       draws_without_items=0)]
    marks = ['%s on %s: %+.2f [%+.2f, %+.2f]' % (r['type'], BASE[k]['name'], 100 * r[nm]['delta'], 100 * r[nm]['ci95'][0], 100 * r[nm]['ci95'][1])
             for r in types if not r['fires'] for nm, k in (('dev_s1', 'S'), ('r0_dev', 'R'))
             if nm in r and r[nm]['ci95'][1] < 0]
    h1 = [r['type'] for r in types if r['fires']]
    return dict(types=types, mean=mean, size_split=size_split, marks=marks, H1=h1, H2=mean['fires'], stop=bool(h1 or mean['fires']),
                levels=dict(H1=L1, H2=L2), redrawn=redrawn)


def ledger_check(path, entry):
    old = [json.loads(l) for l in open(path) if l.strip()] if os.path.exists(path) else []
    for e in old:
        if all(e[k] == entry[k] for k in ('step', 'arm', 'set')):
            if e['read_sha256'] != entry['read_sha256'] or e['manifest_sha256'] != entry['manifest_sha256']:
                refuse('boundary %d, arm %s, %s was read before from another read file or manifest; one read per boundary and arm'
                       % (entry['step'], entry['arm'], entry['set']))
            return False
    return True


def display(res):
    """JSON form: every pp value rounded to three decimals for display; `fires` already decided on the unrounded bounds."""
    def rt(r):
        x = dict(type=r['type'], weight_dev_s1=r['weight_dev_s1'], pooled_delta_pp=r3(r['pooled_delta']), interval_pp=r3(r['interval']),
                 interval_pp_unrounded=[100 * v for v in r['interval']], ci95_pp=r3(r['ci95']), fires=r['fires'])
        for nm in ('dev_s1', 'r0_dev'):
            if nm in r:
                s = r[nm]
                x[nm] = dict(items=s['items'], rooms=s['rooms'], step544_pct=round(s['step544_pct'], 2), delta_pp=r3(s['delta']),
                             ci95_pp_printed_only=r3(s['ci95']))
        return x
    m = res['mean']
    return dict(types=[rt(r) for r in res['types']],
                mean_of_eight=dict(delta_pp=r3(m['delta']), interval_pp=r3(m['interval']), interval_pp_unrounded=[100 * v for v in m['interval']],
                                   ci95_pp=r3(m['ci95']), fires=m['fires']),
                object_size_split_printed_only=[dict(part=z['part'], items=z['items'], delta_pp=r3(z['delta']), ci95_pp=r3(z['ci95']),
                                                     draws_without_items=z['draws_without_items']) for z in res['size_split']],
                set_confined_loss_marks_printed_only=res['marks'], H1_fires_on=res['H1'], H2_fires=res['H2'])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--step', type=int, choices=sorted(LEVELS), required=True)
    ap.add_argument('--read', nargs='+', required=True)
    ap.add_argument('--manifest-s1', required=True)
    ap.add_argument('--manifest-r0', required=True)
    ap.add_argument('--output', required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--ledger')
    g.add_argument('--calibration', action='store_true')
    a = ap.parse_args()
    try:
        man = {'S': json.load(open(a.manifest_s1)), 'R': json.load(open(a.manifest_r0))}
        data = prepare(a.read, man, a.step, a.calibration)
        entries = [dict(step=a.step, arm='direct', set=BASE[d]['name'], run_id=man[d]['run']['run_id'],
                        artifact_sha256=man[d]['run']['artifact_sha256'], read_sha256=man[d]['read_file']['sha256'],
                        manifest_sha256=sha(a.manifest_s1 if d == 'S' else a.manifest_r0)) for d in 'SR']
        new = [e for e in entries if ledger_check(a.ledger, e)] if a.ledger else []
    except Refused as e:
        sys.exit('REFUSED: %s' % e)
    res = decide(data, a.step)
    verdict = ('STOP' if res['stop'] else 'SILENT') if not a.calibration else \
              ('would STOP' if res['stop'] else 'would stay SILENT') + ' (calibration read, decides nothing)'
    out = dict(rule='R1 pooled harm rule v2', step=a.step, calibration=a.calibration,
               read_steps=dict(dev_s1=data['S']['steps'], r0_dev=data['R']['steps']), levels=res['levels'], seed=SEED, draws=DRAWS,
               redrawn=res['redrawn'], crosswalk_sha256=CROSSWALK_SHA256, size_units_sha256=SIZE_UNITS_SHA256,
               baselines={BASE[d]['name']: dict(path=BASE[d]['path'], sha256=BASE[d]['sha256'], manifest_sha256=BASE[d]['manifest_sha256']) for d in 'SR'},
               reads={q: sha(q) for q in a.read}, manifests={BASE[d]['name']: e['manifest_sha256'] for d, e in zip('SR', entries)},
               run=man['S']['run'], script_sha256=sha(os.path.abspath(sys.argv[0])), verdict=verdict, **display(res))
    json.dump(out, open(a.output, 'w'), indent=1)
    if new:
        with open(a.ledger, 'a') as f:
            for e in new:
                f.write(json.dumps(dict(e, utc=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), output=os.path.abspath(a.output)), sort_keys=True) + '\n')
    f2 = lambda v: '[%+7.2f, %+7.2f]' % (100 * v[0], 100 * v[1])
    print('%-28s %-26s %-26s %8s  %-20s %s' % ('type', 'dev-S1 delta [95%]', 'R0-dev delta [95%]', 'pooled', 'interval, H1 level', 'fires'))
    for r in res['types']:
        cell = lambda nm: '%+6.2f %s' % (100 * r[nm]['delta'], f2(r[nm]['ci95'])) if nm in r else '-'
        print('%-28s %-26s %-26s %+8.2f  %s   %s' % (r['type'], cell('dev_s1'), cell('r0_dev'), 100 * r['pooled_delta'], f2(r['interval']),
                                                   'FIRES' if r['fires'] else ''))
    m = res['mean']
    print('%-28s %-26s %-26s %+8.2f  %s   %s' % ('mean of eight (H2 level)', '', '', 100 * m['delta'], f2(m['interval']), 'FIRES' if m['fires'] else ''))
    print('object size split (printed, stops nothing):')
    for z in res['size_split']:
        print('  %-18s %4d items  %+6.2f %s' % (z['part'], z['items'], 100 * z['delta'], f2(z['ci95'])))
    for mk in res['marks']:
        print('mark (printed, stops nothing): loss on one set only,', mk)
    print('verdict:', verdict)


if __name__ == '__main__':
    main()
