K=/scratch/jjyeung/orch_n30/sb_kbox4; K1=/scratch/jjyeung/k1; PY=/scratch/jjyeung/envs/p1cpu/bin/python
echo "=== alias grep kbox4"; grep -nE "alias|dense|raw_name|raw-name|cache_detect|variant" $K/serving_reference.py $K/train_pricing.py $K/reader_src/e2e_reader/stage1.py | cut -c1-260 | head -50
echo "=== cache_detect body"; awk '/def cache_detect/{f=1} f{print; n++} n>40{exit}' $K/serving_reference.py | cut -c1-260
echo "=== stage1 60-130"; sed -n '60,132p' $K/reader_src/e2e_reader/stage1.py | cut -c1-240
V=/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam
echo "=== variantlib alias"; ls $V | head -20; grep -nE "alias|ALIAS|heater|radiator" $V/variantlib.py $V/variant_cache.py 2>/dev/null | cut -c1-260 | head -40
nice -n 10 $PY - <<'PYEOF'
import json,glob,collections
fs=sorted(glob.glob('/scratch/jjyeung/k1/run_tower_sam_2/*/candidates.json'))
d=json.load(open(fs[0]))
print('top keys',list(d.keys()))
for k in d:
    if k not in('frames','frame_indices','phrases','contract'): print('  ',k,json.dumps(d[k])[:800])
fr=d['frames']['0']['phrases'];ph=list(fr.keys());print('frame0 phrases',ph[:20])
p=fr[ph[0]];print('phrase keys',list(p.keys()))
ins=p.get('instances',[]);print('n inst',len(ins))
if ins: print('inst keys',list(ins[0].keys()),{k:(v if k!='mask' else '...') for k,v in ins[0].items()})
src=collections.Counter()
for f in d['frames'].values():
    for name,p in f['phrases'].items():
        for i in p.get('instances',[]):
            src[(name,i.get('source') or i.get('prompt') or i.get('phrase') or i.get('alias'))]+=1
print('sources',src.most_common(20))
PYEOF
