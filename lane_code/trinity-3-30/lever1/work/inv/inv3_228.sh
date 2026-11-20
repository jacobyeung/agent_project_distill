cd /scratch/jjyeung/orch_n30
cat cont_ops25_c/r7_run.sh; echo "##"; ls cont_ops24_c/cap | head -50; ls cont_ops24_c/cap/score_t1 | head; echo "##gbuild"; ls cont_ops24_c/gbuild | sed -n 60,200p | tr '\n' ' '
echo "##gt"; ls cont_ops24_c/gt/t1_gt/gt | head -3; ls cont_ops24_c/gt/arkit_gt/gt | head -3; ls cont_ops24_c/gt/arkit_gt/gt | wc -l
echo "##codex"; ls /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs | tail -5; pgrep -af codex | grep -v pgrep | cut -c1-150 | head
