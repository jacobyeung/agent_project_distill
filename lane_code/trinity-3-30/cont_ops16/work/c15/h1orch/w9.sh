#!/bin/bash
# wait up to $1 minutes for a new ORCH event, inbox file, or main INBOX_TO_DISTILL_ORCH file
D=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918; E=$D/orch_n30/events/cont_ops; I=/scratch/jjyeung/orch_n30/cont_ops/inbox
snap(){ { ls $E | grep _ORCH_; ls $I; ls $D | grep INBOX_TO_DISTILL_ORCH; } 2>/dev/null | sort; }
B=$(snap)
for i in $(seq 1 $1); do sleep 60; N=$(snap); if [ "$N" != "$B" ]; then comm -13 <(echo "$B") <(echo "$N"); exit 0; fi; done
echo none
