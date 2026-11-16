#!/bin/bash
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3
python3 /scratch/jjyeung/orch_n30/k1_ops3/work/prog2b.py | head -2
grep -E 'EXIT|STOP' /scratch/jjyeung/k1/RUN2b.log; cat /scratch/jjyeung/k1/STALL2b.log 2>/dev/null
ls /scratch/jjyeung/k1/run_tower_sam_2 | grep -x HALTED.json
pgrep -u jjyeung -f 'codex exec -m gpt-6-astra.*codex_gtset' >/dev/null && echo codex_running || echo codex_gone; ls /scratch/jjyeung/orch_n30/k1_ops3/work/codex_gtset | tr '\n' ' '; echo
ls $E | grep -E '^20261116.*ORCH' | tail -2; ls /scratch/jjyeung/orch_n30/k1_ops3/inbox
