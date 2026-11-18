import json, re, numpy as np, random
from collections import Counter, defaultdict
from cd_load import load, load_on16k
TYPES = ('object_rel_direction_hard', 'object_rel_direction_medium', 'object_rel_direction_easy')
D, _ = load(types=TYPES)
SEED = 20261118
def boot(delta, rooms, draws=10000):
    by = defaultdict(list)
    for d, r in zip(delta, rooms): by[r].append(d)
    R = list(by); S = np.array([sum(by[r]) for r in R]); N = np.array([len(by[r]) for r in R]); K = len(R)
    rng = random.Random(SEED); out = []
    while len(out) < draws:
        c = np.bincount(rng.choices(range(K), k=K), minlength=K); n = c @ N
        if n: out.append((c @ S) / n)
    return np.quantile(out, [0.025, 0.975])
def opts_of(path_rec):
    return None
# need options: reload with options
import json as J
from cd_load import SOURCES
def load_opts(ex, s):
    p = SOURCES[ex][s]; out = {}
    for line in open(p):
        r = J.loads(line)
        if r.get('question_type') == 'object_rel_direction_hard': out[r['id']] = r.get('options')
    return out
L = []
for s in ['dev-S1', 'R0-dev']:
    O = load_opts('S544', s)
    def content(i, letter):
        for o in O[i] or []:
            if o.strip().upper().startswith((letter or '?').strip().upper() + '.'): return o.split('.', 1)[1].strip().lower()
        return '?'
    hard = {ex: {i: r for i, r in D[ex][s].items() if r['question_type'] == 'object_rel_direction_hard'} for ex in ['S544', 'D0m100', 'H1m100', 'R1m100'] if s in D[ex]}
    B = hard['S544']
    gt_back = sum('back' in content(i, B[i]['ground_truth']) for i in B)
    L.append(f'\n== {s} direction hard: n={len(B)}, rooms={len({r["room"] for r in B.values()})}; GT is a back option on {gt_back}')
    qforms = Counter(re.sub(r'the [a-z ]+?(?=[,?])', 'the X', B[i]['question'])[:90] for i in B)
    L.append('  question forms: ' + ' || '.join(f'{c}x {q}' for q, c in qforms.most_common(3)))
    away = [i for i in B if re.search(r'facing away|opposite direction', B[i]['question'])]
    L.append(f'  items worded as facing away / opposite direction: {len(away)}')
    for ex, H in hard.items():
        back = sum('back' in content(i, H[i]['extracted_answer']) for i in H)
        acc = 100 * np.mean([float(H[i]['score']) for i in H])
        acc_gtback = 100 * np.mean([float(H[i]['score']) for i in H if 'back' in content(i, B[i]['ground_truth'])])
        acc_gtfront = 100 * np.mean([float(H[i]['score']) for i in H if 'back' not in content(i, B[i]['ground_truth'])])
        dist = Counter(content(i, H[i]['extracted_answer']) for i in H)
        L.append(f'  {ex:7} acc {acc:5.1f}; answers a back option {back}/{len(H)}; acc on GT-back {acc_gtback:5.1f} (n={gt_back}), on GT-front {acc_gtfront:5.1f} (n={len(H)-gt_back}); answers {dict(dist.most_common())}')
        if ex != 'S544':
            ids = list(B)
            for nm, sub in [('all', ids), ('GT back', [i for i in ids if 'back' in content(i, B[i]['ground_truth'])]), ('GT front', [i for i in ids if 'back' not in content(i, B[i]['ground_truth'])])]:
                dl = [100 * (float(H[i]['score']) - float(B[i]['score'])) for i in sub]
                lo, hi = boot(dl, [B[i]['room'] for i in sub])
                L.append(f'      {ex}-S544 {nm:8} n={len(sub):>3} {np.mean(dl):+6.2f} [{lo:+6.2f},{hi:+6.2f}]')
    # flips R1 vs S544: front->back errors
    R1 = hard['R1m100']
    tr = Counter()
    for i in B:
        b_ok = float(B[i]['score']) == 1; r_ok = float(R1[i]['score']) == 1
        if b_ok and not r_ok:
            tr[f"lost: GT {content(i, B[i]['ground_truth'])} -> R1 {content(i, R1[i]['extracted_answer'])}"] += 1
        if r_ok and not b_ok:
            tr[f"won: GT {content(i, B[i]['ground_truth'])} (544 said {content(i, B[i]['extracted_answer'])})"] += 1
    L.append('  R1 vs 544 flips: ' + '; '.join(f'{k} x{v}' for k, v in tr.most_common(12)))
open('Q4_REPORT.txt', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))

# R0-dev split by wording
s = 'R0-dev'
O = load_opts('S544', s)
def content2(i, letter):
    for o in O[i] or []:
        if o.strip().upper().startswith((letter or '?').strip().upper() + '.'): return o.split('.', 1)[1].strip().lower()
    return '?'
hard = {ex: {i: r for i, r in D[ex][s].items() if r['question_type'] == 'object_rel_direction_hard'} for ex in ['S544', 'D0m100', 'H1m100', 'R1m100']}
B = hard['S544']
M = []
for nm, f in [('away-worded', lambda i: bool(re.search(r'facing away|opposite direction', B[i]['question']))), ('plain-worded', lambda i: not re.search(r'facing away|opposite direction', B[i]['question']))]:
    ids = [i for i in B if f(i)]
    gtb = sum('back' in content2(i, B[i]['ground_truth']) for i in ids)
    row = [f'  R0-dev hard {nm}: n={len(ids)}, GT back {gtb}']
    for ex in ['S544', 'D0m100', 'H1m100', 'R1m100']:
        H = hard[ex]
        acc = 100 * np.mean([float(H[i]['score']) for i in ids]); bk = sum('back' in content2(i, H[i]['extracted_answer']) for i in ids)
        row.append(f'{ex} acc {acc:.1f} back answers {bk}')
    M.append('; '.join(row))
    dl = [100 * (float(hard['R1m100'][i]['score']) - float(B[i]['score'])) for i in ids]
    lo, hi = boot(dl, [B[i]['room'] for i in ids]); M.append(f'    R1m100-S544 {np.mean(dl):+.2f} [{lo:+.2f},{hi:+.2f}]')
open('Q4_REPORT.txt', 'a').write('\n'.join(M) + '\n'); print('\n'.join(M))
