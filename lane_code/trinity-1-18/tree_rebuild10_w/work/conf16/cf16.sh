#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf16; PKG=tree_rebuild_b16_04e21e92.tar
P="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
mkdir -p $C/pkg $C/tmp; cd $C; echo "start $(date -u +%T)"
sha256sum $W/w16b/out/$PKG > pkg_sha.txt; stat -c %s $W/w16b/out/$PKG >> pkg_sha.txt; cat $W/w16b/work/build16/DELIVERY.json > delivery.json 2>/dev/null
(cd pkg && tar xf $W/w16b/out/$PKG)
for d in $W/w16b/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); done > seal.txt 2>&1
grep -l "tree_rebuild10_w/w16b" pkg/work/build16/*.py pkg/work/build16/run.sh 2>/dev/null > hardcoded.txt
cd $C/pkg
echo "== focused $(date -u +%T)"; B16_PROOF=final_focused timeout 3000 bash work/build16/run.sh work/build16/test16.py tests.test_r1_build16 tests.test_r1_build15 tests.test_r1_build14 tests.test_r2_build_n1 tests.test_r2_n1fix tests.test_r2_n1fix3 tests.test_r2_build12 tests.test_r1_build13 tests.test_r2_build3.Build3.test_opener_export_keep_and_reset > $C/focused.log 2>&1; echo "rc=$?"
echo "== edges $(date -u +%T)"; B16_PROOF=edges timeout 1800 bash work/build16/run.sh work/build16/test16.py edge_test16.Edges stage_test16.Staging > $C/edges.log 2>&1; echo "rc=$?"
for s in real16 float16 mutations16; do echo "== $s $(date -u +%T)"; timeout 3000 bash work/build16/run.sh work/build16/$s.py > $C/$s.log 2>&1; echo "rc=$?"; done
# K1 list vs full-authority check
cd $C && $P - <<'PY' > k1cmp.txt 2>&1
import json
s=[json.loads(l) for l in open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16b/work/build16/inputs/s.json')]
keys={x['row_key'] for x in s}; print('s.json rows',len(s),'reasons',sorted({x['reason'] for x in s}))
k=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/k1check/K1R0_CHECK.json'))
for fam,v in k['slices'].items():
    h=set(q for qs in v['hit_qids'].values() for q in qs)
    print(fam,'full-authority hits',len(h),'in s.json',len(h&keys),'missing',sorted(h-keys)[:5])
print('s.json keys not in full-authority hits',len(keys-set(q for v in k['slices'].values() for qs in v['hit_qids'].values() for q in qs)))
PY
cat k1cmp.txt
# traces: automated scan + compact copy
ls $W/w16b/work/build16/proofs/traces | head -40; du -sh $W/w16b/work/build16/proofs/traces
echo DONE $(date -u +%T)
