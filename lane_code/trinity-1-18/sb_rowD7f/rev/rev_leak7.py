"""Clause predictability without reading the clause: my own mask and classifiers (no sb_rowD* code imported)."""
import collections as C, hashlib, json, pickle, re, sqlite3, sys
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent; W = HERE / 'work'
B = Path('/scratch/jjyeung/orch_n30/sb_rowD7f/out')  # sb_rowD7f: filtered rows
DB = '/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite'
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/work/tree_r1')
CFG = json.load(open(TREE.parents[0] / 'build20/inputs/config.json'))
sys.path.insert(0, str(TREE))
from student_pilot import row_removals, r1_population
CLAUSE = r'(?:facing away from|face away from|turned away from|with my back to|with my back turned to|facing toward|face toward|looking toward|look toward|looking at|look at|facing|face)'
RATE = json.load(open(W / 'ROOMS_REVIEW.json'))['allocation']['v7_plus_twins_as_delivered']['draws_per_row']  # sb_rowD7f


def opts(r): return {m[1]: m[2].strip().lower() for m in (re.fullmatch(r'([A-Z])\.\s*(.+)', s) for s in r['student_input']['options'])}


def step1_names(line):
    for pat in (r'Step 1: (?:find|locate) the (.+?), the (.+?) and the (.+)\.', r'Step 1: (?:find|locate) the (.+?) and the (.+?), then the (.+)\.'):
        m = re.fullmatch(pat, line)
        if m: return list(m.groups())
    return None


def roles(line, names):
    import itertools
    hits = set()
    for X, Y, Z in itertools.permutations(names):
        e = {k: re.escape(v) for k, v in dict(X=X, Y=Y, Z=Z).items()}
        for pat in (rf'Step 2: facing the {e["Y"]} from the {e["X"]}, I find the {e["Z"]} .+\.',
                    rf'Step 2: standing at the {e["X"]} and facing the {e["Y"]}, I find the {e["Z"]} .+\.',
                    rf'Step 2: I stand at the {e["X"]} facing the {e["Y"]}; I find the {e["Z"]} .+\.',
                    rf'Step 2: I find the {e["Z"]} .+ when I stand at the {e["X"]} facing the {e["Y"]}\.'):
            if re.fullmatch(pat, line): hits.add((X, Y, Z))
    return next(iter(hits)) if len(hits) == 1 else None


def template(q, X, Y, Z):
    """Role-tag the names (longest first), then mask the single clause bound to the heading <Y>."""
    t = q
    for n, tag in sorted(((X, '<X>'), (Y, '<Y>'), (Z, '<Z>')), key=lambda p: -len(p[0])):
        t = re.sub(rf'(?<![\w<]){re.escape(n)}(?![\w>])', tag, t)
    t, k = re.subn(rf'\b{CLAUSE}(?= the <Y>)', '<C>', t, flags=re.I)
    return t, k


def trace_form(row, X, Y, Z):
    lines = row['target'].split('\n')
    sub = lambda s: re.sub('|'.join(re.escape(n) for n in sorted((X, Y, Z), key=len, reverse=True)), '<N>', s)
    return sub(lines[1]), re.sub(r'(at|to) my [\w-]+\.$', '<L>', sub(lines[-4]))


def row_feats(row, X, Y, Z, cl):
    q = row['student_input']['question']; t, k = template(q, X, Y, Z); s1, fin = trace_form(row, X, Y, Z)
    return dict(cl=cl, tmpl=t, nmask=k, step1=s1, final=fin, names=tuple(sorted({X, Y, Z})), roles=(X, Y, Z), label=opts(row)[row['answer']], letter=row['answer'],
                dataset=row['dataset'], fam=row['question_type'].rsplit('_', 1)[1], order=tuple(row['student_input']['options']), scene=row['dataset'] + '/' + row['scene'],
                fps=row['student_input'].get('fps'), frames=hashlib.sha256(json.dumps(row['student_input']['frame_indices']).encode()).hexdigest()[:12],
                qlen=len(q), clause_words_left=bool(re.search(r'\b(away|toward|towards|back to|behind me)\b', t.split('\n')[0], re.I)))


def bayes(rows, f, w=None):
    tab = C.defaultdict(C.Counter)
    for i, r in enumerate(rows): tab[f(r)][r['cl']] += (w[i] if w is not None else 1)
    tot = sum(sum(c.values()) for c in tab.values())
    return round(sum(max(c.values()) for c in tab.values()) / tot, 4), len(tab)


def folds(groups, k=5):
    keys = sorted(set(groups), key=lambda g: hashlib.sha256(str(g).encode()).hexdigest())
    fold = {g: i % k for i, g in enumerate(keys)}
    return np.array([fold[g] for g in groups])


