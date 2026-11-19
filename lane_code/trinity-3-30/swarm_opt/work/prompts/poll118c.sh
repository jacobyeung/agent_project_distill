#!/bin/bash
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
load=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); avail=$(free -g | awk '/^Mem:/{print $7}')
n=0; for t in so_step so_launch so_read so_git so_pack; do tmux has-session -t "=$t" 2>/dev/null && n=$((n+1)); done
echo "builds running: $n"
for t in so_pack so_git; do
  L=/scratch/jjyeung/orch_n30/$t
  if [[ ! -d $L ]] && (( n < 3 && load < 60 && avail >= 150 )); then
    mkdir -p $L/in $L/out/patches $L/work; cp $P/$t.md $L/PROMPT.md
    [[ $t == so_git ]] && cp /scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/gitin/* $L/in/
    tmux new-session -d -s $t "cd $L && nice -n 10 bash $B/tools/codex_local.sh implement $L $L/PROMPT.md --model gpt-6-astra --effort high --label $t --skip-git-check > $L/work/dispatch.log 2>&1"
    echo "started $t"; n=$((n+1))
  fi
done
bash $P/poll118.sh
L=/scratch/jjyeung/orch_n30/so_read; [[ -f $L/out/REPORT.md ]] && { echo "#### so_read REPORT"; wc -c $L/out/REPORT.md; cat $L/out/REPORT.md | head -c 14000; ls -R $L/out | head -50; }
