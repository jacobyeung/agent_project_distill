W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf21/pkg; R=$W/work/conf21/r3
date -u +%TZ; cat $R/ff3_rc 2>/dev/null; for f in $R/ff3_*.log; do echo $f; tail -3 $f; done
cd $C && du -sh --exclude=. work/tree_r1 work/build21 2>/dev/null; du -s work/build21/* 2>/dev/null | sort -rn | head -8; find work/tree_r1 -size +2M | head
