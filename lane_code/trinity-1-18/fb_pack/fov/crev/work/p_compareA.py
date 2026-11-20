"""Compare arm-A displacement and routed-distance summaries of a score_fov FOV_RESULT with the accepted score_400n output."""
import json, sys
acc = json.load(open('/scratch/jjyeung/orch_n30/sb_own400/out/real400_score_n/SCORE_RESULT.json'))
fov = json.load(open(sys.argv[1]))
ok = True
for metric in ('displacement', 'routed_distance'):
    for name, a, b in [(f['name'], f['A'], g['A']) for f, g in zip(acc[metric]['folds'], fov[metric]['folds'])] + \
                      [('combined', acc[metric]['combined']['A'], fov[metric]['combined']['A'])]:
        same = a == b
        ok &= same
        print(metric, name, 'equal' if same else 'DIFF', a if same else (a, b))
for k in ('captures', 'pairs'):
    print(k, acc[k], fov[k], acc[k] == fov[k]); ok &= acc[k] == fov[k]
print('missing', sorted(m['capture'] for m in acc['missing']) == sorted(m['capture'] for m in fov['missing']))
dacc = json.load(open('/scratch/jjyeung/orch_n30/sb_own400/out/real400_score_n/DISTANCE_ROWS.json'))['rows']
dfov = json.load(open(sys.argv[1].replace('FOV_RESULT', 'DISTANCE_ROWS')))['rows']
ka = {(r['capture'], r['row_id']): (r['pred'], r['gt'], r['refusal']) for r in dacc if r['arm'] == 'A'}
kf = {(r['capture'], r['row_id']): (r['pred'], r['gt'], r['refusal']) for r in dfov if r['arm'] == 'A'}
print('distance rows A', len(ka), len(kf), 'identical', ka == kf); ok &= ka == kf
print('choice', fov.get('choice'), 'synthetic', fov.get('synthetic'), 'decision_usable', fov.get('decision_usable'))
print('ALL_ARM_A_EQUAL' if ok else 'ARM_A_DIFFERS')
