echo "== $(hostname -s) $(date -u +%T)"; df -h /scratch | tail -1
W=/scratch/jjyeung/orch_n30
ls $W/sb_alias2/out | head -30
grep -n -i -E 'sha256|\.json|list|path' $W/sb_alias2/out/ROOM_AUDIT_REPORT.md | cut -c1-300 | head -40
echo "-- sb_k1list"; ls -la $W/sb_k1list/out | head -20
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json, os, collections
W = '/scratch/jjyeung/orch_n30'
man = json.load(open(W + '/geo_k1/stage/K1_MANIFEST.arkit_timing.json'))
RAST = [W + '/gt_build/out/dose_pool/out/t1_gt/gt', W + '/gt_build/out/dose_pool/out/arkit_gt/gt', W + '/gt_build2/out/dose_pool/out/arkit_gt/gt']
print('manifest keys', list(man)[:10], 'captures', len(man['captures']))
c0 = man['captures'][0]; print('capture keys', sorted(c0)[:40]); print('gt', c0.get('gt'))
st = collections.Counter(); tot = 0; tot_train = 0; found = {}
for c in man['captures']:
    name = os.path.basename(c['gt']['path'])
    ps = [d + '/' + name for d in RAST if os.path.isfile(d + '/' + name)]
    st['found %d' % len(ps)] += 1
    st['split %s/%s' % (c.get('k1_split'), c.get('split'))] += 1
    if ps:
        b = os.path.getsize(ps[0]); tot += b
        if c.get('k1_split') == 'train' and c.get('split') == 'train': tot_train += b
    if c['gt'].get('bytes'): st['gt.bytes given'] += 1
print(dict(st)); print('bytes all', tot, 'train', tot_train)
print('gt fields', {k: c0['gt'][k] for k in c0['gt'] if k != 'path'})
PY
