Q=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/conf21e/pkg/work/build21/kits/q
grep -n 'bwrap' $Q/b/*.sh $Q/b/*.py $Q/job.sh 2>/dev/null | cut -c1-400 | head -20
grep -n 'q_22c714e1' $Q/b/*.sh $Q/b/*.py $Q/job.sh 2>/dev/null | cut -c1-300 | head
P=/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pwrap; ls $P; grep -rn 'bwrap' $P --include=*.sh | cut -c1-400 | head -8
