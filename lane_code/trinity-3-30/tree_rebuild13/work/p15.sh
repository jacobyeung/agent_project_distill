W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; Q=$W/w23/work/build21/kits/q
grep -n "g\.py\|E42" $Q/job.sh $Q/b/* 2>/dev/null | grep -v "^Binary" | head -10 | cut -c1-300
grep -rn "total_memory\|E42" --include=*.py --include=*.sh $W/w23/work/build21/*.py $W/w23/work/build21/kits/q 2>/dev/null | head -10 | cut -c1-250
grep -rn "total_memory\|get_device_properties\|nvidia" $W/ext/pwrap/b/c.sh 2>/dev/null | head -10 | cut -c1-250
grep -rln "E42" $W/w23/work/build21/*.py $W/w23/work/build23*/ 2>/dev/null | head
