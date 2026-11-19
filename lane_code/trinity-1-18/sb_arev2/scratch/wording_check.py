"""Training vs held-out/benchmark wording overlap: char and word normalized Levenshtein, longest shared word run."""
import ctypes, gzip, hashlib, json, re, unicodedata
from collections import Counter
from pathlib import Path

ME = Path('/scratch/jjyeung/orch_n30/sb_arev2/scratch')
OUT = Path('/scratch/jjyeung/orch_n30/sb_rowA/out')
K = Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/bases/b1/src')
T = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
L = ctypes.CDLL(str(ME/'lev.so')); L.lev.restype = ctypes.c_int
W = json.loads((OUT/'WORDINGS.json').read_text())
CAM = ('camera_displacement', 'camera_rotation', 'camera_movement_direction')


def norm(s, strip_options=False):
    s = unicodedata.normalize('NFKC', s).casefold()
    s = s.translate({0x2019: "'", 0x2018: "'", 0x201c: '"', 0x201d: '"', 0x2013: '-', 0x2014: '-', 0x2212: '-'})
    if strip_options:
        s = re.sub(r'\b[a-d][.)]\s*(left|right|forward|backward)\b[;,]?', ' ', s)
        s = re.sub(r'(the options are|choices?:|choose from:|options:)[^?]*$', ' ', s)
        s = re.sub(r'\b(left|right|forward|backward)(,| and| or)\s', ' ', s)
    s = re.sub(r'\d+(\.\d+)?', '#', s)
    return ' '.join(s.split())


def arr(s):
    a = (ctypes.c_int * len(s))(*map(ord, s)); return a, len(s)


def cd(a, b):
    if not a and not b: return 0.0
    m = max(len(a), len(b))
    if abs(len(a) - len(b)) / m >= 0.5: return abs(len(a) - len(b)) / m
    x, n = arr(a); y, k = arr(b); return L.lev(x, n, y, k) / m


def wd(a, b):
    a, b = a.split(), b.split(); m = max(len(a), len(b)) or 1
    voc = {w: i for i, w in enumerate(set(a) | set(b))}
    x = (ctypes.c_int * len(a))(*[voc[w] for w in a]); y = (ctypes.c_int * len(b))(*[voc[w] for w in b])
    return L.lev(x, len(a), y, len(b)) / m


def run(a, b):
    a, b = a.split(), b.split(); best = 0; prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i-1] == b[j-1]: cur[j] = prev[j-1] + 1; best = max(best, cur[j])
        prev = cur
    return best


def inst(t, kind):
    return t.replace('{i}', '7').replace('{j}', '9').replace('{n}', '32').replace('{unit}', 'meters').replace('{options}', 'A. left; B. right; C. forward; D. backward')


def questions(v, acc):
    if isinstance(v, dict):
        for k, x in v.items():
            if k == 'question' and isinstance(x, str): acc.append(x)
            else: questions(x, acc)
    elif isinstance(v, list):
        for x in v: questions(x, acc)


files = [p['path'] for p in W['corpus_files']] + [str(K/'items/devs1_routed.json'), str(K/'items/r0dev.json'), str(K/'inputs/r0dev/R0_QUESTIONS_dev_f32.jsonl'),
         str(K/'b/work/meta/x/sj/orch_cd/legs1_routed/out2/CAMERA_TASKS.jsonl'), str(K/'b/work/meta/x/sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl')]
files += [str(p) for p in sorted((ME/'h1vsti_q/h1vsti/in/out/qsets').glob('*.jsonl'))]
files += [str(T/'tests/fixtures/benchmark_eval/vstibench/vstibench_repr_450_v2.json'), str(T/'tests/fixtures/benchmark_eval/vsibench/answerable500_gt_canonical.json')]
seen, corpus_raw, finfo = set(), [], []
for f in files:
    p = Path(f)
    if not p.is_file(): finfo.append((f, 'MISSING')); continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h in seen: continue
    seen.add(h); acc = []
    txt = p.read_text()
    if f.endswith('.jsonl'):
        for line in txt.splitlines():
            if line.strip():
                try: questions(json.loads(line), acc)
                except Exception: pass
    else:
        try: questions(json.loads(txt), acc)
        except Exception: pass
    finfo.append((f, h[:12], len(acc))); corpus_raw += acc