def cv_majority(rows, f, groups):
    fo = folds(groups); y = np.array([r['cl'] == 'away' for r in rows]); correct = 0
    for k in range(5):
        tab = C.defaultdict(C.Counter); tr = np.where(fo != k)[0]; te = np.where(fo == k)[0]
        for i in tr: tab[f(rows[i])][y[i]] += 1
        prior = y[tr].mean() >= 0.5
        for i in te:
            c = tab.get(f(rows[i]))
            pred = (c[True] > c[False]) if c and c[True] != c[False] else prior
            correct += pred == y[i]
    return round(correct / len(rows), 4)


def onehot(rows, keys):
    vocab = {}; ri, ci = [], []
    for i, r in enumerate(rows):
        toks = set()
        for k in keys:
            if k == 'bow': toks |= {'w:' + w for w in re.findall(r"[<>\w-]+", r['tmpl'].lower())}
            elif k == 'name_tokens': toks |= {'n:' + n for n in r['names']}
            else: toks.add(k + ':' + str(r[k]))
        for t in toks:
            ri.append(i); ci.append(vocab.setdefault(t, len(vocab)))
    return sparse.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=(len(rows), len(vocab)))


def cv_logreg(rows, keys, groups, lam=1.0):
    X = onehot(rows, keys); y = np.array([r['cl'] == 'away' for r in rows], float); fo = folds(groups); correct = 0
    for k in range(5):
        tr, te = fo != k, fo == k; Xt, yt = X[tr], y[tr]
        def f(w):
            z = Xt @ w[:-1] + w[-1]; p = 1 / (1 + np.exp(-z))
            loss = np.sum(np.logaddexp(0, z) - yt * z) + 0.5 * lam * w[:-1] @ w[:-1]
            g = p - yt; return loss, np.append(Xt.T @ g + lam * w[:-1], g.sum())
        w = minimize(f, np.zeros(X.shape[1] + 1), jac=True, method='L-BFGS-B', options=dict(maxiter=300)).x
        correct += int((((X[te] @ w[:-1] + w[-1]) > 0) == (y[te] > 0.5)).sum())
    return round(correct / len(rows), 4), X.shape[1]


