"""Own banded Levenshtein: delivered questions vs the pinned held-out wording corpus (threshold 0.05 of max length,
NFKC + casefold + collapsed whitespace), plus a check that the builder's refused sources are true hits."""
import collections as C
import hashlib
import json
import math
import random
import unicodedata
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/sb_brev3')
B3 = Path('/scratch/jjyeung/orch_n30/sb_rowB3')
T = 0.05


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
                return d / max(n, m)
    return None


def main():
    wc = json.loads((B3 / 'inputs/WORDING_CORPUS.json').read_text())
    corpus = sorted({norm(s) for s in wc['questions']})
    rows = [json.loads(s) for s in (B3 / 'out/rows.jsonl').read_text().splitlines()]
    qs = sorted({norm(r['student_input']['question']) for r in rows})
    refused = json.loads((B3 / 'out/REFUSALS.json').read_text())['wording_hits']
    src = {json.loads(s)['qid']: json.loads(s) for s in (B3 / 'inputs/sources.jsonl').read_text().splitlines()}
    rq = sorted(refused)
    sample = random.Random('sb_brev3|wording').sample(rq, min(100, len(rq)))
    # the builder refused on any option permutation; the source's own wording is a lower bound, so test it and record
    sq = [norm(src[q]['student_input']['question']) for q in sample]
    with ProcessPoolExecutor(16, initializer=init, initargs=(corpus,)) as ex:
        delivered = list(ex.map(hit, qs, chunksize=32))
        ref = list(ex.map(hit, sq, chunksize=4))
    res = dict(corpus_unique=len(corpus), delivered_unique_questions=len(qs), delivered_hits=sum(d is not None for d in delivered),
               refused_sample=len(sample), refused_sample_source_wording_hits=sum(d is not None for d in ref),
               corpus_sha256=hashlib.sha256((B3 / 'inputs/WORDING_CORPUS.json').read_bytes()).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (W / 'out/RV_WORDING.json').write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
