K=/scratch/jjyeung/orch_n30/sb_kbox4; PY=/scratch/jjyeung/envs/p1cpu/bin/python
echo "=== adapters"; sed -n '1,30p' $K/adapters.py | cut -c1-240
TREE=$(grep -oE "TREE *= *Path\('[^']+'\)" $K/adapters.py | grep -oE "'[^']+'" | tr -d "'"); echo "TREE=$TREE"
RF=$(ls $TREE/student_pilot/routed_features.py 2>/dev/null); echo "RF=$RF"
[ -n "$RF" ] && { echo "=== cache_for"; awk '/^def cache_for/{f=1} f{print; n++} n>30{exit}' $RF | cut -c1-240; echo "=== presence uses"; grep -n "presence" $RF | cut -c1-220 | head -30; }
echo "=== selector_inputs presence"; grep -rn "presence" /scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/sl118/selector_inputs.py 2>/dev/null | cut -c1-220 | head -12
echo "=== sam3 ckpt dirs"; for d in /scratch/jjyeung/n13_outage/sam3_ckpt /scratch/jjyeung/qwen_port_1110/sam3_ckpt /scratch/jjyeung/split_efficiency/sam3 /scratch/jjyeung/orch_cd/sam3_tower; do echo "-- $d"; ls -la $d 2>&1 | head -12; done
echo "=== sam3 package"; SP=$(ls -d /scratch/jjyeung/envs/sam3_capretry_native_v1/lib/python3*/site-packages); ls $SP | grep -i -E "^sam|torch$|^torch-" | head; for p in $SP/sam3 $SP/sam3.egg-link $SP/__editable__*sam3*; do [ -e "$p" ] && { echo "-- $p"; ls $p 2>/dev/null | head -40; cat $p 2>/dev/null | head -5; }; done
find $SP/sam3 -maxdepth 2 -iname "*video*" 2>/dev/null | head -12; find $SP/sam3 -maxdepth 2 -iname "*train*" -o -maxdepth 2 -iname "*loss*" 2>/dev/null | head -12
echo "=== dense frames exist"
nice -n 10 $PY - <<'PYEOF'
import json,os,collections
p=json.load(open('/scratch/jjyeung/orch_n30/sb_kbox4/pinned_train.json'))
ids=set(open('/scratch/jjyeung/n30_mirror/sb_headacc2/K1_ROWSETS/K1_TRAIN_1037.txt').read().split())
n=collections.Counter();gaps=[]
for c in p['captures']:
    ex=sum(os.path.exists(f['path']) for f in c['dense_frames']);n[(len(c['dense_frames']),ex,any(r['id'] in ids for r in c['rows']))]+=1
    a=c['anchor_indices'];gaps.append((c['canonical'].split('/')[0],(a[-1]-a[0])/31))
print('captures by (dense frames listed, files present, has priced rows):',dict(n))
import numpy as np
for ds in ['arkitscenes','scannet','scannetpp']:
    g=[x for d,x in gaps if d==ds];print(ds,'median native-frame gap between anchors %.1f (min %.1f max %.1f)'%(np.median(g),min(g),max(g)))
print('sample frame keys',list(p['captures'][0]['dense_frames'][0].keys()))
PYEOF
