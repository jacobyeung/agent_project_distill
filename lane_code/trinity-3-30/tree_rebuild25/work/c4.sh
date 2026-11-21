W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr2
cp /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/n_review/20261121T0212Z_RESULT_PASS_task_A_restated_for_arming_under_RULING_0211Z.md $W/work/TASKA_PASS_0212Z.md; sha256sum $W/work/TASKA_PASS_0212Z.md | cut -c1-16
ls $W/w24z11b/out; cat $W/w24z11b/out/ARM_LAUNCH_24M4Z11B.md | cut -c1-400 | head -60
ls -la $W/w24z13b/out | tail -4; tail -2 $W/work/b24m4z13b.log | cut -c1-200
