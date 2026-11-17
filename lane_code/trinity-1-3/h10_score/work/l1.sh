cd /scratch/jjyeung/orch_n30/h10_stage || exit 1
ls -la; ls -la inbox work work/proof work/o work/results 2>&1 | head -80
du -sh work/proof work/o work/results inbox 2>&1
tail -5 work/o/q3.hist 2>&1
tmux ls 2>&1
