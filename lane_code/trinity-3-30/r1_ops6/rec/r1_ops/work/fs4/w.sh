#!/bin/bash
m=/scratch/jjyeung/orch_n30/r1_ops/work/drv_p5/mon2_last.txt
date -u +%T; head -1 $m; grep -E '^17(1377|2180)' $m; grep -E 'metrics|m100|m200|artifact|export|ckpt|checkpoint' $m | tail -6
sed -n '/== 172180.proof.log/,/== 172180.err/p' $m | tail -5 | cut -c1-220
sed -n '/== 171377.err/,/== 171377.steps/p' $m | tail -4 | cut -c1-220
ls -t /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops/ | head -3; ls /scratch/jjyeung/orch_n30/r1_ops/inbox 2>/dev/null
