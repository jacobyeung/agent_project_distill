R=/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs; C=/scratch/jjyeung/orch_n30/lever1_c
tmux ls | grep l1_; tail -1 $C/r2e_run.log
echo "=====R1REV2"; cat $R/20261120T192520Z_lever1_r1rev2/final_message.md
echo "=====R5"; cat $R/20261120T192520Z_lever1_r5/final_message.md; echo "=====R5REPORT"; cat $C/nogt/out/NOGT_REPORT.md; cat $C/nogt/out/REPRO_INPUTS_REQUIRED.json | head -c 3000
echo "=====R2E"; cat $R/*lever1_r2e/final_message.md 2>/dev/null
