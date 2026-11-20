set +x
cd /scratch/jjyeung
echo "== g3s"; for s in g3s32 g3s64; do ls devs1_r2/anchors/$s | head -3; ls devs1_r2/anchors/$s | wc -l; done
f=$(ls devs1_r2/anchors/g3s64 | head -1); echo "-- $f"; ls -la devs1_r2/anchors/g3s64/$f 2>/dev/null | head -5; head -c 800 devs1_r2/anchors/g3s64/$f 2>/dev/null; echo
echo "== devs1_frames count"; find devs1_frames -type f | wc -l
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import sqlite3, json, os, collections
have = set()
for root in ('/scratch/jjyeung/k1_frames', '/scratch/jjyeung/devs1_frames'):
    for d in os.listdir(root):
        for f in os.listdir(os.path.join(root, d)): have.add(f.split('.')[0])
print('local frame shas', len(have))
c = sqlite3.connect('file:/scratch/jjyeung/orch_n30/fb_pack/point/out/rows_pointing_locate.sqlite?mode=ro', uri=True)
hit = collections.Counter(); tot = collections.Counter(); clips_hit = set()
for i, s in c.execute('select i,row from rows'):
    d = json.loads(s); p = d['pointing']; k = p['kind']; tot[k] += 1
    if p.get('rgb_sha256') in have: hit[k] += 1; clips_hit.add(d['scene'])
print('pointing rows with frame on 2-28', dict(hit), 'of', dict(tot), 'clips', len(clips_hit))
PY
