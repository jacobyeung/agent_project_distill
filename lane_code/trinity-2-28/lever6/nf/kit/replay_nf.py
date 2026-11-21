"""NF: CPU replay of the banked step-544 dev-S1 served read (Orchard 170056, native arm) with
K5's second-order (A2) tower cameras in place of the first order's (A1).

The model's text is held fixed. Every camera tool call (move, turn) is re-served from the swapped
geometry with the reader's own server code; the final answer is re-extracted where the model
copied the printed value (displacement: printed distance; rotation: printed turn) or applied its
written option-scoring rule to the printed components (movement direction). Distance and room
calls need tower depth and SAM 3 masks, which K5 does not return, so those types are reported
as unmeasured with the share of their items on captures whose tower outputs changed.

Substitution per capture: (i) direct, when the banked cameras equal A1's bit for bit (cameras,
K and scale): A2's arrays replace them; otherwise (ii) relative: B'_k = B_k inv(A1_k) A2_k per
anchor frame (unscaled camera-to-world), scale_B' = scale_B * s_A2 / s_A1, K_B' = K_B * K_A2 / K_A1
on non-zero entries. A capture without both K5 records keeps its banked cameras.

No question text is written. CPU only.
"""
import os
for _k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ.setdefault(_k, '4')
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import time

import numpy as np

LANE = Path('/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook')
TREE = Path('/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449')
NATIVE = LANE/'work/n13/ret/native'
META = LANE/'work/meta/x/sj/orch_cd'
K5KIT = Path('/scratch/jjyeung/orch_n30/lever5/k5/kit')
DEFAULTS = dict(
    banked=NATIVE/'R1.json', geometry=NATIVE/'geometry',
    tasks=[META/'legs1_reads/work/vendor/r3/TASKS.jsonl', META/'legs1_routed/out2/CAMERA_TASKS.jsonl'],
    k5_config=K5KIT/'1.json', k5_reference=K5KIT/'REFERENCE_K5.json')
PINNED = {  # sha256 of every input the replay reads; main() refuses a mismatch
    'banked': '75669a6300aeeaf1ec98ef1dbd2b5276a7607422d92d9624af0d64a9c82154c0',
    'TASKS.jsonl': 'a2f3fdbdab06ab81942d44044d85090df8ec5b86908cf010cdbcb17e35637f5e',
    'CAMERA_TASKS.jsonl': 'f59090ffc8fd0f4d80a2b049e2624660c0f46dbc1d26016145f4747850a432ac',
    '1.json': '54aceb9f4a9803eda2b0ece4bf4ecaf8b2a1267f69a3d1f0209cc1ce1b830f60',
    'REFERENCE_K5.json': 'b570a994de0cb051f59c00e28b6d720d0a26c99c48d69c1d2aecbe164fbaf996',
    'geometry_npz': 'bc352a3f2c4115d5ac3958a24ed69ce927e8b199a1438ce0902c733d1f02dd3e',
}
CODE = [LANE/'e2e_reader/geometry.py', LANE/'e2e_reader/servers.py',
        TREE/'student_pilot/carrier_c1_routing.py', TREE/'student_pilot/carrier_c1_decode.py',
        TREE/'student_pilot/camera_targets.py', TREE/'student_pilot/geometry_profiles.py',
        TREE/'evalpath/run.py']
CAMERA = ('camera_displacement', 'camera_rotation', 'camera_movement_direction')
UNMEASURED = ('object_abs_distance', 'room_size_estimation')
TYPES = CAMERA+UNMEASURED
# Types a registered rule has read (sources: NEXT_LEG_DECISION_20261117.md 2.2 item 4a;
# TOWER_ARM_SCALE_DRIFT_20261119.md; READER_R1_20261117.md; ROUTED_READER_LEVER_PLAN_20261120.md).
RULE_READ = {
    'camera_displacement': 'H3 (tower-arm camera harm rule) read at R1 steps 200 and 400; R1 stopped at step 400 on it (-0.73 pts)',
    'camera_rotation': 'H3 read at R1 steps 200 and 400',
    'camera_movement_direction': 'H3 read at R1 steps 200 and 400',
    'object_abs_distance': 'protected outcome "termination on the claimed arm" (capped distance reads <= 5/150) read at each R1 boundary',
    'room_size_estimation': 'R1 room gate registered (baseline: reader_r1 job 172456); a read of it is not evidenced in the records',
}
LOWER_BOUND_PTS = 0.5
CHANGED_SHARE = 0.05
TOWER_SHA = ('p9', 'd', 'dc', 'pt', 'K', 'cm', 'cu', 's')
ARM_NAMES = ['A1', 'A2', 'D1', 'D2']
NOTE = 'replay holds the model text fixed, so the difference is a lower bound'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def install():
    sys.dont_write_bytecode = True
    for p in (str(TREE), str(LANE)):
        if p not in sys.path:
            sys.path.insert(0, p)
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'


