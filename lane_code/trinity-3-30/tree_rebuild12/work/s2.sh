W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; R=$W/w21/out/BUILD21_REPORT.md; B=$W/w21/work/build21
tail -3 $W/work/build21b_dispatch.log; echo ---HEAD; grep -n '^#' $R | head -60; wc -l $R; awk 'length>2000{c++} END{print c" long lines"}' $R
echo ---DELIVERY; head -c 2500 $B/DELIVERY.json; echo; echo ---FC; head -c 2500 $B/FINAL_CHECKS.json; echo; echo ---CF; cat $W/work/conf21/cf21.log