corpus = {norm(q) for q in corpus_raw}; corpus_s = {norm(q, True) for q in corpus_raw}
camc = {q for q in corpus if 'camera' in q or 'frame' in q}; camc_s = {q for q in corpus_s if 'camera' in q or 'frame' in q}
rows = [json.loads(l) for l in open(OUT/'CAMERA_ROWS.jsonl')]
train_t = {(t, f't{k:02d}'): inst(x, t) for t in CAM for k, x in enumerate(W['training'][t])}
train_q = {norm(r['student_input']['question']) for r in rows}
held_t = {(t, f'h{k:02d}'): inst(x, t) for t in CAM for k, x in enumerate(W['heldout'][t])}
held_q = {norm(it['question']) for it in json.loads((OUT/'HELDOUT_CAMERA_ITEMS.json').read_text())['items']}
TH = (0.2, 0.3, 0.4, 0.5)


def compare(A, Bset, label, strip=False):
    res = dict(pairs=0, min_char=9, min_word=9, max_run=0, below_char={str(t): 0 for t in TH}, below_word={str(t): 0 for t in TH})
    closest = []
    for a in A:
        na = norm(a, strip)
        for b in Bset:
            dc = cd(na, b); res['pairs'] += 1
            for t in TH:
                if dc < t: res['below_char'][str(t)] += 1
            if dc < 0.5:
                dw = wd(na, b); rr = run(na, b)
                for t in TH:
                    if dw < t: res['below_word'][str(t)] += 1
                res['min_word'] = min(res['min_word'], dw); res['max_run'] = max(res['max_run'], rr)
                closest.append((round(dc, 3), round(dw, 3), rr, na[:110], b[:110]))
            res['min_char'] = min(res['min_char'], dc)
    closest.sort(); res['closest'] = closest[:3]
    print(label, {k: v for k, v in res.items() if k != 'closest'}); return res


out = dict(files=finfo, corpus_questions=len(corpus_raw), corpus_unique_norm=len(corpus), camera_corpus_unique_norm=len(camc))
tt = list(train_t.values()); hq = {norm(x) for x in held_t.values()} | held_q
out['train_templates_vs_heldout'] = compare(tt, hq, 'templates vs heldout')
out['train_templates_vs_heldout_stripopts'] = compare(tt, {norm(x, True) for x in list(held_t.values())}, 'templates vs heldout (options stripped)', True)
out['train_questions_vs_heldout'] = compare(list(train_q), hq, 'train questions vs heldout')
out['train_templates_vs_camera_corpus'] = compare(tt, camc, 'templates vs camera corpus')
out['train_templates_vs_camera_corpus_stripopts'] = compare(tt, camc_s, 'templates vs camera corpus (options stripped)', True)
out['train_templates_vs_all_corpus'] = compare(tt, corpus, 'templates vs all corpus')
out['train_questions_vs_camera_corpus'] = compare(list(train_q), camc, 'train questions vs camera corpus')
out['heldout_vs_camera_corpus_info'] = compare([x for x in held_t.values()], camc, 'heldout templates vs camera corpus (info)')
# longest shared word run per held-out template against all training templates
runs = {f'{k[0]}:{k[1]}': max(run(norm(h), norm(t)) for t in tt) for k, h in held_t.items()}
out['heldout_max_shared_run_with_training'] = dict(sorted(runs.items(), key=lambda kv: -kv[1])[:6])
json.dump(out, open(ME/'wording_check.json', 'w'), indent=1)
print(json.dumps({k: out[k] for k in ('corpus_questions', 'corpus_unique_norm', 'camera_corpus_unique_norm', 'heldout_max_shared_run_with_training')}, indent=1))
for k in ('train_templates_vs_heldout', 'train_templates_vs_camera_corpus', 'train_questions_vs_heldout'): print(k, out[k]['closest'])