# ---------------------------------------------------------------- banked read

def load_tasks(paths):
    tasks = {}
    for p in paths:
        for line in Path(p).read_text().splitlines():
            if line.strip():
                t = json.loads(line)
                tasks['devrows:'+t['id']] = t
    return tasks


def final_answer(text):
    tail = text.rsplit('</think>', 1)[-1]
    return tail.replace('<|im_end|>', '').strip()


def with_answer(text, answer):
    """The same text with only the final answer string replaced."""
    head, sep, tail = text.rpartition('</think>')
    old = final_answer(text)
    i = tail.rfind(old)
    if not sep or i < 0:
        raise ValueError('answer not located')
    return head+sep+tail[:i]+answer+tail[i+len(old):]


def load_banked(path, tasks):
    data = json.loads(Path(path).read_text())
    items = []
    for x in data['arms']['unflagged']:
        t = tasks[x['key']]
        dec = x.get('decode') or {}
        items.append(dict(key=x['key'], type=x['question_type'], room=t['room'], capture=t['scene'],
                          dataset=t['dataset'], clip=x['perception']['clip'], task=t,
                          calls=[dict(call=c['call'], response=c.get('response'), served=c.get('served', True))
                                 for c in dec.get('calls', [])],
                          text=dec.get('text', ''), finish=dec.get('finish', 'item_error'),
                          strict_no_answer=dec.get('strict_no_answer'), score=x['scores']['answer']))
    return items


# ---------------------------------------------------------------- scoring

def score(task, text, finish, strict_no_answer=None):
    """parity.score's answer label: official fuzzy EM / MRA with native_score's think-close rule."""
    from evalpath.run import score_item
    dec = dict(text=text, finish=finish, calls=[])
    no_answer = (strict_no_answer or not re.search(r'</think\s*>', text, re.I)
                 or score_item({**task, 'ground_truth': task['answer']}, dec)['parse_failed'])
    return 0.0 if no_answer else score_item({**task, 'ground_truth': task['answer']}, dec)['score']


# ---------------------------------------------------------------- re-extraction

DIR = re.compile(r'Scoring each option by the matching component: (.*?)\.\s*\n\s*\nThe largest is (\w+)\. '
                 r'That matches option ([A-Z])\.', re.S)
TERM = re.compile(r'(\w+) = ([+-]?)d([xyz]) = [+-]?\d+(?:\.\d+)? m')


def components(response):
    m = re.search(r'dx = ([+-]?\d+\.\d+) m, dy = ([+-]?\d+\.\d+) m, dz = ([+-]?\d+\.\d+) m, distance = (\d+\.\d+) m', response)
    if not m:
        return None
    return dict(dx=float(m.group(1)), dy=float(m.group(2)), dz=float(m.group(3)), distance=m.group(4))


