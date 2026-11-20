echo "== $(hostname -s) $(date -u +%T)"
W=/scratch/jjyeung/orch_n30
ls -la $W/sb_alias2/out $W/sb_alias2/work 2>&1 | head -40
sed -n 1,56p $W/sb_alias2/out/ROOM_AUDIT_REPORT.md | cut -c1-700
cat $W/sb_k1list/out/U2_REPORT.md | cut -c1-600
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json, os, hashlib
W = '/scratch/jjyeung/orch_n30'
man = json.load(open(W + '/geo_k1/stage/K1_MANIFEST.arkit_timing.json'))
RAST = [W + '/gt_build/out/dose_pool/out/t1_gt/gt', W + '/gt_build/out/dose_pool/out/arkit_gt/gt', W + '/gt_build2/out/dose_pool/out/arkit_gt/gt']
lst = []; bad = 0; tot = 0; idx = {}
for c in man['captures']:
    if not (c.get('k1_split') == 'train' and c.get('split') == 'train'): continue
    name = os.path.basename(c['gt']['path']); ps = [d + '/' + name for d in RAST if os.path.isfile(d + '/' + name)]
    if not ps: print('MISSING', c['canonical']); continue
    h = hashlib.sha256(open(ps[0], 'rb').read()).hexdigest()
    if h != c['gt']['sha256']: bad += 1; print('SHA MISMATCH', c['canonical'], ps[0]); continue
    rel = os.path.relpath(ps[0], W); lst.append(rel); tot += os.path.getsize(ps[0]); idx[c['canonical']] = dict(rel=rel, sha256=h)
open('/scratch/jjyeung/orch_n30/nvkey1/k1r_files.txt', 'w').write('\n'.join(lst + ['geo_k1/stage/K1_MANIFEST.arkit_timing.json']) + '\n')
json.dump(idx, open('/scratch/jjyeung/orch_n30/nvkey1/k1r_index.json', 'w'))
print('train rasters', len(lst), 'sha ok', len(lst), 'bad', bad, 'bytes', tot)
PY
cp /scratch/jjyeung/orch_n30/nvkey1/k1r_index.json /scratch/jjyeung/orch_n30/geo_k1/stage/ 2>/dev/null; 
cd $W && tar cf - -T /scratch/jjyeung/orch_n30/nvkey1/k1r_files.txt -C /scratch/jjyeung/orch_n30/nvkey1 k1r_index.json | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/nvkey1/work/k1r && tar xf - -C /scratch/jjyeung/orch_n30/nvkey1/work/k1r && du -sh /scratch/jjyeung/orch_n30/nvkey1/work/k1r && date -u +%T'
echo "tar rc ${PIPESTATUS[*]}"
