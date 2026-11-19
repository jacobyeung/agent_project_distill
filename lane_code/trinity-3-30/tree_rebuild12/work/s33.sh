P=/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pwrap; sed -n '336,380p' $P/b/c.sh | cut -c1-300
Q=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/conf21e/pkg/work/build21/kits/q; grep -n 'tk_bwrap\|NS=\|namespace\|/tmp/q_' $Q/b/*.sh $Q/b/z.py | cut -c1-300 | head -20