def reextract(item, old, new):
    """New final answer under the model's own copy or written rule, or None (answer held)."""
    answer = final_answer(item['text'])
    qt = item['type']
    if qt == 'camera_displacement':
        a, b = components(old), components(new)
        if a and b and answer == a['distance']:
            return b['distance']
        return None
    if qt == 'camera_rotation':
        a, b = re.fullmatch(r'turn = ([+-]\d+) deg', old), re.fullmatch(r'turn = ([+-]\d+) deg', new)
        if a and b and re.fullmatch(r'[+-]?\d+', answer) and int(answer) == int(a.group(1)):
            v = int(b.group(1))
            return ('%+d' % v) if answer.startswith('+') else str(v)
        return None
    if qt == 'camera_movement_direction':
        m = DIR.search(item['text'])
        b = components(new)
        if not m or not b or m.group(3) != answer:
            return None
        terms = TERM.findall(m.group(1))
        if not terms:
            return None
        values = [(w, (-1 if sign == '-' else 1)*b['d'+axis]) for w, sign, axis in terms]
        best = max(v for _, v in values)
        word = next(w for w, v in values if v == best)  # first maximum in the model's written order
        letters = {}
        for o in item['task'].get('options', []):
            mm = re.fullmatch(r'([A-Z])\. (.+)', o.strip())
            if mm:
                letters[mm.group(2).strip()] = mm.group(1)
        return letters.get(word)
    return None


# ---------------------------------------------------------------- geometry

def rigid_inverse(C):
    R, t = C[..., :3, :3], C[..., :3, 3]
    out = np.zeros_like(C)
    out[..., :3, :3] = np.swapaxes(R, -1, -2)
    out[..., :3, 3] = -np.einsum('...ji,...j->...i', R, t)
    out[..., 3, 3] = 1
    return out


def swapped_arrays(z, a1, a2):
    """Return (mode, K, camera_to_world, scale) for one capture; z holds the banked arrays."""
    B, KB, sB = np.asarray(z['camera_to_world'], float), np.asarray(z['K'], float), float(z['scale'])
    if a1 is None or a2 is None:
        return 'kept', KB, B, sB
    A1, A2 = np.asarray(a1['cu'], float), np.asarray(a2['cu'], float)
    K1, K2 = np.asarray(a1['K'], float), np.asarray(a2['K'], float)
    if A1.shape != B.shape or A2.shape != B.shape or K1.shape != KB.shape or K2.shape != KB.shape:
        raise ValueError('K5 record shape differs from banked geometry')
    if np.array_equal(A1, B) and np.array_equal(K1, KB) and float(a1['s']) == sB:
        return 'direct', K2, A2, float(a2['s'])
    C = B.copy()
    for k in range(len(B)):
        if not np.array_equal(A1[k], A2[k]):
            C[k] = B[k] @ (rigid_inverse(A1[k]) @ A2[k])
    s = sB if float(a1['s']) == float(a2['s']) else sB*float(a2['s'])/float(a1['s'])
    K = KB.copy()
    if not np.array_equal(K1, K2):
        nz = K1 != 0
        K[nz] = KB[nz]*(K2[nz]/K1[nz])
    return 'relative', K, C, s


def geometry_of(z, K, C, s):
    from e2e_reader import geometry as G
    return G.from_arrays(K=K, canvas_to_source=z['canvas_to_source'], camera_to_world=C, scale=s,
                         depth_grid=z['depth_grid'], grid_uv=z['grid_uv'],
                         anchor_frame_indices=z['anchor_frame_indices'])


def serve(geometry, calls):
    from e2e_reader.servers import ReadServers
    servers = ReadServers(geometry)
    return [servers.head(c['call'])[0] for c in calls]


# ---------------------------------------------------------------- K5 records

def authenticated(directory):
    d = Path(directory)
    receipt_path = next(d.glob('5?.1.json'))
    g = int(receipt_path.name[1])
    raw = (d/('5%d.json' % g)).read_bytes()
    receipt = json.loads(receipt_path.read_text())
    if receipt['sha256'] != hashlib.sha256(raw).hexdigest() or receipt['bytes'] != len(raw) or receipt['group'] != g:
        raise ValueError('receipt does not authenticate result %d' % g)
    return json.loads(raw), dict(group=g, sha256=receipt['sha256'], bytes=len(raw), job=receipt.get('job'))


