"""Own banded Levenshtein (threshold 0.05 of max codepoint length, NFKC + casefold + collapsed whitespace) against the pinned
held-out wording corpus: every store-v7 source row's own question (all 11,926, MISSING_GT included) and every delivered sb_rowB4 question."""
import collections as C
import hashlib
import json
import math
import sqlite3
import unicodedata
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/sb_brev4')
B4 = Path('/scratch/jjyeung/orch_n30/sb_rowB4')
STORE = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
FAMS = ['camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3',
        'obj_obj_relative_pos_lr', 'obj_obj_relative_pos_nf', 'obj_obj_relative_pos_ud']
T = 0.05
WORKERS = 7


def norm(s):
    return ' '.join(unicodedata.normalize('NFKC', s).casefold().split())


def within(a, b, k):
    n, m = len(a), len(b)
    if abs(n - m) > k:
        return None
    INF = k + 1
    prev = [j if j <= k else INF for j in range(m + 1)]
    for i in range(1, n + 1):
        lo, hi = max(1, i - k), min(m, i + k)
        cur = [INF] * (m + 1)
        if i <= k:
            cur[0] = i
        best = cur[0]
        ai = a[i - 1]
        for j in range(lo, hi + 1):
            v = prev[j - 1] + (ai != b[j - 1])
            if prev[j] + 1 < v:
                v = prev[j] + 1
            if cur[j - 1] + 1 < v:
                v = cur[j - 1] + 1
            cur[j] = v if v < INF else INF
            if cur[j] < best:
                best = cur[j]
        if best > k:
            return None
        prev = cur
    return prev[m] if prev[m] <= k else None


CORPUS = None


def init(corpus):
    global CORPUS
    by = C.defaultdict(list)
    for s in corpus:
        by[len(s)].append(s)
    CORPUS = by


def hit(q):
    n = len(q)
    for m in range(math.ceil(n * (1 - T)), math.floor(n / (1 - T)) + 1):
        k = math.floor(T * max(n, m) + 1e-12)
        for o in CORPUS.get(m, ()):
            d = within(q, o, k)
            if d is not None:
                return round(d / max(n, m), 4)
    return None


def main():
    wp = B4 / 'inputs/WORDING_CORPUS.json'
    wc = json.loads(wp.read_text())
    corpus = sorted({norm(s) for s in wc['questions']})
    con = sqlite3.connect('file:' + str(STORE / 'vqa/rows.sqlite') + '?mode=ro', uri=True)
    ranges = json.loads((STORE / 'FAMILY_INDEX_RANGES.json').read_text())['families']
    src = {}
    for fam in FAMS:
        for a, b in ranges[fam]:
            for (s,) in con.execute('select row from rows where i between ? and ?', (a, b)):
                r = json.loads(s)
                src[r['qid']] = (fam, norm(r['student_input']['question']))
    con.close()
    rows = [json.loads(s) for s in (B4 / 'out/rows.jsonl').read_text().splitlines()]
    dq = sorted({norm(r['student_input']['question']) for r in rows})
    sq = sorted({v[1] for v in src.values()})
    with ProcessPoolExecutor(WORKERS, initializer=init, initargs=(corpus,)) as ex:
        dres = dict(zip(dq, ex.map(hit, dq, chunksize=16)))
        print('delivered done', sum(v is not None for v in dres.values()), flush=True)
        sres = dict(zip(sq, ex.map(hit, sq, chunksize=16)))
    hits = {q: sres[v[1]] for q, v in src.items() if sres[v[1]] is not None}
    res = dict(corpus_unique=len(corpus), corpus_sha256=hashlib.sha256(wp.read_bytes()).hexdigest(),
               delivered_unique_questions=len(dq), delivered_hits=sum(v is not None for v in dres.values()),
               sources=len(src), source_unique_questions=len(sq), source_own_wording_hits=len(hits),
               source_hits_by_family=dict(C.Counter(src[q][0] for q in hits)),
               source_hit_qids=dict(sorted(hits.items())),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (W / 'out/RV4_WORDING.json').write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'source_hit_qids'}, indent=1))


if __name__ == '__main__':
    main()
