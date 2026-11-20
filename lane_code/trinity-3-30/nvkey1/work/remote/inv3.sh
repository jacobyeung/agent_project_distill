set +x
cd /scratch/jjyeung
echo "== devs1_r2"; head -c 1500 devs1_r2/REQUEST.json; echo; ls devs1_r2/anchors | head -5; ls devs1_r2/anchors | wc -l
echo "== grd_funnel1 REPORT/STATUS"; head -c 3000 orch_n30/grd_funnel1/STATUS.md; echo; head -c 2500 orch_n30/grd_funnel1/REPORT.md; echo
echo "== grd INPUTS"; head -c 2500 orch_n30/grd_funnel1/kit/INPUTS_REQUIRED.json; echo
echo "== sqlite"
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import sqlite3, json, collections
c = sqlite3.connect('file:/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite?mode=ro', uri=True)
rows = c.execute('select i,row,target from rows').fetchall()
r0 = json.loads(rows[0][1]); print(json.dumps(r0)[:2500]); print('target0', rows[0][2][:300])
vis = [r for r in rows if '"gt_absent"' not in r[1]][:1]
if vis: print('VIS', json.dumps(json.loads(vis[0][1]))[:2500]); print('target', vis[0][2][:300])
kinds = collections.Counter(); ds = collections.Counter(); af = collections.Counter(); scenes = set()
for i, s, t in rows:
    d = json.loads(s); p = d.get('pointing', {}); kinds[p.get('kind')] += 1; ds[d.get('dataset')] += 1
    a = p.get('area_fraction') or 0; af['0' if a == 0 else '<0.002' if a < 0.002 else '<0.01' if a < 0.01 else '<0.05' if a < 0.05 else '>=0.05'] += 1
    scenes.add((d.get('dataset'), (p.get('mask') or {}).get('path', '').split('/')[-2]))
print('kinds', dict(kinds)); print('datasets', dict(ds)); print('area', dict(af)); print('clips', len(scenes))
PY
