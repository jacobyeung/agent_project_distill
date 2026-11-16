G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; PY=/scratch/jjyeung/envs/planner_local_v1/bin/python; date -u
tail -n1 logs/convert_pi3x.log; ls harness/out_pi3x/captures | wc -l
$PY -c "
import json,collections;s=json.load(open('geom/CONVERT_SUMMARY_pi3x.json'));print({a:collections.Counter(v.split(':')[0]+':'+v.split(':')[1][:50] for v in r.values()) for a,r in s['refused'].items()})"
cp -p harness/agg.py k1towers/agg.py; (cd k1towers && $PY -B tests/test_decide.py | tail -2)
if [ $(ls harness/out_pi3x/captures | wc -l) = 296 ]; then
$PY -B k1towers/merge_caps.py harness/out_merged_mdp harness/out_ref/captures harness/out_moge2/captures harness/out_da3/captures harness/out_pi3x/captures
$PY -B k1towers/decide.py harness/out_merged_mdp out/decide_train_mdp.json | head -60
$PY - <<'PY'
import json, glob, numpy as np, collections
v = collections.defaultdict(list)
for p in glob.glob('harness/out_merged_mdp/*.json'):
    d = json.load(open(p))['diagnostics']
    if d['split'] != 'train': continue
    for a, i in d['arms'].items():
        if 'absrel' in i and i['absrel'] is not None:
            v[a].append((i['absrel'], i['absrel_median_aligned'], i['gravity_err_deg'], i.get('scale_to_SO') or np.nan))
for a, x in sorted(v.items()):
    x = np.array(x, float); s = x[:, 3]
    print(a, 'n', len(x), 'absrel med %.3f aligned %.3f grav_err med %.1f' % tuple(np.nanmedian(x[:, :3], 0)), 'scale/SO in[.8,1.2] %.2f' % np.mean((s > .8) & (s < 1.2)) if np.isfinite(s).any() else '')
PY
fi
