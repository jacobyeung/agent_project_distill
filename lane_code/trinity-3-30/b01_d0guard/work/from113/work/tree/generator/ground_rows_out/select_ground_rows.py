"""Deterministic subset selection. Never edit a selected JSONL line."""
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

EDGES = (0, .5, 1, 2, 4, None)
BIN_NAMES = ('0-0.5', '0.5-1', '1-2', '2-4', '4+')


def bin_id(value):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError('invalid distance')
    return next(i for i, hi in enumerate(EDGES[1:]) if hi is None or value < hi)


def apportion(n, weights):
    total = sum(weights)
    counts = [n*w//total for w in weights]
    order = sorted(range(len(weights)), key=lambda i: (-(n*weights[i] % total), i))
    for i in order[:n-sum(counts)]:
        counts[i] += 1
    return counts


def select(metadata, benchmark):
    bench = Counter()
    with Path(benchmark).open() as f:
        for line in f:
            r = json.loads(line)
            if r['question_type'] == 'object_abs_distance':
                bench[bin_id(r['ground_truth'])] += 1
    weights = [bench[i] for i in range(5)]
    absolute, relative, selected = defaultdict(list), defaultdict(list), set()
    option_mix = Counter()
    for r in metadata:
        typ = r['type']
        if typ == 'object_abs_distance':
            absolute[bin_id(r['gt_answer'])].append(r)
        elif typ == 'object_rel_distance':
            relative[r['answer']].append(r)
            option_mix[len(r['options'])] += 1
        else:
            selected.add(r['candidate_id'])
    rank = lambda r: hashlib.sha256(('ground-selection-v8\0'+r['candidate_id']).encode()).digest()
    capacity = [len(absolute[i]) for i in range(5)]
    # Hamilton quotas differ from the requested shares by <1 row per bin.
    # A feasible quota has n*w/total < capacity+1; this is a strict upper bound.
    upper = min([sum(capacity)]+[math.ceil((capacity[i]+1)*sum(weights)/w)-1
                                for i, w in enumerate(weights) if w])
    for n in range(upper, -1, -1):
        quotas = apportion(n, weights)
        if all(q <= c for q, c in zip(quotas, capacity)):
            break
    for i, quota in enumerate(quotas):
        selected.update(r['candidate_id'] for r in sorted(absolute[i], key=rank)[:quota])
    letters = 'ABCD'
    # Exact global equality is feasible whenever all four letters are present.
    # D exists only in four-option rows. Keep the largest equal-count subset.
    relative_keep = min((len(relative[k]) for k in letters), default=0)
    for k in letters:
        selected.update(r['candidate_id'] for r in sorted(relative[k], key=rank)[:relative_keep])
    receipt = dict(schema='ground-subset-selection-v1', algorithm='deterministic-sha256-rank-v8',
                   row_mutations=0, input_rows=len(metadata), selected_rows=len(selected),
                   absolute=dict(bin_edges_m=EDGES, bins=BIN_NAMES, benchmark_counts=weights,
                                 benchmark_shares=[w/sum(weights) for w in weights], available=capacity,
                                 selected=quotas, kept=sum(quotas),
                                 policy='Largest feasible Hamilton-apportioned subset; each bin is within one row of benchmark share'),
                   relative=dict(available={k:len(relative[k]) for k in letters},
                                 option_count_mix=dict(option_mix), selected={k:relative_keep for k in letters},
                                 selected_option_count_mix=dict(Counter(len(r['options']) for r in metadata
                                     if r['type']=='object_rel_distance' and r['candidate_id'] in selected)),
                                 kept=4*relative_keep, shares={k:.25 if relative_keep else None for k in letters},
                                 policy='Largest subset with equal A/B/C/D counts; option-count mix may change',
                                 limitation='D is available only in four-option rows; the rarest letter caps every letter. If any letter is absent, no nonempty four-way balanced subset exists.'),
                   other_types='Keep every admitted direction row unchanged')
    return selected, receipt


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('full_packed'); p.add_argument('benchmark'); p.add_argument('output')
    a = p.parse_args(); out = Path(a.output); out.mkdir(parents=True, exist_ok=False)
    metadata = []
    with open(a.full_packed) as f:
        for line in f:
            r = json.loads(line); g = r['ground_record']
            metadata.append({k:g[k] for k in ('candidate_id','type','answer','gt_answer','options')})
    selected, receipt = select(metadata, a.benchmark)
    src_hash, dst_hash, ids = hashlib.sha256(), hashlib.sha256(), []
    with open(a.full_packed,'rb') as src, (out/'balanced.packed.jsonl').open('xb') as dst:
        for line in src:
            src_hash.update(line); r = json.loads(line)
            if r['candidate_id'] in selected:
                dst.write(line); dst_hash.update(line); ids.append(r['candidate_id'])
    receipt.update(source_sha256=src_hash.hexdigest(), output_sha256=dst_hash.hexdigest(),
                   benchmark=dict(path=str(Path(a.benchmark).resolve()), sha256=hashlib.sha256(Path(a.benchmark).read_bytes()).hexdigest()),
                   membership_sha256=hashlib.sha256(('\n'.join(sorted(ids))+'\n').encode()).hexdigest())
    (out/'SELECTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
