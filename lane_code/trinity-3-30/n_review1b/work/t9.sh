X=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24l3_back/out
wc -c $X/*.patch $X/*.md $X/ROUTING_DIGEST_STABILITY.json
cat $X/ROUTING_DIGEST_STABILITY.json | head -c 3000; echo
cat $X/PIN_COMPARISONS_24N.md | head -c 14000
