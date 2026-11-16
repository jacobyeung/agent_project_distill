#!/bin/bash
# wait up to $1 seconds (default 1200) for a change worth acting on; print what changed
L=/scratch/jjyeung/orch_n30/gpu_fill; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918; E=$B/orch_n30/events
snap(){ for l in gpu_fill b11_presence b05_owngrd b04_e2ehook trin_read trin_read3 h1_headsft; do ls $E/$l 2>/dev/null | grep -v -E "STATUS|FREE_CARDS" | { [ $l = gpu_fill ] && cat || grep -E "RESULT|QUESTION|BLOCKER|CARD"; } | sed "s|^|$l/|"; done; ls $B | grep INBOX_TO_DISTILL; ls $L/inbox 2>/dev/null; grep -c CANDIDATE $L/alerts.log; grep -E "^- trinity-(1-13|1-3|1-18|0-13|0-28) " $E/gpu_fill/FREE_CARDS.md | sed 's/; upd [0-9:]*//; s|/scratch [0-9]*GB|/scratch|'; }
snap > $L/.s0; end=$(( $(date +%s) + ${1:-1200} ))
while [ $(date +%s) -lt $end ]; do sleep 60; snap > $L/.s1; if ! cmp -s $L/.s0 $L/.s1; then date -u +%H%MZ; diff $L/.s0 $L/.s1 | grep '^[<>]'; exit 0; fi; done
date -u +%H%MZ; echo NOCHANGE
