"""CPU-only ANCHOR diagnostics. All data inputs and outputs are local.

Locate: python3 anchor_analysis.py locate
K1 (requires the missing raw-pool adapter/export):
  python3 anchor_analysis.py kill --input k1_calls.jsonl
The normalized K1 schema is documented in K1_INPUT_SCHEMA.md.
"""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
import numpy as np

ROOT = Path(__file__).resolve().parent
GT_ROOT = Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gt')
SEED = 20261120
DRAWS = 10000
FIND = re.compile(r'^Step \d+: find (?:the )?(.+?), first seen .*?\bframe (\d+(?:\.\d+)?)(?=\D|$)', re.I)
SEEN = re.compile(r'^(?:Locate:\s*)?(?:The )?(.+?) is seen in frame (\d+(?:\.\d+)?)(?=\D|$)', re.I)
NUMERIC_FRAME = re.compile(r'\bframe\s+\d', re.I)


def digest(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write_json(name, data):
    (ROOT / name).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def rate(rows, numerator, denominator=None):
    """Percentile cluster bootstrap of a ratio, retaining room multiplicity."""
    groups = collections.defaultdict(lambda: [0., 0.])
    for r in rows:
        d = float(denominator(r)) if denominator else 1.
        groups[r['room']][0] += float(numerator(r))
        groups[r['room']][1] += d
    a = np.array(list(groups.values()), dtype=float).reshape(-1, 2)
    n = float(a[:, 0].sum())
    d = float(a[:, 1].sum())
    result = dict(numerator=n, denominator=d, rooms=len(a), rate=n/d if d else None,
                  ci95=None, bootstrap_draws=DRAWS, seed=SEED)
    if not d:
        return result
    rng = np.random.RandomState(SEED)
    bs = []
    for _ in range(100):
        idx = rng.randint(len(a), size=(DRAWS//100, len(a)))
        totals = a[idx].sum(axis=1)
        valid = totals[:, 1] > 0
        bs.extend((totals[valid, 0]/totals[valid, 1]).tolist())
    result['ci95'] = np.percentile(bs, [2.5, 97.5]).tolist()
    result['valid_draws'] = len(bs)
    return result


def parse_citations(text):
    claims, unparsed = [], []
    for line in text.splitlines():
        if not NUMERIC_FRAME.search(line):
            continue
        m = FIND.search(line) or SEEN.search(line)
        if not m:
            unparsed.append(line)
            continue
        noun, frame = m.groups()
        key = (noun.strip().casefold(), frame)
        if key not in {(c['noun'], c['frame_text']) for c in claims}:
            claims.append(dict(noun=key[0], frame_text=frame, line=line))
    return claims, unparsed


def raster_inventory():
    inventory = {}
    for p in sorted(GT_ROOT.glob('*_gt/gt/*.npz')):
        capture = ('arkitscenes/' + p.stem if p.parent.parent.name == 'arkit_gt'
                   else p.stem.replace('__', '/'))
        with np.load(p, allow_pickle=False) as z:
            inst = z['inst']
            ids, labels, valid = z['ids'].tolist(), z['labels'].tolist(), z['valid'].tolist()
            assert inst.shape[0] == len(valid) == 32
            shares = np.zeros((len(ids), 32), dtype=float)
            pos = {int(i): j for j, i in enumerate(ids)}
            for f in range(32):
                if not valid[f]:
                    continue
                values, counts = np.unique(inst[f], return_counts=True)
                for v, count in zip(values, counts):
                    if int(v) in pos:
                        shares[pos[int(v)], f] = float(count)/inst[f].size
            inventory[capture] = dict(path=str(p), bytes=p.stat().st_size,
                sha256=digest(p), frame_indices=z['frame_indices'].tolist(), valid=valid,
                shape=list(inst.shape), ids=ids, labels=labels, shares=shares.tolist())
    return inventory


def score_claim(c, gt, source_frames):
    c = dict(c, status='missing_raster', visible=None, visible_any=None, unique=None)
    f = float(c['frame_text'])
    c['valid_citation'] = f.is_integer() and 1 <= f <= 32
    c['frame'] = int(f) if f.is_integer() else f
    if gt is None:
        return c
    if source_frames != gt['frame_indices']:
        c['status'] = 'frame_map_mismatch'
        return c
    indices = [i for i, label in enumerate(gt['labels']) if label.casefold().strip() == c['noun']]
    c['gt_instance_ids'] = [gt['ids'][i] for i in indices]
    if not indices:
        c['status'] = 'literal_label_absent'
        return c
    c['unique'] = len(indices) == 1
    shares = np.array([gt['shares'][i] for i in indices])
    c['visible_any'] = bool((shares >= .01).any())
    c['max_share_any_anchor'] = float(shares.max())
    c['status'] = 'resolved_unique' if c['unique'] else 'resolved_multiple'
    c['cited_share'] = 0.
    if c['valid_citation']:
        f = int(f) - 1
        if not gt['valid'][f]:
            c['status'] = 'invalid_gt_anchor'
            return c
        c['cited_share'] = float(shares[:, f].max())
    c['visible'] = c['cited_share'] >= .01
    return c


def summarize_claims(rows):
    counts = dict(collections.Counter(r['status'] for r in rows))
    eligible = [r for r in rows if r['visible'] is not None and r['visible_any']]
    unique = [r for r in eligible if r['unique']]
    all_resolved = [r for r in rows if r['visible'] is not None]
    return dict(citations=len(rows), items=len({r['item_id'] for r in rows}),
        rooms=len({r['room'] for r in rows}), captures=len({r['scene'] for r in rows}),
        status_counts=counts, invalid_citations=sum(not r['valid_citation'] for r in rows),
        never_visible_at_1pct=sum(r['visible_any'] is False for r in rows),
        unique_instance_conditional=rate(unique, lambda r: r['visible']),
        any_same_label_instance_conditional=rate(eligible, lambda r: r['visible']),
        any_same_label_instance_unconditional=rate(all_resolved, lambda r: r['visible']))


def locate():
    gt = raster_inventory()
    write_json('raster_visibility.json', gt)
    claims, audit, summary = [], [], {}
    for step in (400, 600):
        p = ROOT / f'direct{step}.jsonl.gz'
        main, other = [], []
        with gzip.open(p, 'rt') as f:
            for line in f:
                r = json.loads(line)
                arm = r['raw']['arms']['B2048']
                citations, unparsed = parse_citations(r['arms']['B2048']['trace'])
                item = dict(step=step, item_id=r['item_id'], scene=r['scene'], room=r['room'],
                            question_type=r['question_type'], dataset=r['scene'].split('/')[0],
                            family=r['family'], citations=len(citations), unparsed=unparsed)
                if r['family'] != 'main':
                    other.append(item)
                    continue
                main.append(item)
                g = gt.get(r['scene'])
                item['local_gt'] = g is not None
                item['frame_map_exact'] = g is not None and arm['source_frame_indices'] == g['frame_indices']
                for citation in citations:
                    c = dict(item, **citation)
                    c = score_claim(c, g, arm['source_frame_indices'])
                    claims.append(c)
                audit.append(item)
        local = [r for r in claims if r['step'] == step]
        report = dict(input=str(p), input_sha256=digest(p), arm='B2048',
            main_items=len(main), main_captures=len({r['scene'] for r in main}),
            gt_covered_items=sum(r['local_gt'] for r in main),
            frame_map_exact_items=sum(r['frame_map_exact'] for r in main),
            citation_items=sum(r['citations'] > 0 for r in main),
            unparsed_numeric_frame_lines=sum(len(r['unparsed']) for r in main),
            R0_items=len(other), R0_citation_items=sum(r['citations'] > 0 for r in other),
            R0_visibility_status='NOT COMPUTABLE: anonymized scenes lack a local GT binding',
            overall=summarize_claims(local), groups=[])
        for fields in [('dataset',), ('question_type',), ('dataset','question_type')]:
            keys = sorted({tuple(r[k] for k in fields) for r in main})
            for key in keys:
                selected = [r for r in local if tuple(r[k] for k in fields) == key]
                selected_items = [r for r in main if tuple(r[k] for k in fields) == key]
                report['groups'].append(dict(group=dict(zip(fields,key)),
                    total_items=len(selected_items), **summarize_claims(selected)))
        summary[str(step)] = report
    write_json('locate_summary.json', summary)
    with (ROOT/'locate_claims.jsonl').open('w') as f:
        for c in claims:
            f.write(json.dumps(c, allow_nan=False)+'\n')
    write_json('locate_item_audit.json', audit)
    print(json.dumps({s: dict(main_items=r['main_items'], citation_items=r['citation_items'],
          unparsed=r['unparsed_numeric_frame_lines'], overall=r['overall']) for s,r in summary.items()}, indent=2))


def a3x(candidates, frame):
    """Largest member area on the cited frame; stored pool order breaks exact ties."""
    eligible = [(c, float(c['members'][str(frame)])) for c in candidates
                if str(frame) in c['members']]
    return max(eligible, key=lambda x: x[1])[0] if eligible else None


def best_anchor(visibility):
    eligible = [(int(f), float(area)) for f,area in visibility.items() if area >= .01]
    return min(eligible, key=lambda x:(-x[1], x[0]))[0] if eligible else None


def neighbor_anchor(visibility, best, adjacent_only=False):
    eligible = [int(f) for f,area in visibility.items() if area >= .01 and int(f) != best
                and (not adjacent_only or abs(int(f)-best)==1)]
    return min(eligible, key=lambda f:(abs(f-best), f)) if eligible else None


def kill(path):
    rows = [json.loads(l) for l in Path(path).open()]
    assert len({r['row_id'] for r in rows}) == 1012, 'decision rows must equal 1,012'
    assert len(rows) == 2024, 'two operand occurrences required per decision row'
    out = []
    for r in rows:
        candidates = r['candidates']
        ids = [c['id'] for c in candidates]
        assert len(ids) == len(set(ids))
        baseline = next((c for c in candidates if c['id']==r['baseline_id']), None)
        assert r['baseline_id'] is None or baseline is not None
        best = best_anchor(r['gt_visibility'])
        chosen = a3x(candidates, best) if best is not None else None
        neighbor = neighbor_anchor(r['gt_visibility'], best) if best is not None else None
        adjacent = neighbor_anchor(r['gt_visibility'], best, True) if best is not None else None
        perturbed = a3x(candidates, neighbor) if neighbor is not None else None
        out.append(dict(row_id=r['row_id'], room=r['room'], operand=r['operand'],
            baseline_right=bool(baseline and baseline['on_target']),
            baseline_not_seen=baseline is None, best_frame=best, neighbor_frame=neighbor,
            adjacent_frame=adjacent, a3x_right=bool(chosen and chosen['on_target']),
            a3x_not_seen=chosen is None, chosen_id=chosen['id'] if chosen else None,
            neighbor_right=bool(perturbed and perturbed['on_target']),
            neighbor_not_seen=perturbed is None))
    result = dict(rows=1012, operand_occurrences=len(out), input_sha256=digest(path))
    for key in ('baseline_right','baseline_not_seen','a3x_right','a3x_not_seen'):
        result[key] = rate(out, lambda r:r[key])
    result['paired_on_target_delta'] = rate(out, lambda r:int(r['a3x_right'])-int(r['baseline_right']))
    result['f_fixed_wrong'] = rate(out, lambda r:r['a3x_right'] and not r['baseline_right'], lambda r:not r['baseline_right'])
    result['h_broken_right'] = rate(out, lambda r:r['baseline_right'] and not r['a3x_right'], lambda r:r['baseline_right'])
    neighbors = [r for r in out if r['neighbor_frame'] is not None]
    result['neighbor_eligible'] = len(neighbors)
    result['neighbor_delta_vs_best'] = rate(neighbors, lambda r:int(r['neighbor_right'])-int(r['a3x_right']))
    result['neighbor_on_target'] = rate(neighbors, lambda r:r['neighbor_right'])
    result['neighbor_not_seen'] = rate(neighbors, lambda r:r['neighbor_not_seen'])
    result['gap_MRA_bar'] = 'NOT COMPUTED: requires served distance replay, not on-target substitution'
    result['decision'] = 'INCOMPLETE pending distance-type score and independent review'
    write_json('kill_summary.json', result)
    write_json('kill_calls.json', out)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['locate','kill'])
    p.add_argument('--input')
    args = p.parse_args()
    if args.mode == 'locate':
        locate()
    else:
        kill(args.input)