def main():
    con = sqlite3.connect('file:' + DB + '?mode=ro&immutable=1', uri=True)
    new = [json.loads(l) for l in open(B / 'NEW_ROWS.jsonl')]
    smap = {m['qid']: m for m in map(json.loads, open(B / 'SOURCE_MAP.jsonl'))}
    teach, groups, bad, cellsN = [], [], C.Counter(), []
    for r in new:
        m = smap[r['qid']]; s = json.loads(con.execute('select row from rows where i=?', (m['source_i'],)).fetchone()[0])
        rl = roles(s['target'].split('\n')[2], step1_names(s['target'].split('\n')[1]) or m['objects'])
        if rl is None: bad['roles_unparsed'] += 1; rl = tuple(m['objects'])
        a, b = row_feats(s, *rl, 'toward'), row_feats(r, *rl, 'away')
        bad['pair_template_differs'] += a['tmpl'] != b['tmpl']; bad['mask_count_not_1'] += (a['nmask'] != 1) + (b['nmask'] != 1)
        bad['clause_words_left_in_template'] += a['clause_words_left'] + b['clause_words_left']
        teach += [a, b]; groups += [s['qid'], s['qid']]; cellsN += [r1_population.family(s, 'vqa'), r1_population.family(r, 'vqa')]
    out = dict(teaching_rows=len(teach), mask_audit=dict(bad), templates=len({t['tmpl'] for t in teach}))
    sets = {
        'template': lambda t: t['tmpl'], 'name_set': lambda t: t['names'], 'role_triple': lambda t: t['roles'],
        'answer_label': lambda t: t['label'], 'answer_letter': lambda t: t['letter'], 'dataset': lambda t: t['dataset'],
        'template+name_set': lambda t: (t['tmpl'], t['names']), 'template+label': lambda t: (t['tmpl'], t['label']),
        'template+letter': lambda t: (t['tmpl'], t['letter']), 'template+dataset': lambda t: (t['tmpl'], t['dataset']),
        'name_set+label': lambda t: (t['names'], t['label']), 'name_set+letter': lambda t: (t['names'], t['letter']),
        'template+name_set+label+letter+dataset': lambda t: (t['tmpl'], t['names'], t['label'], t['letter'], t['dataset']),
        'all_inputs(template,roles,dataset,options,frames,fps,scene)': lambda t: (t['tmpl'], t['roles'], t['dataset'], t['order'], t['frames'], t['fps'], t['scene']),
        'family+label': lambda t: (t['fam'], t['label']), 'question_length(reads_clause)': lambda t: t['qlen'],
        'TARGET_step1_line_form(teacher-forced prefix)': lambda t: t['step1'], 'TARGET_final_line_form': lambda t: t['final'],
        'template+TARGET_step1_line_form': lambda t: (t['tmpl'], t['step1'])}
    scenes = [t['scene'] for t in teach]
    out['trace_forms'] = {cl: dict(step1=dict(C.Counter(t['step1'] for t in teach if t['cl'] == cl)), final=dict(C.Counter(t['final'] for t in teach if t['cl'] == cl)))
                          for cl in ('toward', 'away')}
    src = [t for t in teach if t['cl'] == 'toward']; tab = C.defaultdict(C.Counter)
    for t in src: tab[t['tmpl']][t['step1']] += 1
    out['source_step1_form_from_template'] = dict(majority_acc=round(sum(max(c.values()) for c in tab.values()) / len(src), 4), templates=len(tab))
    out['majority'] = {k: dict(in_sample=bayes(teach, f), cv_pair=cv_majority(teach, f, groups), cv_scene=cv_majority(teach, f, scenes)) for k, f in sets.items()}
    lr = {'template_bow': ['bow'], 'template_id': ['tmpl'], 'names': ['name_tokens'], 'template+names': ['tmpl', 'bow', 'name_tokens'],
          'template+names+label+letter+dataset': ['tmpl', 'bow', 'name_tokens', 'label', 'letter', 'dataset'],
          'all': ['tmpl', 'bow', 'name_tokens', 'label', 'letter', 'dataset', 'fam', 'scene', 'fps']}
    out['logreg'] = {k: dict(zip(('cv_pair', 'features'), cv_logreg(teach, v, groups))) | dict(cv_scene=cv_logreg(teach, v, scenes)[0]) for k, v in lr.items()}
    # Balance per template and per name set: no value may carry only one clause.
    for key, f in (('template', sets['template']), ('name_set', sets['name_set']), ('single_name', None)):
        tab = C.defaultdict(C.Counter)
        for t in teach:
            for v in ([f(t)] if f else t['names']): tab[v][t['cl']] += 1
        one = [v for v, c in tab.items() if len(c) == 1]
        out[f'balance_{key}'] = dict(values=len(tab), one_clause_values=len(one), max_abs_away_share_minus_half=round(max(abs(c['away'] / sum(c.values()) - 0.5) for c in tab.values()), 4))
    # As N would sample it: each row weighted by the draws per row of the N cell it lands in (sb_rowD7f).
    w = [RATE[c] for c in cellsN]
    out['teaching_cells_by_clause'] = {cl: dict(C.Counter(c for c, t in zip(cellsN, teach) if t['cl'] == cl)) for cl in ('toward', 'away')}
    out['as_sampled_by_N'] = dict(rates=RATE, **{k: bayes(teach, sets[k], w)[0] for k in ('template', 'name_set', 'template+name_set', 'dataset')})
    # Full Step-1 easy/hard store (v7 rows that pass N's build20 removal lists and division) plus the twins.
    rem = row_removals.Removals(CFG['remove_files']); div = json.load(open(CFG['scene_division']['path'])); train = set(div['train_scenes'])
    D = pickle.load(open(W / 'census.pkl', 'rb'))['dirrows']; full = []; unparsed = 0
    for i, mm in D.items():
        if mm['op'] != 'Step 1' or mm['fam'] == 'medium': continue
        r = json.loads(con.execute('select row from rows where i=?', (i,)).fetchone()[0])
        if rem.match(r) or r['dataset'] + '/' + r['scene'] not in train: continue
        lines = r['target'].split('\n'); nm = step1_names(lines[1]); rl = roles(lines[2], nm) if nm else None
        if rl is None: unparsed += 1; continue
        full.append(row_feats(r, *rl, 'toward'))
    full += [t for t in teach if t['cl'] == 'away']
    tab = C.defaultdict(C.Counter)
    for t in full: tab[t['tmpl']][t['cl']] += 1
    only = {v for v, c in tab.items() if 'away' not in c}
    out['full_step1_store'] = dict(rows=len(full), unparsed_skipped=unparsed, clause=dict(C.Counter(t['cl'] for t in full)), templates=len(tab),
                                   toward_only_templates=len(only), rows_in_toward_only_templates=sum(sum(tab[v].values()) for v in only),
                                   majority_by_template=bayes(full, sets['template'])[0], base_rate_toward=round(sum(t['cl'] == 'toward' for t in full) / len(full), 4),
                                   top_toward_only=sorted(((sum(tab[v].values()), v[:140]) for v in only), reverse=True)[:5])
    out['inputs'] = {str(p): hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (B / 'NEW_ROWS.jsonl', B / 'SOURCE_MAP.jsonl')}
    (W / 'LEAK_REVIEW.json').write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out, indent=1, default=str))


if __name__ == '__main__':
    main()
