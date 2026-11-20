J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24y2; K=$J/out/kit_n_go; date -u +%TZ; ls -l $J/out/tree_rebuild_b24m4y2_*
ls $K $K/b $K/k | tr '\n' ' '; echo; wc -l $K/job.sh $K/b/*.py $K/b/*.sh 2>/dev/null | tail -40
echo ===JOB; cat $K/job.sh | cut -c1-250
