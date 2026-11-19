#!/bin/bash
# start queued Codex builds while fewer than 3 of mine run; one start per call (spacing)
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
load=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); avail=$(free -g | awk '/^Mem:/{print $7}')
run=0; for t in $(cut -d'|' -f1 $P/queue.txt) so_read_fix so_launch_fix so_git_fix so_pack_fix; do tmux has-session -t "=$t" 2>/dev/null && run=$((run+1)); done
echo "my codex builds running: $run (load $load avail ${avail}G)"
started=0
while IFS='|' read -r n L pr model mk; do
  [[ -z "$n" ]] && continue
  tmux has-session -t "=$n" 2>/dev/null && { echo "$n RUNNING"; continue; }
  [[ -f $L/work/${mk}_STARTED_$n ]] && { echo "$n ENDED: $(head -1 $L/out/REPORT.md 2>/dev/null | cut -c1-180)"; continue; }
  CAP=$(cat $P/cap.txt 2>/dev/null || echo 2)
  if (( run < CAP && started == 0 && load < 60 && avail >= 150 )); then
    mkdir -p $L/work $L/out/patches $L/in; cp $P/$pr $L/PROMPT_$n.md; date -u > $L/work/${mk}_STARTED_$n
    tmux new-session -d -s $n "cd $L && nice -n 10 bash $B/tools/codex_local.sh implement $L $L/PROMPT_$n.md --model $model --effort high --label $n --skip-git-check > $L/work/dispatch_$n.log 2>&1"
    echo "started $n ($model)"; run=$((run+1)); started=1
  else echo "$n QUEUED"; fi
done < $P/queue.txt
for t in so_read_fix so_launch_fix so_git_fix; do tmux has-session -t "=$t" 2>/dev/null && echo "$t RUNNING" || echo "$t ENDED"; done
for c in so_cr_step; do W=/scratch/jjyeung/orch_n30/$c; echo "-- $c: verdict=$(head -1 $W/REVIEW_VERDICT.md 2>/dev/null) running=$(tmux has-session -t "=$c" 2>/dev/null && echo y || echo n)"; done
for t in so_read so_launch so_git; do echo "-- $t: $(head -1 /scratch/jjyeung/orch_n30/$t/out/REPORT.md | cut -c1-200)"; done
