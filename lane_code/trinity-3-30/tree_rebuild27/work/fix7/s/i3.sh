W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
ls -la $W/w24z11b/out/ | grep -iv "BUILD24M4[A-Y]" | tail -40
echo ==== arm_launch.sh; wc -l $W/w24z11b/out/arm_launch.sh; head -150 $W/w24z11b/out/arm_launch.sh
echo ==== w27fix; ls -la $W/w27fix $W/w27fix/work | head -50
echo ==== w28fix; ls -la $W/w28fix/work $W/w28fix/src | head -60
for f in $W/w28fix/*.md $W/w28fix/work/*.md $W/w27fix/*.md $W/w27fix/work/*.md; do [ -f $f ] && echo "== $f $(wc -c <$f)"; done