def k5_records(dirs, reference, arm_ids):
    """{capture: {arm: first ok record}} for the requested arms, as score_k5.split_records reads them."""
    ref = json.loads(Path(reference).read_text())['captures']
    n = len(ref)
    scene = {c['k']: c['capture'] for c in ref}
    arms, receipts = {}, []
    for d in dirs:
        result, rc = authenticated(d)
        receipts.append(rc)
        for a in result['arms']:
            if a['arm'] in arms:
                raise ValueError('arm returned twice')
            arms[a['arm']] = a
    out, status = {}, {}
    for arm in arm_ids:
        a = arms.get(arm)
        status[ARM_NAMES[arm]] = None if a is None else dict(status=a.get('status'), complete=a.get('complete'),
                                                             records=len(a.get('records', [])))
        if a is None:
            continue
        for r in a.get('records', []):
            if r.get('status') != 'ok' or (r['position'] == n and r['index'] == 0):
                continue
            out.setdefault(scene[r['k']], {}).setdefault(arm, r)
    return out, status, receipts


def tower_changed(rec, a1, a2):
    c = rec.get(a1), rec.get(a2)
    if None in c:
        return None
    return any(c[0]['sha'].get(n) != c[1]['sha'].get(n) for n in TOWER_SHA)


# ---------------------------------------------------------------- bootstrap and rule

class Bootstrap:
    """round7_common.Bootstrap: item-weighted, whole physical rooms, random.Random(seed)."""
    def __init__(self, rooms, seed=20261120, draws=10000):
        self.rooms = sorted(set(rooms))
        self.lookup = {r: i for i, r in enumerate(self.rooms)}
        self.n = draws
        rng = random.Random(seed)
        self.draws = np.zeros((draws, len(self.rooms)), dtype=np.int16)
        for row in self.draws:
            for _ in self.rooms:
                row[self.lookup[rng.choice(self.rooms)]] += 1

    def samples(self, rows, key):
        n = np.zeros(len(self.rooms))
        total = n.copy()
        for r in rows:
            i = self.lookup[r['room']]
            n[i] += 1
            total[i] += r[key]
        dn = self.draws@n
        return np.divide(self.draws@total, dn, out=np.full(self.n, np.nan), where=dn > 0)

    def contrast(self, rows, a, b):
        v = self.samples(rows, a)-self.samples(rows, b)
        valid = v[np.isfinite(v)]
        mean = float(np.mean([r[a] for r in rows])-np.mean([r[b] for r in rows])) if rows else None
        return dict(mean=mean, ci95=np.percentile(valid, [2.5, 97.5]).tolist() if len(valid) else None,
                    defined_draws=int(len(valid)), undefined_draws=int(self.n-len(valid)))


def verdict(rule_read, delta_pts, changed, items):
    """The fixed rule (ORCH ANSWER 1902Z): option A before the next rule read on the type when the
    lower bound is at least 0.5 points (in magnitude) or more than 5% of its items change value."""
    share = changed/items if items else 0.0
    trigger = (delta_pts is not None and abs(delta_pts) >= LOWER_BOUND_PTS) or share > CHANGED_SHARE
    if not rule_read:
        return 'no registered rule read; rule not applied' + (' (would trigger)' if trigger else '')
    return 'OPTION_A before the next rule read on this type' if trigger else 'no option A needed'


# ---------------------------------------------------------------- replay

def replay(items, geometry_dir, records, a1, a2, log=print):
    from e2e_reader import geometry as G
    cache, modes = {}, {}
    for it in items:
        if it['type'] not in CAMERA:
            continue
        cap = it['capture']
        if cap not in cache:
            z = dict(np.load(Path(geometry_dir)/(it['clip']+'.npz'), allow_pickle=False))
            rec = records.get(cap, {})
            mode, K, C, s = swapped_arrays(z, rec.get(a1), rec.get(a2))
            modes[cap] = mode
            cache[cap] = (G.from_npz(Path(geometry_dir)/(it['clip']+'.npz')), geometry_of(z, K, C, s))
        banked_geom, swapped_geom = cache[cap]
        old = [c['response'] for c in it['calls']]
        it['banked_served'] = serve(banked_geom, it['calls'])
        it['swapped_served'] = serve(swapped_geom, it['calls'])
        it['mode'] = modes[cap]
        it['rescored'] = score(it['task'], it['text'], it['finish'], it['strict_no_answer'])
        it['rederived'] = reextract(it, old[-1], old[-1]) if old else None
        it['changed'] = it['swapped_served'] != it['banked_served']
        new_text = it['text']
        it['new_answer'] = None
        if it['changed']:
            ans = reextract(it, it['banked_served'][-1], it['swapped_served'][-1])
            if ans is not None and ans != final_answer(it['text']):
                new_text = with_answer(it['text'], ans)
                it['new_answer'] = ans
        it['replay_score'] = score(it['task'], new_text, it['finish'], it['strict_no_answer'])
        it['strict_score'] = it['score'] if it['type'] == 'camera_movement_direction' else it['replay_score']
    return modes


