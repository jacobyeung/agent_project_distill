Q=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/work/build21/kits/q; cd $Q
grep -n "def bootstrap" -A60 b/z.py | grep -n "g.py\|print\|result\|return\|run(\|call(\|json\|copy\|out" | cut -c1-260 | head -40
