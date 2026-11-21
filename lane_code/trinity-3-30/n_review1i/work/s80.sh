W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; D=$W/work/d173881/173881
date -u +%TZ; df -h /scratch < /dev/null | tail -1
ls -la $D < /dev/null | head -80
for s in live p p/q p/q/b; do echo "== $s"; ls -la $D/$s < /dev/null 2>&1 | head -40; done
ls $W/work < /dev/null | tr '\n' ' '; echo
ls -la $W/w24z14/out < /dev/null | head -30
ls $W < /dev/null | tr '\n' ' '; echo
ls -la $W/w24z13b/out $W/w24z15/out < /dev/null 2>&1 | grep -v 'BUILD24M[0-3]\|UPLOADS_\|DELIVERY_' | head -60
