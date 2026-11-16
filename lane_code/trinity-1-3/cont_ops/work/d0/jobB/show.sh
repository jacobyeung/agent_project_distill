f=/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/p5_last.txt
date -u +%T; sed -n 1,3p $f; sed -n '/== A2/,/== B w.steps/p' $f | tail -4; sed -n '/== B w.steps/,/== B steps/p' $f | tail -3; sed -n '/== B steps/,/== B err/p' $f | tail -4; sed -n '/== B err/,/== B o/p' $f; sed -n '/== B runs/,$p' $f | tail -4
ls /scratch/jjyeung/orch_n30/cont_ops/inbox; ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/cont_ops | head -3
