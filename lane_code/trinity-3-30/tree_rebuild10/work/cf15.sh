#!/bin/bash
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf15; PKG=tree_rebuild_b15_67f8baf1.tar
P="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
mkdir -p $C/pkg $C/tmp; cd $C
echo "start $(date -u +%T)"
sha256sum $W/w15/out/$PKG > pkg_sha.txt; stat -c %s $W/w15/out/$PKG >> pkg_sha.txt
(cd pkg && tar xf $W/w15/out/$PKG)
for d in $W/w15/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))") ; done > seal.txt 2>&1
grep -l "tree_rebuild10_w/w15" pkg/work/build15/*.py pkg/work/build15/run.sh 2>/dev/null > hardcoded.txt
for f in $(cat hardcoded.txt); do sed -i "s#/scratch/jjyeung/orch_n30/tree_rebuild10_w/w15#$C/pkg#g; s#/scratch/jjyeung/orch_n30/tree_rebuild_w/w15#$C/pkg#g" $f; done
cd $C/pkg
for s in real15 opener15 witness_edges15; do echo "== $s $(date -u +%T)"; timeout 2400 bash work/build15/run.sh work/build15/$s.py > $C/$s.log 2>&1; echo "rc=$?"; done
echo "== focused $(date -u +%T)"; B15_PROOF=final_focused timeout 3000 bash work/build15/run.sh work/build15/test15.py tests.test_r1_build15 tests.test_r1_build14 tests.test_r2_build_n1 tests.test_r2_n1fix tests.test_r2_n1fix3 tests.test_r2_build12 tests.test_r1_build13 tests.test_r2_build3.Build3.test_opener_export_keep_and_reset > $C/focused.log 2>&1; echo "rc=$?"
# refute scripts of builds 12/13 (lane copies), repointed conf13 -> conf15
cd $C; cp -r $W/work/conf13/s $W/work/conf13/t11 . ; sed -i "s#work/conf13#work/conf15#g" s/*.py t11/*/*.py
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TMPDIR=$C/tmp; ulimit -f 204800
for s in n1r n1c t4; do echo "== $s $(date -u +%T)"; timeout 1500 $P s/$s.py > $s.log 2>&1; echo rc=$?; done
(cd t11/m1 && timeout 600 $P load_b11.py $C/t11/m1 tamper_b13 > load.log 2>&1; echo "load rc=$?"; timeout 600 $P m1b.py > m1b.log 2>&1; echo "m1b rc=$?")
(cd t11/l2 && timeout 600 $P probe_int.py > probe.log 2>&1; echo "l2 rc=$?")
# packet float check: same single test on b14 package in this node's env
grep -rln "test_production_generator_on_off" $C/pkg/work $C/pkg/fixtures 2>/dev/null | head -5 > float_test_files.txt
echo DONE $(date -u +%T)
