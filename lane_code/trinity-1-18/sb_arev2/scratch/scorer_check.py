"""Independent review of SCORER_PATCH: parity, held-out coverage, fail-closed and wrong-answer checks."""
import copy, hashlib, importlib.util, json, re, sys, traceback
from collections import Counter
from pathlib import Path

K = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src')
OUT = Path('/scratch/jjyeung/orch_n30/sb_rowA/out')
PATCHED = OUT/'SCORER_PATCH/h1eval/scorers.py'
sys.path.insert(0, str(K))
import h1eval  # noqa: E402  (inserts reader_core and tree)
from h1eval import scorers as S0  # noqa: E402

spec = importlib.util.spec_from_file_location('h1eval.scorers_patched', PATCHED)
S1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(S1)
CAM = ('camera_displacement', 'camera_rotation', 'camera_movement_direction')
rep = Counter(); notes = []


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def call(kind, i, j, style='plain'):
    name = 'turn' if kind == 'camera_rotation' else 'move'
    if style == 'quoted': return f'<{name} from="{i}" to="{j}">'
    if style == 'zero': return f'<{name} from=0{i} to={j}>'
    return f'<{name} from={i} to={j}>'


def response(kind, item, wrong=False):
    gt = item['ground_truth']
    if kind == 'camera_rotation':
        v = float(gt) + (90 if wrong else 0)
        return f'turn = {v:+.0f} deg'
    if kind == 'camera_displacement':
        d = float(gt) * (3 if wrong else 1)
        return f'dx = +0.00 m, dy = +0.00 m, dz = {d:+.2f} m, distance = {d:.2f} m'
    if kind == 'camera_movement_direction':
        opts = {o.split('. ', 1)[0]: o.split('. ', 1)[1].lower() for o in item['options']}
        lab = opts[gt]
        if wrong: lab = next(v for v in opts.values() if v != lab)
        vec = dict(left=(-1, 0), right=(1, 0), forward=(0, 1), backward=(0, -1))[lab]
        return f'dx = {vec[0]:+.2f} m, dy = +0.00 m, dz = {vec[1]:+.2f} m, distance = 1.00 m'
    return 'distance = 1.00 m'


def out(calls, text_answer, before=False, hook=False, responses=None):
    recs = [dict(call=c, response=(responses or [''] * len(calls))[k], at_token=10 + k, start_token=5 + k)
            for k, c in enumerate(calls)]
    body = '<think>\nreasoning ' + ' '.join(c + '<tool_response>' + r['response'] + '</tool_response>' for c, r in zip(calls, recs))
    text = ('<answer>X</answer>' if before else '') + body + '\n</think>\n\n<answer>' + str(text_answer) + '</answer>'
    o = dict(text=text, finish='eos')
    o['hook' if hook else 'calls'] = dict(records=recs) if hook else recs
    return o


def outputs(item):
    kind = item['question_type']; res = []
    if kind in CAM:
        i, j = item['display_frame_pair']
        for c in ([call(kind, i, j)], [call(kind, i, j, 'quoted')], [call(kind, i, j, 'zero')],
                  [call(kind, i, j + 1 if j < 32 else j - 1)], [call(kind, j, i)], [call(kind, i - 1 if i > 1 else i + 1, j)],
                  [call('camera_displacement' if kind == 'camera_rotation' else 'camera_rotation', i, j)],
                  [call(kind, i, j), call(kind, i, j)], [call(kind, i, j), call(kind, 1, 2)], [call(kind, 1, 2), call(kind, i, j)],
                  ['<ground obj="chair" mode="box">'], ['<gap a="x" b="y" rule="box_grid_5cm">'], []):
            res.append(out(c, item['ground_truth']))
        res.append(out([call(kind, i, j)], item['ground_truth'], before=True))
        res.append(out([call(kind, i, j)], item['ground_truth'], hook=True))
        res.append(dict(text='no calls', finish='max_calls', calls=[]))
    else:
        try: exp = S0.expected_calls(item['question'], kind)
        except ValueError: exp = []
        for c in (exp, exp[:1], exp[::-1], exp + exp[-1:], ['<move from=1 to=2>'], ['<turn from=3 to=9>'], [],
                  ['<ground obj="nothing" mode="box">'] + exp[1:]):
            res.append(out(c, item['ground_truth']))
        res.append(out(exp, item['ground_truth'], before=True))
        res.append(out(exp, item['ground_truth'], hook=True))
    return res


def safe(fn, *a):
    try: return ('ok', fn(*a))
    except Exception as e: return ('raise', type(e).__name__ + ':' + str(e))


