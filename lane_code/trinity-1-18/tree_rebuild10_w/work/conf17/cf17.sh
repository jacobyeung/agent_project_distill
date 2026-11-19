#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf17; PKG=tree_rebuild_b17_846ead7a.tar
P="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
mkdir -p $C/pkg $C/tmp; cd $C; echo "start $(date -u +%T)"
sha256sum $W/w17b/out/$PKG > pkg_sha.txt; stat -c %s $W/w17b/out/$PKG >> pkg_sha.txt; cat $W/w17b/work/build17/DELIVERY.json > delivery.json 2>/dev/null
(cd pkg && tar xf $W/w17b/out/$PKG)
for d in $W/w17b/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); done > seal.txt 2>&1
grep -l "tree_rebuild10_w/w17b" pkg/work/build17/*.py pkg/work/build17/run.sh 2>/dev/null > hardcoded.txt
cd $C/pkg
echo "== integrity $(date -u +%T)"; timeout 1800 bash work/build17/run.sh work/build17/integrity17.py > $C/integrity.log 2>&1; echo "rc=$?"
for t in final_focused/TESTS.json export/TESTS.json mutations/RESULT.json rooms/RESULT.json real/RESULT.json; do echo "== $t"; python3 -c "
import json,sys;d=json.load(open('$C/pkg/work/build17/proofs/$t'))
def summ(d):
  if isinstance(d,dict):
    ks=[k for k in d if any(x in k.lower() for x in ('pass','fail','error','ran','total','caught','count','summary','v7','result','status'))]
    return {k:(d[k] if not isinstance(d[k],(dict,list)) or len(json.dumps(d[k]))<400 else str(d[k])[:400]) for k in ks}
  return str(d)[:400]
print(json.dumps(summ(d))[:1500])"; done
# K1 list vs full-authority check
cd $C && $P - <<'PY' > k1cmp.txt 2>&1
import json
s=[json.loads(l) for l in open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w17b/work/build17/inputs/s.json')]
keys={x['row_key'] for x in s}; print('s.json rows',len(s),'reasons',sorted({x['reason'] for x in s}))
k=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/k1check/K1R0_CHECK.json'))
for fam,v in k['slices'].items():
    h=set(q for qs in v['hit_qids'].values() for q in qs)
    print(fam,'full-authority hits',len(h),'in s.json',len(h&keys),'missing',sorted(h-keys)[:5])
print('s.json keys not in full-authority hits',len(keys-set(q for v in k['slices'].values() for qs in v['hit_qids'].values() for q in qs)))
PY
cat k1cmp.txt
# traces: automated scan + compact copy
echo DONE $(date -u +%T)
python3 -c "
import json;d=json.load(open('$C/pkg/work/build17/proofs/rooms/RESULT.json'))
def find(o,path=''):
  if isinstance(o,dict):
    for k,v in o.items():
      if 'v7' in k.lower() or 'store' in k.lower(): print(path+'/'+k, json.dumps(v)[:1500])
      elif isinstance(v,dict): find(v,path+'/'+k)
find(d)" > $C/v7_k1.txt 2>&1
echo DONE2 $(date -u +%T)
