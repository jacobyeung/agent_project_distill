W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; wc -c $W/work/rev19_dispatch.log; tail -c 3000 $W/work/rev19_dispatch.log
R=/home/jjyeung/agent_project_distill/agent/scratch/codex_runs; ls -dt $R/*rev19* | head -3
d=$(ls -dt $R/*rev19* | head -1); ls -la $d; for f in $d/*; do echo "== $f"; tail -c 6000 $f; done 2>/dev/null | head -c 20000
