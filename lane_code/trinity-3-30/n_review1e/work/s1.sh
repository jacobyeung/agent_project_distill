W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; N=/scratch/jjyeung/orch_n30/n_review
date -u +%TZ; hostname -s; df -h /scratch | tail -1
ls -la $N $N/r1b $N/r1d | head -60
du -sh $N/r1b/tc/work/tree_r1 2>/dev/null
ls -la $W/w24k/out $W/w24l/out $W/w24m/out 2>&1 | head -60
ls -la /scratch/jjyeung/orch_n30/tr19_revC1 /scratch/jjyeung/orch_n30/tr19_revC1/work 2>&1 | head -40
sha256sum $W/w24k/out/TREE_CHANGE_24M4K.patch /scratch/jjyeung/orch_n30/tr19_revC1/work/TEST_HOST24J_FIX.patch
wc -l $W/w24k/out/TREE_CHANGE_24M4K.patch /scratch/jjyeung/orch_n30/tr19_revC1/work/TEST_HOST24J_FIX.patch
echo "@@@ PATCH"; cat $W/w24k/out/TREE_CHANGE_24M4K.patch | head -c 60000
echo "@@@ TESTFIX"; cat /scratch/jjyeung/orch_n30/tr19_revC1/work/TEST_HOST24J_FIX.patch
