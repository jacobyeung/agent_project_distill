"""Helpers for lane san_dd_size (read-only analysis of object-size traces). Builds /tmp caches if absent."""
import json, os, re, sys, sqlite3, statistics as st, collections
KIT = '/scratch/jjyeung/orch_n30/swarm_an/kit'
STORE = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
DEV_CACHE, ROW_CACHE = '/tmp/sdd_dev.json', '/tmp/sdd_size_rows.json'
STEPS = (('S1', 544), ('R1', 100), ('R1', 200))
UNIT_CM = {'cm': 1.0, 'in': 2.54, 'ft': 30.48, 'm': 100.0}

def dev(cache=True):
    if not cache or not os.path.isfile(DEV_CACHE):
        sys.path.insert(0, KIT); import san_kit as K
        D = {}
        for run, step in STEPS:
            for s in ('dev-S1', 'R0-dev'):
                rows = K.direct(run, step, s, types=['object_size_estimation'])
                D['%s|%d|%s' % (run, step, s)] = [{k: r[k] for k in ('id', 'question', 'gt', 'gt_released', 'pred', 'score', 'pred_on', 'score_on', 'text', 'room', 'forced_close', 'subtype', 'unit', 'stratum')} for r in rows]
        if not cache: return D
        json.dump(D, open(DEV_CACHE, 'w'))
    return json.load(open(DEV_CACHE))

def rows(cache=True):
    """All 9,778 store-v7 object-size rows, fetched by primary key (200 per query)."""
    if not cache or not os.path.isfile(ROW_CACHE):
        fam = json.load(open(STORE + '/FAMILY_INDEX_RANGES.json'))['families']['object_size_estimation']
        ids = [i for a, b in fam for i in range(a, b + 1)]
        db = sqlite3.connect('file:' + STORE + '/vqa/rows.sqlite?mode=ro', uri=True); out = []
        for k in range(0, len(ids), 200):
            b = ids[k:k + 200]
            for i, raw in db.execute('select i,row from rows where i in (%s)' % ','.join('?' * len(b)), b):
                r = json.loads(raw); si = r['student_input']
                out.append(dict(i=i, qid=r['qid'], scene=r.get('scene'), dataset=r.get('dataset'), q=si['question'], a=r['answer'], t=r['target'],
                    cited=(r.get('retrace_a2') or {}).get('cited'), raster=(r.get('retrace_a2') or {}).get('raster'), a2rule=(r.get('retrace_a2') or {}).get('rule'),
                    gtk=(r.get('provenance') or {}).get('gt_kind'), nf=si.get('total_num_frames'),
                    extra={k: v for k, v in r.items() if k not in ('student_input', 'target', 'provenance', 'retrace', 'retrace_a2', 'license')}))
        db.close()
        if not cache: return out
        json.dump(out, open(ROW_CACHE, 'w'))
    return json.load(open(ROW_CACHE))

def unit(q):
    q = q.lower()
    if re.search(r'centimet|\bcm\b', q): return 'cm'
    if 'inch' in q: return 'in'
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b', q): return 'ft'
    if re.search(r'\bmeters?\b|\bmetres?\b', q): return 'm'
    return None

def dcls(q):
    """Object class of a dev question (dev-S1 phrasings and the R0-dev template)."""
    m = re.match(r'What is the length of the longest dimension \(length, width, or height\) of the (.*), measured in centimeters\?$', q)
    if m: return m.group(1).strip().lower()
    s = q.split('the ')[-1]
    return re.split(r"'s |'s$| in | measured| using|,|\?| stated| expressed| along|\.$", s)[0].strip().lower()

def tcls(r, byq=None):
    """Object class of a training row; paraphrase rows inherit the class of the row they paraphrase."""
    q = r['q']
    for p in (r'What is the length of the longest edge of the (.*), in centimeters\?$',
              r'What is the length of the longest dimension \(length, width, or height\) of the (.*), measured in centimeters\?$',
              r'Measure the (.*) along its longest dimension and give that length in centimeters\.$',
              r'Of the length, width, and height of the (.*), what is the largest measurement in centimeters\?$',
              r'How long is the longest side of the (.*)\? State its length in centimeters\.$'):
        m = re.match(p, q)
        if m: return m.group(1).strip().lower()
    return None

def mra(p, g):
    p, g = float(p), float(g)
    return sum(abs(p - g) / g <= 1 - t / 100 + 1e-12 for t in range(50, 100, 5)) / 10

def num(x):
    try: return float(x)
    except Exception: return None

def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
            for k in range(i, j + 1): r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    a, b = rk(x), rk(y)
    ma, mb = st.mean(a), st.mean(b)
    den = (sum((u - ma) ** 2 for u in a) * sum((v - mb) ** 2 for v in b)) ** .5
    return sum((u - ma) * (v - mb) for u, v in zip(a, b)) / den if den else float('nan')

def think(t):
    return (t or '').split('</think>')[0].strip()

def train_stats(R=None):
    """Class -> list of answers (cm) over BASE rows (paraphrases dropped: they repeat their base row's scene, object and answer)."""
    R = R if R is not None else rows(); base = collections.defaultdict(list); allr = collections.defaultdict(list)
    for r in R:
        c = tcls(r)
        a = num(r['a'])
        if c is None or a is None: continue
        allr[c].append(a)
        if not r['extra'].get('paraphrase_of'): base[c].append(a)
    return base, allr
