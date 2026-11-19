"""Recheck normalized edit distance of every new question against the pinned local dev/benchmark wordings."""
import collections as C, json, unicodedata
from pathlib import Path

B = Path('/scratch/jjyeung/orch_n30/sb_rowD6/out')
T = 0.10


def norm(s): return ' '.join(unicodedata.normalize('NFKC', s).casefold().split())


def lev_within(a, b, k):
    """Levenshtein distance if <= k else k+1 (banded)."""
    la, lb = len(a), len(b)
    if abs(la - lb) > k: return k + 1
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        lo, hi = max(1, i - k), min(lb, i + k)
        cur = [k + 1] * (lb + 1)
        cur[0] = i if i <= k else k + 1
        best = cur[0]
        for j in range(lo, hi + 1):
            v = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
            cur[j] = v
            if v < best: best = v
        if best > k: return k + 1
        prev = cur
    return prev[lb]


def main():
    words = sorted({norm(w['text']) for w in json.load(open(B / 'WORDING_CORPUS.json'))['wordings']})
    bags = [(w, len(w), C.Counter(w)) for w in words]
    qs = sorted({norm(json.loads(l)['student_input']['question']) for l in open(B / 'NEW_ROWS.jsonl')})
    best, hits, dp = 1.0, [], 0
    for q in qs:
        lq, bq = len(q), C.Counter(q)
        for w, lw, bw in bags:
            m = max(lq, lw); k = int(T * m)
            if abs(lq - lw) > k: continue
            d = bq.copy(); d.subtract(bw)
            if max(sum(v for v in d.values() if v > 0), -sum(v for v in d.values() if v < 0)) > k: continue
            dp += 1
            dist = lev_within(q, w, k)
            if dist <= k:
                hits.append((q, w, dist / m))
    out = dict(questions=len(qs), wordings=len(words), pairs=len(qs) * len(words), dp_pairs=dp, threshold=T, hits=hits)
    Path(__file__).with_name('work').joinpath('WORDING_REVIEW.json').write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != 'hits'}), 'hits', len(hits))


if __name__ == '__main__':
    main()
