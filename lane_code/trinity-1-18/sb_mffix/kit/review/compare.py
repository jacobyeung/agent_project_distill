"""Compare the reviewer rerun (tmp/rr) with sb_kbox4 PER_ITEM and sb_maskfail outputs; write REVIEW_NUMBERS.json."""
import collections, glob, hashlib, json, pickle, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
BOX = Path('/scratch/jjyeung/orch_n30/sb_kbox4'); KIT = Path('/scratch/jjyeung/orch_n30/sb_maskfail/out')
sys.path.insert(0, str(BOX))
from summarize_train import contrast
import math_v2 as M

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

files = sorted(glob.glob(str(HERE / 'tmp/rr/*.pkl'))); assert len(files) == 209, len(files)
recs, prices = [], {}
for p in files:
    d = pickle.load(open(p, 'rb')); recs += d['records']; prices.update(d['prices'])
ids = {rid for (_, rid) in prices}; assert len(ids) == 1037
arms = sorted({a for (a, _) in prices})
rows = {a: [prices[(a, i)] for i in sorted(ids)] for a in arms}

# 1. endpoints vs PER_ITEM
old = {}
with open(BOX / 'out/box_ladder/PER_ITEM.jsonl') as f:
    for line in f:
        r = json.loads(line)
        if r['row_id'] in ids and r['arm'] in ('A0_deployed', 'A2_gt_masks'):
            old[(r['arm'], r['row_id'])] = r
out = dict(input_sha256={str(BOX / 'out/box_ladder/PER_ITEM.jsonl'): sha(BOX / 'out/box_ladder/PER_ITEM.jsonl'),
                         str(KIT / 'MASKFAIL.json'): sha(KIT / 'MASKFAIL.json'), str(KIT / 'ATTRIBUTION.json'): sha(KIT / 'ATTRIBUTION.json'),
                         str(KIT / 'COUNTERFACTUAL_ROWS.json'): sha(KIT / 'COUNTERFACTUAL_ROWS.json'), str(HERE / 'rerun.py'): sha(HERE / 'rerun.py')})
for mine, theirs in (('A0', 'A0_deployed'), ('A2', 'A2_gt_masks')):
    mism = [i for i in ids if prices[(mine, i)]['prediction'] != old[(theirs, i)]['prediction']]
    lab = [i for i in ids if abs(prices[(mine, i)]['label'] - old[(theirs, i)]['label']) > 0]
    out[mine] = dict(mra=100 * float(np.mean([M.mra(r['prediction'], r['label']) for r in rows[mine]])),
                     refusals=sum(r['prediction'] is None for r in rows[mine]), prediction_mismatch_vs_per_item=len(mism), label_mismatch=len(lab))
out['gap_A2_minus_A0'] = contrast(rows['A2'], rows['A0'])

# 2. arms vs kit
kitrows = json.load(open(KIT / 'COUNTERFACTUAL_ROWS.json'))['rows']
kit = {(r['arm'], r['row_id']): r for r in kitrows if r['arm'].startswith('0.5/')}
att = json.load(open(KIT / 'ATTRIBUTION.json'))['thresholds']['0.5']
name = {'ind': 'independent', 'cum': 'cumulative'}
out['arms'] = {}
for a in arms:
    if '/' not in a:
        continue
    mode, k = a.split('/'); ka = f'0.5/{name[mode]}/{k}'
    mism = [i for i in ids if prices[(a, i)]['prediction'] != kit[(ka, i)]['prediction']]
    c = contrast(rows[a], rows['A0'])
    out['arms'][a] = dict(estimate=c['estimate'], ci95=c['ci95'], refusals=sum(r['prediction'] is None for r in rows[a]),
                          kit_estimate=att[name[mode]][k]['estimate'], kit_ci95=att[name[mode]][k]['ci95'], kit_refusals=att[name[mode]][k]['refusals'],
                          prediction_mismatch_vs_kit=len(mism))
out['closure_cum_correct_vs_A2'] = sum(prices[('cum/correct', i)]['prediction'] != prices[('A2', i)]['prediction'] for i in ids)
refused = [i for i in ids if prices[('A0', i)]['prediction'] is None]
gain_ref = sum(M.mra(prices[('ind/no_proposal', i)]['prediction'], prices[('ind/no_proposal', i)]['label']) for i in refused) / len(ids) * 100
out['ind_no_proposal_from_A0_refused_rows'] = dict(rows=len(refused), points=gain_ref)
newref = [i for i in ids if prices[('ind/wrong_class', i)]['prediction'] is None and prices[('A0', i)]['prediction'] is not None]
loss = sum(M.mra(prices[('A0', i)]['prediction'], prices[('A0', i)]['label']) for i in newref) / len(ids) * 100
out['ind_wrong_class_new_refusals'] = dict(rows=len(newref), points_lost=loss)

# 3. per-frame agreement with kit (unique capture/object/frame)
kr = json.load(open(KIT / 'MASKFAIL.json'))['records']
ku = {(r['capture'], r['object'], r['frame']): r for r in kr}
mu = {(r['capture'], r['object'], r['frame']): r for r in recs}
assert set(ku) == set(mu)
dis = collections.Counter(); diou = 0.
for k, m in mu.items():
    q = ku[k]
    for t in ('0.3', '0.5', '0.7'):
        if m['kinds'][t] != q['failure_kinds'][t]:
            dis[(t, q['failure_kinds'][t], m['kinds'][t])] += 1
    if m['valid'] and m['visible']:
        diou = max(diou, abs(m['iou'] - q['iou']))
out['frame_agreement'] = dict(unique_object_frames=len(mu), kind_disagreements={'|'.join(k): v for k, v in dis.items()}, max_abs_iou_diff_visible=diou)

# 4. item 5: correct candidate availability layers, row-weighted like the kit
weight = collections.Counter((r['capture'], r['object'], r['frame']) for r in kr)
vis = [(k, m) for k, m in mu.items() if m['valid'] and m['visible']]
avail = {}
for t in ('0.3', '0.5', '0.7'):
    wrong = [(k, m) for k, m in vis if m['iou'] < float(t)]
    w = lambda pred: sum(weight[k] for k, m in wrong if pred(m))
    bykind = collections.defaultdict(lambda: collections.Counter())
    for k, m in wrong:
        pc = m['pool_correct'][t]
        lvl = 'in_accepted_track' if pc['in_track'] else 'liftable_not_in_track' if pc['liftable'] else 'raw_only_score_lt_0.3' if pc['any'] else 'none'
        bykind[m['kinds'][t]][lvl] += weight[k]
    avail[t] = dict(wrong=w(lambda m: True), any_correct=w(lambda m: m['pool_correct'][t]['any']),
                    liftable_score_ge_0p3=w(lambda m: m['pool_correct'][t]['liftable']),
                    in_accepted_track=w(lambda m: m['pool_correct'][t]['in_track']), by_kind={k: dict(v) for k, v in bykind.items()})
out['availability'] = avail
(HERE / 'REVIEW_NUMBERS.json').write_text(json.dumps(out, indent=1) + '\n')
print(json.dumps({k: v for k, v in out.items() if k not in ('input_sha256',)}, indent=1))
