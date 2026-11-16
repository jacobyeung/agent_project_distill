"""Shared loading, split and metrics for the selector-head comparison (numpy only; both envs import it)."""
import collections, glob, gzip, hashlib, json, os
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
CAPS = HERE / os.environ.get('SEL_CAPS', 'data/caps')   # data/caps_raw: raw-prompt-only tables
TAG = os.environ.get('SEL_TAG', '')
SCALES = HERE / 'sl118/SCALES_S4.json'
SEED = 20261116


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(splits=None):
    """Candidate rows with split/room from E3's K1 membership (SCALES_S4.json); inputs x attached in row order.
    splits: the splits to read (None = all); a table of another split is never opened."""
    S = json.load(open(SCALES))['captures']
    rows = []
    for p in sorted(glob.glob(str(CAPS / '*.json.gz'))):
        capture = Path(p).name[:-len('.json.gz')].replace('__', '/')
        if splits is not None and S[capture]['split'] not in splits:
            continue
        d = json.load(gzip.open(p, 'rt'))
        assert d['capture'] == capture
        s = S[d['capture']]
        for r, i in zip(d['rows'], d['inputs'], strict=True):
            assert (r['object_id'], r['candidate_id']) == (i['object_id'], i['candidate_id'])
            rows.append(dict(r, x=i['x'], split=s['split'], room=s['room'], capture=d['capture']))
    return rows


def key(r):
    return r['object_id'] + '|' + r['candidate_id']


def auc(y, p):
    # Mann-Whitney with average ranks for ties (equals sklearn roc_auc_score).
    y, p = np.asarray(y), np.asarray(p, float)
    order = np.argsort(p, kind='mergesort')
    ps = p[order]
    ranks = np.empty(len(p))
    i = 0
    while i < len(p):
        j = i
        while j + 1 < len(p) and ps[j + 1] == ps[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    n1 = int((y == 1).sum()); n0 = len(y) - n1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def top1(rows, p):
    """Highest-probability candidate per object_id, ties by SAM peak (kit train.py metrics())."""
    groups = collections.defaultdict(list)
    for r, s in zip(rows, p):
        groups[r['object_id']].append((r, float(s)))
    return float(np.mean([max(g, key=lambda x: (x[1], x[0]['features'].get('peak', 0)))[0]['y'] for g in groups.values()]))


def ap(y, p):
    y, p = np.asarray(y), np.asarray(p, float)
    o = np.argsort(-p, kind='mergesort'); y = y[o]
    tp = np.cumsum(y); prec = tp / np.arange(1, len(y) + 1)
    return float((prec * y).sum() / max(y.sum(), 1))
