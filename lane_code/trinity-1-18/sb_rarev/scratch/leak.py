"""Reviewer leakage check with a word-level normalisation independent of build_camera.normalized."""
import json, re, sys, unicodedata, hashlib
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/sb_rowA')
from wordings import HELDOUT, candidates

OUT = Path('/scratch/jjyeung/orch_n30/sb_rowA/out')
W = json.loads((OUT/'WORDINGS.json').read_text())
T = ('camera_displacement', 'camera_rotation', 'camera_movement_direction')
STOP = set('a an the of in on at to for from by with and or is are was were be this that these those its it their his her as into within '
           'what which how many much does do did your you please use using give report return state find'.split())

def toks(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'\{[a-z]+\}', ' ', s)
    s = re.sub(r'[a-d]\.\s*(left|right|forward|backward)', ' ', s)  # option lists
    s = re.sub(r'\(-?180, ?180\]', ' RANGE ', s)
    s = re.sub(r'\d+(\.\d+)?', ' ', s)
    out = []
    for w in re.findall(r'[a-z]+|RANGE', s):
        for suf in ('ing', 'ed', 'es', 's', 'ly'):
            if len(w) > 5 and w.endswith(suf): w = w[:-len(suf)]; break
        out.append(w)
    return out

def content(ts): return {t for t in ts if t not in STOP}
def bigr(ts): return {(a, b) for a, b in zip(ts, ts[1:])}
def jac(a, b): return len(a & b) / max(1, len(a | b))
def wlev(a, b):
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        new = [i]
        for j, y in enumerate(b, 1): new.append(min(new[-1] + 1, row[j] + 1, row[j-1] + (x != y)))
        row = new
    return row[-1] / max(len(a), len(b), 1)
def lcsub(a, b):
    best = 0; prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            if x == y: cur[j] = prev[j-1] + 1; best = max(best, cur[j])
        prev = cur
    return best

def sim(a, b):
    ta, tb = toks(a), toks(b)
    return dict(wlev=round(wlev(ta, tb), 3), cjac=round(jac(content(ta), content(tb)), 3),
                bjac=round(jac(bigr(ta), bigr(tb)), 3), lcs=lcsub(ta, tb))

# Independent dev/kit corpus: same file inventory, own extraction (any string field holding a question).
def strings(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str) and k in ('question', 'question_text', 'prompt', 'q', 'text') and 'frame' in v.lower(): yield v
            elif isinstance(v, (dict, list)): yield from strings(v)
    elif isinstance(o, list):
        for x in o: yield from strings(x)
corpus = set(); seen = set()
for inv in ('item_file_inventory.txt', 'kit_json_inventory.txt'):
    for p in (OUT/inv).read_text().split():
        b = Path(p).read_bytes(); h = hashlib.sha256(b).hexdigest()
        if h in seen: continue
        seen.add(h)
        d = [json.loads(l) for l in b.decode().splitlines() if l.strip()] if p.endswith('.jsonl') else json.loads(b)
        corpus.update(strings(d))
# Generator templates for existing camera training rows.
corpus.update(['Approximately how far (in meters) did the camera move between frame {i} and frame {j} of 32?',
               'What is the signed camera rotation in degrees between frame {i} and frame {j} of 32? Positive means left; use (-180, 180].',
               "During the sequence between frame {i} and frame {j} of 32, what was the primary consistent direction of the camera's movement relative to its orientation at the start? The options are Left, Right, Forward and Backward."])
cam_corpus = sorted({q for q in corpus if re.search(r'camera', q, re.I)})
# Collapse instantiated duplicates by token form.
uniq = {}
for q in cam_corpus: uniq.setdefault(tuple(toks(q)), q)
print('corpus strings', len(corpus), 'camera strings', len(cam_corpus), 'unique token forms', len(uniq))

def worst(h, refs):
    best = None
    for r in refs:
        s = sim(h, r)
        key = (-s['lcs'], s['wlev'], -s['cjac'])
        if best is None or key < best[0]: best = (key, s, r)
    return best

report = {}
for t in T:
    train = W['training'][t]; unused = [c for c in candidates()[t] if c not in train]
    for k, h in enumerate(HELDOUT[t]):
        bt = worst(h, train); bu = worst(h, unused); bd = worst(h, list(uniq.values()))
        hh = [worst(h, [x for x in HELDOUT[t] if x != h])]
        report[f'{t}|h{k:02d}'] = dict(train=bt[1], train_ref=bt[2], unused=bu[1], dev=bd[1], dev_ref=bd[2][:140], other_heldout=hh[0][1])
mx = lambda key, f: (max if f == 'max' else min)(v[key][m] for v in report.values() for m in [f == 'max' and 'cjac' or 'wlev'])
for k, v in report.items():
    print(k, 'TRAIN', v['train'], '| UNUSED', v['unused'], '| DEV', v['dev'], '| HO', v['other_heldout'])
print('max train cjac', max(v['train']['cjac'] for v in report.values()), 'min train wlev', min(v['train']['wlev'] for v in report.values()),
      'max train lcs', max(v['train']['lcs'] for v in report.values()))
print('max dev cjac', max(v['dev']['cjac'] for v in report.values()), 'min dev wlev', min(v['dev']['wlev'] for v in report.values()),
      'max dev lcs', max(v['dev']['lcs'] for v in report.values()))
# Show the closest training references for the highest-overlap held-out wordings.
for k, v in sorted(report.items(), key=lambda kv: (-kv[1]['train']['lcs'], kv[1]['train']['wlev']))[:6]:
    print('\n', k, v['train'], '\n  H:', HELDOUT[k.split('|')[0]][int(k[-2:])], '\n  T:', v['train_ref'])
for k, v in sorted(report.items(), key=lambda kv: (-kv[1]['dev']['lcs'], kv[1]['dev']['wlev']))[:4]:
    print('\n', k, v['dev'], '\n  H:', HELDOUT[k.split('|')[0]][int(k[-2:])], '\n  D:', v['dev_ref'])
json.dump(report, open('/scratch/jjyeung/orch_n30/sb_rarev/scratch/leak_report.json', 'w'), indent=1)
