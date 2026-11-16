#!/bin/bash
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events; C=/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/c6
date -u +%T; ls /scratch/jjyeung/orch_n30/cont_ops/inbox; ls -t $E/cont_ops | grep ORCH | head -2; ls $E/review_d0r | grep -v -x 'STATUS.md\|REVIEW_VERDICT_D0_READ_KIT.md\|20261116T0932Z_RESULT_d0_read_kit.md'
sed -n "/== metrics/,/== free/p" $C/q3.out | grep "^[0-9]" | tail -1 | cut -c1-150; tail -1 $C/q3.out | cut -c1-80
