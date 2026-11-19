#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
date -u +%H:%MZ; uptime; free -g | head -2
bash $P/qrun.sh
for t in so_xstore so_pack_fix so_corpus_fix so_step_fix so_read_fix; do W=/scratch/jjyeung/orch_n30/${t%_fix}; [[ $t == so_corpus_fix ]] && W=/scratch/jjyeung/orch_n30/so_corpus_fix; echo "-- $t: $(tail -c 300 $W/work/STATUS.md 2>/dev/null | tr '\n' ' ')"; done
grep -c "at capacity" /scratch/jjyeung/orch_n30/so_*/work/dispatch_*.log 2>/dev/null | grep -v ':0$'
ls /scratch/jjyeung/orch_n30/so_xstore/in 2>/dev/null
