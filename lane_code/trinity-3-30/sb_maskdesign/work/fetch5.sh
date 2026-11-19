D=/scratch/jjyeung/orch_n30/sb_maskfail; K=/scratch/jjyeung/orch_n30/sb_kbox4; PY=/scratch/jjyeung/envs/p1cpu/bin/python
echo "=== MASKFAIL_REPORT"; cat $D/out/MASKFAIL_REPORT.md | cut -c1-1200; echo "=== tar"; ls -la $D/out/sb_maskfail.tar; cat $D/out/sb_maskfail.tar.sha256
echo "=== gt path resolution"; grep -nE "gt_arrays|def gt|rasters|GT_ROOT|k1_gt|\.npz|run_tower_sam|SEL *=|ROWSETS *=|k1_frames|FRAMES" $K/serving_reference.py | cut -c1-240 | head -40
echo "=== tower preflight"; head -c 2500 /scratch/jjyeung/k1/run_tower_sam_2.preflight.json; echo
echo "=== tower dir sample"; d=$(ls /scratch/jjyeung/k1/run_tower_sam_2 | head -1); ls -la /scratch/jjyeung/k1/run_tower_sam_2/$d | head -20
nice -n 10 $PY - <<'PYEOF'
import numpy as np,glob,json,os
d=sorted(glob.glob('/scratch/jjyeung/k1/run_tower_sam_2/*/tower.npz'))
print('tower.npz count',len(d))
z=np.load(d[0],allow_pickle=True)
for k in z.files[:40]:
    try: a=z[k];print('  ',k,getattr(a,'shape',None),getattr(a,'dtype',None))
    except Exception as e: print('  ',k,'ERR',e)
p=json.load(open('/scratch/jjyeung/orch_n30/sb_kbox4/pinned_train.json'))
c=p['captures'][0]
from PIL import Image
im=Image.open(c['dense_frames'][0]['path']);print('frame size',im.size,'n dense frames',len(c['dense_frames']),'exists all 64',sum(os.path.exists(f['path']) for f in c['dense_frames']))
print('gt entry',c['gt'])
import collections
ex=collections.Counter()
for c in p['captures']:
    ex[(c['canonical'].split('/')[0],os.path.exists(c['gt']['path']))]+=1
print('gt path exists by dataset',dict(ex))
print('counts',p.get('counts'))
PYEOF
echo "=== raster stores"; ls -d /scratch/jjyeung/n30_mirror/*gt* /scratch/jjyeung/n30_mirror/*raster* /scratch/jjyeung/orch_n30/*gt* /scratch/jjyeung/orch_n30/*raster* /scratch/jjyeung/*raster* /scratch/jjyeung/*gt* 2>/dev/null | head -40
echo "=== kobj"; ls -d /scratch/jjyeung/orch_n30/sb_kobj* /scratch/jjyeung/orch_n30/sb_ktow* /scratch/jjyeung/orch_n30/sb_selrefit* 2>/dev/null; for d in /scratch/jjyeung/orch_n30/sb_kobj4; do [ -f $d/STATUS.md ] && head -c 1500 $d/STATUS.md; done
echo "=== sam3 env"; ls /scratch/jjyeung/trinity_qwen_sam3 | head -20; ls /scratch/jjyeung/envs/sam3_capretry_native_v1/bin 2>/dev/null | grep -E "^python" | head -3; ls -la /scratch/jjyeung/k1/src 2>/dev/null | head -20
echo "=== FRAME RECALL fix"
cat > /tmp/sb_maskdesign_fr.py <<'PYEOF'
import json,collections,numpy as np
recs=json.load(open('/scratch/jjyeung/orch_n30/sb_maskfail/out/MASKFAIL.json'))['records']
vis=[r for r in recs if r['visible'] and r['valid'] and r['share']>=.001]
print('visible frames with share>=0.1pct',len(vis),'served IoU>=.3 rate %.3f'%np.mean([(r['iou'] or 0)>=.3 for r in vis]),'pool IoU>=.3 rate %.3f'%np.mean([max(r['iou'] or 0,r['deployed_best_iou'])>=.3 for r in vis]),'served>=.5 %.3f pool>=.5 %.3f'%(np.mean([(r['iou'] or 0)>=.5 for r in vis]),np.mean([max(r['iou'] or 0,r['deployed_best_iou'])>=.5 for r in vis])))
big=[r for r in vis if r['share']>=.01];print('share>=1pct n',len(big),'served>=.5 %.3f pool>=.5 %.3f'%(np.mean([(r['iou'] or 0)>=.5 for r in big]),np.mean([max(r['iou'] or 0,r['deployed_best_iou'])>=.5 for r in big])))
PYEOF
nice -n 10 $PY /tmp/sb_maskdesign_fr.py 2>&1 | tail -5
