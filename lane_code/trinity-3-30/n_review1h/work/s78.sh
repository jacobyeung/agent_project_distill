W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
date -u +%TZ
echo "== QD_STEP1.md"; cat $W/w24z12/out/QD_STEP1.md < /dev/null | head -80
echo "== ADMIT_TEST_USAGE.md"; cat $W/w24z14/out/ADMIT_TEST_USAGE.md < /dev/null | head -80
echo "== admit_test.sh"; cat $W/w24z14/out/admit_test.sh < /dev/null
echo "== admit_test.py"; wc -l $W/w24z14/out/admit_test.py < /dev/null; sha256sum $W/w24z14/out/admit_test.py $W/w24z14/out/admit_test.sh < /dev/null; cat $W/w24z14/out/admit_test.py < /dev/null | head -150
echo "== z15"; ls $W/w24z15 $W/w24z15/out $W/w24z13b/out < /dev/null 2>&1 | grep -v 'BUILD24M[0-3]\|BUILD24M4[A-Y]\|UPLOADS_\|DELIVERY_' | head -60
