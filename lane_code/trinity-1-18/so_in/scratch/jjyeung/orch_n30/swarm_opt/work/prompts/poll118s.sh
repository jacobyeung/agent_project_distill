#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
bash $P/qrun.sh | grep -v ENDED
S=/scratch/jjyeung/orch_n30/so_step/out/REPORT.md; head -3 $S | cut -c1-300
grep -n -i "coordinator\|gloo\|run_cpu_tests\|outside the sandbox" $S | cut -c1-400 | head -20
ls /scratch/jjyeung/orch_n30/so_step/work/*.sh 2>/dev/null
