"""Checks 2/4 data side: source identity, cell counts, parser vs ground truth, weight-file derivation."""
import json, pickle, re
from collections import Counter
from fractions import Fraction
from pathlib import Path

W = Path(__file__).resolve().parent
FB = Path('/scratch/jjyeung/orch_n30/fb_pack')
recs = pickle.loads((W/'rows.pkl').read_bytes())
card = json.loads((FB/'prior2/work/recovered/card.json').read_text())
weights = json.loads((FB/'prior2/out/TOWARD_HARD_WEIGHTS.json').read_text())
R = {}

R['rows'] = len(recs)
R['digest_eq_col'] = sum(r['digest'] == r['sha_col'] for r in recs)
R['src_equal'] = sum(bool(r.get('src_equal')) for r in recs)
R['family_agree'] = sum(r['fam_tree'] == r['fam_mine'] == r['cell'] for r in recs)
R['target_col_empty'] = sum(r['target_col'] == '{}' for r in recs)
R['qid_unique'] = len({r['qid'] for r in recs}) == len(recs)
counts = Counter(r['fam_tree'] for r in recs)
ceil = {c['type']: Fraction(str(c.get('ceiling_rows_per_step', 0)))*1000/4 for c in card['cells'] if c['stream'] == 'vqa'}
R['cell_vs_card_ceiling'] = {k: [counts.get(k, 0), str(v)] for k, v in ceil.items() if counts.get(k, 0) != v}
R['cells'] = dict(counts)

D = [r for r in recs if r['fam_tree'] in ('direction', 'facing_pairs')]
tab = Counter((r['fam_tree'],) + r['details'][:3] for r in D)
R['class_table'] = {'|'.join(k): v for k, v in sorted(tab.items())}

# Clause ground truth
gt = Counter()
for r in D:
    clause = r['details'][0]
    if r['fam_tree'] == 'facing_pairs':
        gt['facing_field', r['facing'], clause] += 1
    elif r['source'] == 'twins':
        truth = 'away' if r['clause_edit'] and 'away' in r['clause_edit'] else ('toward' if r['clause_edit'] else None)
        gt['twin_clause_edit', truth, clause] += 1
    else:
        gt['v7_direction', None, clause] += 1
R['clause_gt'] = {'|'.join(map(str, k)): v for k, v in sorted(gt.items(), key=str)}
R['clause_wrong_examples'] = [dict(qid=r['qid'], cell=r['fam_tree'], facing=r['facing'], edit=r['clause_edit'],
                                   clause=r['details'][0], q=r['question'][:160])
                              for r in D if (r['fam_tree'] == 'facing_pairs' and r['facing'] != r['details'][0])
                              or (r['source'] == 'twins' and r['clause_edit'] and ('away' in r['clause_edit']) != (r['details'][0] == 'away'))][:8]
# Old vs new parser
dis = Counter()
for r in D:
    o, n = r['old_dims'], r['details'][:3]
    if o != n:
        dis['clause' if o[0] != n[0] else 'side' if o[2] != n[2] else 'diff'] += 1
        dis['old:'+o[0]+'->new:'+n[0]+'|'+o[2]+'->'+n[2]] += 1
R['old_vs_new'] = dict(dis.most_common(20))
R['old_vs_new_rows'] = sum(r['old_dims'] != r['details'][:3] for r in D)

# Side vs my own option parse
def side_of(label):
    if label is None: return 'MISSING'
    return 'back' if re.search(r'\b(back|behind)\b', label) else 'front' if re.search(r'\bfront\b', label) else 'other'
R['side_disagree_own_parse'] = sum(side_of(r['label']) != r['details'][2] for r in D)
R['twin_mapped_label_vs_option'] = Counter((r['mapped_label'] == r['label']) for r in D if r['mapped_label'] is not None)
R['twin_mapped_label_vs_option'] = {str(k): v for k, v in R['twin_mapped_label_vs_option'].items()}

# Toward-hard targets and relation consistency
TH = [r for r in D if r['details'][:2] == ('toward', 'hard')]
rel = Counter((r['fam_tree'], r['details'][2], r['details'][3]) for r in TH)
R['toward_hard_side_relation'] = {'|'.join(k): v for k, v in sorted(rel.items())}
R['toward_hard_identity_failures'] = sum(not (r['details'][2] in ('front', 'back') and
                                             r['details'][3] == {'front': 'front', 'back': 'behind'}[r['details'][2]])
                                         for r in TH if r['details'][2] in ('front', 'back')) + sum(
                                             r['details'][2] not in ('front', 'back') for r in TH)
# Hard rows with other clause labels
R['hard_missing_clause'] = sum(r['details'][0] == 'MISSING' for r in D)

# Weight file equals toward-hard set
W_rows = {}
for kind, cell in weights['cells'].items():
    for x in cell['rows']:
        W_rows[x['qid']] = (kind, x['row_sha256'], x['side'])
target = {r['qid']: (r['fam_tree'], r['digest'], r['details'][2]) for r in TH}
R['weights_rows'] = len(W_rows)
R['weights_equal_toward_hard'] = W_rows == target
R['weights_minus_target'] = len(set(W_rows) - set(target))
R['target_minus_weights'] = len(set(target) - set(W_rows))
R['weights_value_mismatch'] = sum(W_rows[q] != target[q] for q in set(W_rows) & set(target))
side_counts = Counter((k, s) for k, _, s in W_rows.values())
R['weights_side_counts'] = {'|'.join(k): v for k, v in side_counts.items()}
ok = True
for kind, cell in weights['cells'].items():
    mass = side_counts[kind, 'front'] + side_counts[kind, 'back']
    for s in ('front', 'back'):
        ok &= Fraction(cell['weights'][s]) * side_counts[kind, s] == Fraction(mass, 2)
R['weights_mass_half'] = ok
R['twins_in_weights'] = sum(1 for r in TH if r['source'] == 'twins')
(W/'S3_ANALYZE.json').write_text(json.dumps(R, indent=1, default=str) + '\n')
print(json.dumps(R, indent=1, default=str))