# 1. Parity on the 636 devs1_routed originals.
devs = json.loads((K/'items/devs1_routed.json').read_text())['items']
assert len(devs) == 636
for item in devs:
    for o in outputs(item):
        a, b = safe(S0.placement, o, item), safe(S1.placement, o, item)
        rep['parity_cases'] += 1
        if a == b: rep['parity_equal'] += 1
        else:
            rep['parity_diff'] += 1
            if len(notes) < 10: notes.append(dict(id=item['id'], a=a, b=b))
        if a[0] == 'raise': rep['parity_orig_raise'] += 1
    if item['question_type'] in CAM:
        e0 = S0.expected_calls(item['question'], item['question_type'])
        i, j = item['display_frame_pair']
        rep['devs1_cam_pair_equals_parse'] += e0 == [call(item['question_type'], i, j)]
        rep['devs1_cam_pair_i_lt_j'] += int(1 <= i < j <= 32)
print('parity', dict(rep), notes[:3])

# 2. Held-out 900: independent frame binding from the question text by template match.
H = json.loads((OUT/'HELDOUT_CAMERA_ITEMS.json').read_text())
W = json.loads((OUT/'WORDINGS.json').read_text())
items = H['items']; assert len(items) == 900
orig_tpl = {
    'camera_displacement': 'Approximately how far (in meters) did the camera move between frame {i} and frame {j} of {n}?',
    'camera_rotation': 'What is the signed camera rotation in degrees between frame {i} and frame {j} of {n}? Positive means left; use (-180, 180].',
    'camera_movement_direction': "During the sequence between frame {i} and frame {j} of {n}, what was the primary consistent direction of the camera's movement relative to its orientation at the start? The options are {options}."}


PAT = dict(i=r'(?P<i>\d+)', j=r'(?P<j>\d+)', n=r'(?P<n>\d+)', unit=r'(?P<unit>[A-Za-z]+)', options=r'(?P<options>.+)')


def tregex(t):
    parts = re.split(r'\{(i|j|n|unit|options)\}', t); s = ''; seen = set()
    for k, p in enumerate(parts):
        if k % 2 == 0: s += re.escape(p)
        else:
            s += f'(?P={p})' if p in seen else PAT[p]; seen.add(p)
    return re.compile('^' + s + '$', re.S)


tpls = {t: [('orig', tregex(orig_tpl[t]))] + [(f'h{k:02d}', tregex(x)) for k, x in enumerate(W['heldout'][t])] for t in CAM}
train_tpls = {t: [tregex(x) for x in W['training'][t]] for t in CAM}
by_wording = Counter(); bad = []
for item in items:
    kind = item['question_type']; q = item['question']
    hits = [(name, m) for name, rx in tpls[kind] if (m := rx.match(q))]
    if len(hits) != 1: bad.append((item['id'], 'template_hits', len(hits))); continue
    name, m = hits[0]; by_wording[(kind, name)] += 1
    i, j, n = int(m['i']), int(m['j']), int(m['n'])
    nums = [int(x) for x in re.findall(r'(?<![\d.])\d+(?![\d.])', q)]
    if (i, j) != tuple(item['display_frame_pair']) or n != 32: bad.append((item['id'], 'pair_mismatch', (i, j, n), item['display_frame_pair']))
    if any(x not in (i, j, 32, 180) for x in nums): bad.append((item['id'], 'stray_number', nums))
    if kind == 'camera_displacement' and m.groupdict().get('unit', 'meters') not in ('meters', 'metres'): bad.append((item['id'], 'unit', m['unit']))
    if any(rx.match(q) for rx in train_tpls[kind]): bad.append((item['id'], 'matches_training_template'))
rep['heldout_template_bound'] = sum(by_wording.values()); rep['heldout_bad'] = len(bad)
print('heldout binding', len(bad), bad[:5]); print(sorted(by_wording.items()))

# 3. Score all 900 with correct and wrong outputs, original vs patched scorer, via measure-equivalent.
try:
    from h1eval import runner as R
    rep['runner_import'] = 'ok'
except Exception as e:
    R = None; rep['runner_import'] = 'fail:' + type(e).__name__ + ':' + str(e)[:120]


def measure(S, o, item, base=None):
    r = dict(M1=S.placement(o, item), M2=S.accuracy(o, item))
    if base is not None: r['M3'] = S.usage(base, o, item)
    if 'benchmark_item' in item or 'ground_truth' in item: r['M4'] = S.benchmark(o, item)
    return r


if R is not None:
    # Real runner.measure with the patched module swapped in, to confirm the merge path uses only placement.
    real_patched = lambda o, it, b=None: (setattr(R, 'scorers', S1), R.measure(o, it, b))[1]