def summarize(items, records, a1, a2, seed, draws):
    boot = Bootstrap([it['room'] for it in items], seed, draws)
    per_type = {}
    for qt in TYPES:
        rows = [it for it in items if it['type'] == qt]
        caps = sorted({it['capture'] for it in rows})
        entry = dict(items=len(rows), captures=len(caps), rooms=len({it['room'] for it in rows}),
                     rule_read=RULE_READ.get(qt))
        if qt in CAMERA:
            for r in rows:
                r['b100'], r['r100'], r['s100'] = 100*r['score'], 100*r['replay_score'], 100*r['strict_score']
            changed = sum(r['changed'] for r in rows)
            c = boot.contrast(rows, 'r100', 'b100')
            entry.update(banked_pct=float(np.mean([r['b100'] for r in rows])),
                         replay_pct=float(np.mean([r['r100'] for r in rows])),
                         difference_pts=c['mean'], ci95=c['ci95'], undefined_draws=c['undefined_draws'],
                         changed_items=changed, changed_share=changed/len(rows) if rows else 0.0,
                         answers_changed=sum(r['new_answer'] is not None for r in rows),
                         substitution={m: len({r['capture'] for r in rows if r['mode'] == m}) for m in ('direct', 'relative', 'kept')},
                         note=NOTE)
            if qt == 'camera_movement_direction':
                s = boot.contrast(rows, 's100', 'b100')
                entry['strict_answer_held'] = dict(difference_pts=s['mean'], ci95=s['ci95'])
            entry['verdict'] = verdict(bool(RULE_READ.get(qt)), entry['difference_pts'], changed, len(rows))
        else:
            ch = [tower_changed(records.get(cap, {}), a1, a2) for cap in caps]
            at_risk = sum(1 for it in rows if tower_changed(records.get(it['capture'], {}), a1, a2))
            entry.update(measured=False, reason='ground/gap/room calls need tower depth and SAM 3 masks; K5 returns depth hashes only',
                         captures_tower_changed=sum(1 for x in ch if x), captures_without_k5=sum(1 for x in ch if x is None),
                         items_on_changed_captures=at_risk, at_risk_share=at_risk/len(rows) if rows else 0.0,
                         verdict='UNMEASURED by option B' + (
                             '; at-risk share above 5%, so option B cannot clear it' if rows and at_risk/len(rows) > CHANGED_SHARE else ''))
        per_type[qt] = entry
    cam = [it for it in items if it['type'] in CAMERA]
    pooled = boot.contrast(cam, 'r100', 'b100') if cam else None
    return per_type, dict(rooms=len(boot.rooms), seed=seed, draws=draws, unit='physical room (task room key)',
                          weighting='item-weighted ratio of sums, as round7_common.Bootstrap'), pooled


