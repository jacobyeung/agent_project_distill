#!/bin/bash
# prints new ORCH events after 1812Z and inbox contents
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
date -u +%H%MZ
ls $B/events/lever | awk '$0 > "20261122T1812Z"' | grep -v STATUS
ls /scratch/jjyeung/orch_n30/lever10/inbox