fails = Counter(); wrong_right = Counter(); pertype = Counter()
for item in items:
    kind = item['question_type']; i, j = item['display_frame_pair']; reworded = '-sbca-h' in item['id']
    good = out([call(kind, i, j)], item['ground_truth'], responses=[response(kind, item)])
    perturbed = out([call(kind, i, j)], item['ground_truth'], responses=[response(kind, item, True)])
    r0 = safe(measure, S0, good, item)
    fails[('orig', reworded, r0[0])] += 1
    r1 = safe(real_patched if R is not None else (lambda o, it: measure(S1, o, it)), good, item)
    fails[('patched', reworded, r1[0])] += 1
    if r1[0] != 'ok': continue
    m = r1[1]; pertype[(kind, 'exact')] += bool(m['M1']['exact']); pertype[(kind, 'M4=1')] += m['M4']['score'] == 1.0
    pertype[(kind, 'M2acc=1')] += m['M2']['task_accuracy'] == 1.0
    if kind == 'camera_displacement':
        pertype[(kind, 'unit_factor=1')] += S1.unit_factor(item['question']) == 1.0
        c = m['M2']['calls'][0]; pertype[(kind, 'M2_abs_err<=0.006')] += c.get('absolute_error_m', 9) <= 0.006
    if kind == 'camera_rotation': pertype[(kind, 'M2_err0')] += m['M2']['calls'][0].get('error_deg') == 0
    if kind == 'camera_movement_direction': pertype[(kind, 'M2_option_correct')] += bool(m['M2']['calls'][0].get('correct'))
    m3 = safe(measure, S1, perturbed, item, good)
    pertype[(kind, 'M3_ok')] += m3[0] == 'ok' and m3[1]['M3'].get('eligible') is True
    # wrong outputs must never score as right
    for c in ([call(kind, i, j + 1 if j < 32 else j - 1)], [call(kind, j, i)], [call(kind, i + 1, j) if i + 1 < j else call(kind, i - 1, j)],
              [call('camera_displacement' if kind == 'camera_rotation' else 'camera_rotation', i, j)], [], [call(kind, i, j), call(kind, i, j)]):
        mm = S1.placement(out(c, item['ground_truth']), item)
        wrong_right['wrong_call_cases'] += 1; wrong_right['wrong_call_exact'] += bool(mm['exact'])
        wrong_right['wrong_call_args_full'] += (mm['argument_agreement'] == 1.0 and len(c) == 1)
    if kind == 'camera_movement_direction':
        wrong = next(o.split('. ')[0] for o in item['options'] if o.split('. ')[0] != item['ground_truth'])
        answers = [wrong, '(' + wrong + ')', wrong + '.', 'E', '']
    else:
        g = float(item['ground_truth']); s = 1 if g >= 0 else -1
        answers = [f'{g*3+7*s:.2f}', f'{g*0.4:.2f}' if abs(g) >= 5 else f'{g+20*s:.0f}', f'{-g-40*s:.0f}', 'unknown', '']
    for a in answers:
        mm = measure(S1, out([call(kind, i, j)], a, responses=[response(kind, item)]), item)
        wrong_right['wrong_answer_cases'] += 1; wrong_right['wrong_answer_M4_full'] += mm['M4']['score'] == 1.0
        wrong_right['wrong_answer_M4_pos'] += mm['M4']['score'] > 0
        if mm['M4']['score'] > 0 and len(notes) < 20: notes.append(dict(id=item['id'], ans=a, gt=item['ground_truth'], s=mm['M4']['score']))
    # wrong printed response must not count as a correct head value
    mm = measure(S1, out([call(kind, i, j)], item['ground_truth'], responses=[response(kind, item, True)]), item)
    cc = mm['M2']['calls'][0]
    wrong_right['wrong_response_cases'] += 1
    wrong_right['wrong_response_scored_right'] += (cc.get('correct') is True or cc.get('error_deg') == 0 or (cc.get('absolute_error_m', 9) <= 0.006))
print('fails', sorted(fails.items(), key=str)); print('pertype', sorted(pertype.items())); print('wrong', dict(wrong_right))
print('notes', notes[-5:]); print('runner', rep['runner_import'])

# 4. Fail-closed on bad display_frame_pair.
base = next(it for it in items if it['question_type'] == 'camera_rotation')
forms = [None, 'MISSING', [5], [5, 9, 11], ['5', '9'], [5.0, 9.0], [True, 9], [9, 5], [5, 5], [0, 9], [5, 33], (5, 9), '5,9', {'i': 5}]
closed = {}
for f in forms:
    it = copy.deepcopy(base)
    if f == 'MISSING': it.pop('display_frame_pair')
    else: it['display_frame_pair'] = f
    r = safe(S1.placement, out([call('camera_rotation', 5, 9)], '1'), it)
    closed[repr(f)] = r[0] if r[0] == 'raise' else ('ok_exact=' + str(r[1]['exact']))
print('fail_closed', closed)

json.dump(dict(counts=dict(rep), heldout_by_wording={f'{k[0]}:{k[1]}': v for k, v in sorted(by_wording.items())},
               heldout_bad=bad[:50], fails={str(k): v for k, v in fails.items()}, pertype={str(k): v for k, v in pertype.items()},
               wrong=dict(wrong_right), fail_closed=closed, notes=notes,
               sha256={str(p): sha(p) for p in (K/'h1eval/scorers.py', PATCHED, OUT/'SCORER_PATCH/placement.patch', K/'items/devs1_routed.json',
                                                 OUT/'HELDOUT_CAMERA_ITEMS.json', OUT/'WORDINGS.json', K/'rows/expected_calls.py')}),
          open('/scratch/jjyeung/orch_n30/sb_arev2/scratch/scorer_check.json', 'w'), indent=1, default=str)