def markdown(nf):
    L = ['# NF: banked step-544 dev-S1 read replayed with K5 A2 cameras', '',
         'Every line: ' + NOTE + '.', '',
         '## Reproduction of the banked read',
         '- Camera calls re-served from the banked geometry: %(served_equal)d/%(calls)d byte-equal' % nf['reproduction'],
         '- Camera items re-scored from recorded text: %(rescored_equal)d/%(items)d; answers re-derived by the copy/written rule: %(rederived_equal)d/%(items)d' % nf['reproduction'],
         '- ' + nf['reproduction']['note_834_842'], '',
         '## Substitution', '- ' + json.dumps(nf['substitution']), '',
         '## Per type (points; paired room bootstrap, %(draws)d draws, seed %(seed)d, %(rooms)d rooms)' % nf['bootstrap'],
         '| Type | Items | Banked % | Replay % | Replay - banked [95% CI] | Printed value changed | Rule read | Verdict |',
         '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for qt, e in nf['types'].items():
        if 'difference_pts' in e:
            ci = e['ci95'] or [float('nan')]*2
            L.append('| %s | %d | %.3f | %.3f | %+.3f [%+.3f, %+.3f] (lower bound) | %d (%.1f%%) | %s | %s |' % (
                qt, e['items'], e['banked_pct'], e['replay_pct'], e['difference_pts'], ci[0], ci[1],
                e['changed_items'], 100*e['changed_share'], 'yes' if e['rule_read'] else 'no', e['verdict']))
        else:
            L.append('| %s | %d | - | - | unmeasured | %d items on %d changed captures (%.1f%%, upper proxy) | %s | %s |' % (
                qt, e['items'], e['items_on_changed_captures'], e['captures_tower_changed'], 100*e['at_risk_share'],
                'yes' if e['rule_read'] else 'no', e['verdict']))
    d = nf['types'].get('camera_movement_direction', {})
    if 'strict_answer_held' in d:
        s = d['strict_answer_held']
        L += ['', '- Movement direction with every answer held (strict text-fixed): %+.3f pts.' % s['difference_pts']]
    L += ['', '## Rule-read types (sources)'] + ['- %s: %s' % (k, v) for k, v in RULE_READ.items()]
    L += ['', 'Thresholds: |difference| >= %.1f pts or changed share > %d%% triggers option A on a rule-read type.' % (LOWER_BOUND_PTS, 100*CHANGED_SHARE),
          'Runtime %.1f s.' % nf['runtime_seconds']]
    return '\n'.join(L)+'\n'


def run(args, log=print):
    t0 = time.time()
    install()
    inputs = {'banked': dict(path=str(args.banked), sha256=sha(args.banked))}
    if not args.no_pin and inputs['banked']['sha256'] != PINNED['banked']:
        raise ValueError('banked R1.json sha256 mismatch')
    for p in args.tasks:
        inputs[str(p)] = sha(p)
    for p in (args.k5_config, args.k5_reference):
        inputs[str(p)] = sha(p)
    geo = sorted(Path(args.geometry).glob('*.npz'))
    inputs['geometry_npz'] = dict(files=len(geo), sha256_of_sorted_list=hashlib.sha256(
        '\n'.join(p.name+' '+sha(p) for p in geo).encode()).hexdigest())
    inputs['code'] = {str(p): sha(p) for p in CODE}
    if not args.no_pin:
        for p in [*args.tasks, args.k5_config, args.k5_reference]:
            if inputs[str(p)] != PINNED[Path(p).name]:
                raise ValueError('input sha256 mismatch: '+str(p))
        if inputs['geometry_npz']['sha256_of_sorted_list'] != PINNED['geometry_npz']:
            raise ValueError('geometry export sha256 mismatch')
    tasks = load_tasks(args.tasks)
    items = load_banked(args.banked, tasks)
    clip_of = {}
    for it in items:
        clip_of.setdefault(it['capture'], it['clip'])
    ref_scene = {c['k']: c['capture'] for c in json.loads(Path(args.k5_reference).read_text())['captures']}
    bound = 0
    for row in json.loads(Path(args.k5_config).read_text())['x3']:
        cap = ref_scene[row['k']]
        if cap in clip_of:
            z = np.load(Path(args.geometry)/(clip_of[cap]+'.npz'))
            if list(map(int, z['anchor_frame_indices'])) != list(row['a']):
                raise ValueError('K5 anchors differ from the banked geometry on '+cap)
            bound += 1
    inputs['k5_captures_bound_by_anchor_indices'] = bound
    records, arm_status, receipts = k5_records(args.k5, args.k5_reference, [args.a1, args.a2])
    log('banked items %d, K5 captures with records %d' % (len(items), len(records)))
    modes = replay(items, args.geometry, records, args.a1, args.a2, log)
    cam = [it for it in items if it['type'] in CAMERA]
    calls = sum(len(it['calls']) for it in cam)
    served_equal = sum(a == c['response'] for it in cam for a, c in zip(it['banked_served'], it['calls']))
    reproduction = dict(
        items=len(cam), calls=calls, served_equal=served_equal,
        rescored_equal=sum(it['rescored'] == it['score'] for it in cam),
        rederived_equal=sum(it['rederived'] == final_answer(it['text']) for it in cam),
        note_834_842=('834/842 is the R8 reconstruction (cont_ops24_c/gbuild/analyze_round8.py) of the held-out camera reads '
                      '173258/173412/173234 from distance-read cameras, not of this read; read 170056 exports its served '
                      'geometry per capture, so its camera calls replay from the exported tensors directly '
                      '(b04 token replay: 927/927 calls, tests/replay_170056.py).'))
    types, boot, pooled = summarize(items, records, args.a1, args.a2, args.seed, args.draws)
    substitution = {m: sum(1 for v in modes.values() if v == m) for m in ('direct', 'relative', 'kept')}
    substitution['camera_captures'] = len(modes)
    cu_equal = 0
    for cap, rec in records.items():
        if args.a1 in rec:
            clip = next(it['clip'] for it in items if it['capture'] == cap)
            z = np.load(Path(args.geometry)/(clip+'.npz'))
            cu_equal += np.array_equal(np.asarray(rec[args.a1]['cu'], float), z['camera_to_world'])
    substitution['captures_banked_cameras_equal_A1_cu_bitwise'] = cu_equal
    nf = dict(schema='nf-replay-v1', arms=dict(swapped_from=ARM_NAMES[args.a1], swapped_to=ARM_NAMES[args.a2]),
              arm_status=arm_status, k5_receipts=receipts, inputs=inputs, reproduction=reproduction,
              substitution=substitution, bootstrap=boot, types=types, pooled_camera_descriptive=pooled,
              thresholds=dict(lower_bound_pts=LOWER_BOUND_PTS, changed_share=CHANGED_SHARE, comparison='|difference| >= 0.5 or share > 0.05'),
              note=NOTE,
              items=[dict(key=it['key'], type=it['type'], capture=it['capture'], room=it['room'], mode=it['mode'],
                          banked_response=it['banked_served'], swapped_response=it['swapped_served'],
                          banked_answer=final_answer(it['text']), new_answer=it['new_answer'],
                          banked_score=it['score'], replay_score=it['replay_score']) for it in cam])
    nf['runtime_seconds'] = time.time()-t0
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    (out/'NF.json').write_text(json.dumps(nf, indent=1, allow_nan=False)+'\n')
    (out/'NF.md').write_text(markdown(nf))
    return nf


def parser():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--k5', nargs='+', required=True, help='directories holding 5<g>.json and 5<g>.1.json (g0, g1)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--banked', type=Path, default=DEFAULTS['banked'])
    ap.add_argument('--geometry', type=Path, default=DEFAULTS['geometry'])
    ap.add_argument('--tasks', type=Path, nargs='+', default=DEFAULTS['tasks'])
    ap.add_argument('--k5-config', type=Path, default=DEFAULTS['k5_config'])
    ap.add_argument('--k5-reference', type=Path, default=DEFAULTS['k5_reference'])
    ap.add_argument('--a1', type=int, default=0, help='K5 arm whose cameras are replaced (0 = A1)')
    ap.add_argument('--a2', type=int, default=1, help='K5 arm whose cameras are substituted (1 = A2)')
    ap.add_argument('--seed', type=int, default=20261120)
    ap.add_argument('--draws', type=int, default=10000)
    ap.add_argument('--no-pin', action='store_true', help='tests only')
    return ap


def main():
    nf = run(parser().parse_args())
    print(json.dumps(dict(reproduction={k: v for k, v in nf['reproduction'].items() if k != 'note_834_842'},
                          substitution=nf['substitution'],
                          types={k: dict(difference_pts=v.get('difference_pts'), changed=v.get('changed_items'),
                                         verdict=v['verdict']) for k, v in nf['types'].items()},
                          runtime_seconds=nf['runtime_seconds']), indent=1))


if __name__ == '__main__':
    main()
