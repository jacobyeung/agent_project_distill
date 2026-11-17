"""Summarise the second reader over all K1 distance rows with rasters (SECOND_READER_ALL2.json) plus the GT-arm ratio check."""
import collections, glob, json
import numpy as np

W = '/scratch/jjyeung/orch_n30/tower_redecide/work'
S = json.load(open(W + '/second_reader/SECOND_READER_ALL2.json'))
LAB = {json.loads(l)['id']: json.loads(l) for l in open('/scratch/jjyeung/orch_n30/gt_audit/out/audit/k1/K1_LABELS_CORRECTED.jsonl')}
rows = S['rows']
out = dict(n_rows=len(rows), x1_reproduces_stored=sum(r['x1_reproduces_stored'] for r in rows),
           label_agrees=sum(r['agree'] for r in rows), box_conflicts=sum(not all(r['box_level_agree']) for r in rows))
box = {}
for r in rows:
    for k, (mine, ga) in enumerate(zip(r['my_box_verdicts'], r['ga_box_statuses'])):
        box[(r['capture'], r['operands'][k])] = (mine, ga, LAB[r['id']]['dataset'])
ct = collections.Counter((d, ga, mine) for mine, ga, d in box.values())
out['box_crosstab_dataset_ga_mine'] = {f'{d}|ga={ga}|mine={m}': n for (d, ga, m), n in sorted(ct.items())}
gtv = {}
for f in glob.glob(W + '/reprice/caps_corrected/*.json'):
    for it in json.load(open(f))['items']:
        if it['type'] == 'object_abs_distance' and it['arm'] == 'GT':
            gtv[it['row_id']] = it['pred']
unc = collections.Counter(); flagged = []
for r in rows:
    l = LAB[r['id']]
    both_unknown = any(m == 'unknown' and g == 'unknown' for m, g in zip(r['my_box_verdicts'], r['ga_box_statuses']))
    if l['convention'] == 'half' and both_unknown:
        unc[(r['split'], l['dataset'])] += 1
    p = gtv.get(r['id'])
    if l['convention'] == 'half' and p and p / l['corrected'] > 1.6:
        flagged.append(dict(id=r['id'], split=r['split'], capture=r['capture'], ratio=round(p / l['corrected'], 2), mine=r['my_box_verdicts'], ga=r['ga_box_statuses']))
out['half_rows_with_a_box_undecided_by_both_readers'] = {f'{s}|{d}': n for (s, d), n in sorted(unc.items())}
out['half_rows_gt_arm_over_corrected_gt_1p6'] = flagged
sc = collections.defaultdict(collections.Counter)
for p, s in S['scenes'].items():
    sc[s['canonical'].split('/')[0]][s['scene_convention']] += 1
out['scene_conventions_mine'] = {d: dict(c) for d, c in sc.items()}
out['scannetpp_scene_median_r'] = [round(float(np.percentile([s['median_r'] for s in S['scenes'].values() if s['canonical'].startswith('scannetpp/') and s['median_r']], q)), 3) for q in (0, 5, 50, 95, 100)]
out['scannet_half_scenes_mine'] = sorted(s['canonical'] for s in S['scenes'].values() if s['canonical'].startswith('scannet/') and s['scene_convention'] != 'full')
json.dump(out, open(W + '/second_reader/SECOND_READER_SUMMARY.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
