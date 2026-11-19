W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; F=$W/work/conf21/ff2_focused.log
for n in 683 809 956; do sed -n "$((n)),$((n+21))p" $F | cut -c1-260; echo ----; done
awk '/^ERROR: /{e=1} e&&/^[A-Za-z]+Error/{print; e=0}' $F | sort | uniq -c | sort -rn | cut -c1-300 | head
for f in ff2_edges.log ff2_pedges.log; do tail -c 700 $W/work/conf21/$f; echo; done
