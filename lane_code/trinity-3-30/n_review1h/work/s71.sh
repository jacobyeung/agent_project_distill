W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Z=$W/w24z12; A=$W/w24z11b/out
date -u +%TZ
echo "== arm_routing diff 1a4b900b -> 3dbd7af2"; diff -u $W/w24y2/out/arm_routing.py $A/arm_routing.py < /dev/null
echo "== w24z12 arm_routing"; sha256sum $Z/out/arm_routing.py < /dev/null
echo "== arm_launch.sh"; cat $A/arm_launch.sh < /dev/null
echo "== ARM_LAUNCH_24M4Z11B.md"; cat $A/ARM_LAUNCH_24M4Z11B.md < /dev/null | head -120
echo "== jn3.sh"; cat $Z/out/jn3.sh < /dev/null
echo "== ENOSPC_24M4Z12.md"; cat $Z/out/ENOSPC_24M4Z12.md < /dev/null | head -150
echo "== BUILD24M4Z12_REPORT.md"; cat $Z/out/BUILD24M4Z12_REPORT.md < /dev/null | head -120
