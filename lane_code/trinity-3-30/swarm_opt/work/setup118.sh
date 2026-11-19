#!/bin/bash
# run on trinity-1-18 after so_in extraction
set -u
I=/scratch/jjyeung/orch_n30/so_in; P=$I/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
echo "host $(hostname -s) $(date -u +%FT%TZ)"; uptime; free -g | head -2; df -h /scratch | tail -1
load=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1); avail=$(free -g | awk '/^Mem:/{print $7}')
T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/out/tree_rebuild_b20_780ca7b4.tar
sha=$(sha256sum $T | cut -d' ' -f1); echo "b20 sha $sha"
[[ $sha == 3d58bd34ebbd44472cb7bc85adecfe79df53ccaa4c395bb866d111ac8741c442 ]] || { echo "B20 SHA MISMATCH"; exit 3; }
for t in so_step so_launch so_read; do
  L=/scratch/jjyeung/orch_n30/$t; mkdir -p $L/in $L/out/patches $L/work
  cp $P/$t.md $L/PROMPT.md
  if [[ $t != so_read && ! -d $L/in/tree ]]; then mkdir -p $L/in/tree && nice -n 10 tar xf $T -C $L/in/tree; fi
done
du -sh /scratch/jjyeung/orch_n30/so_step/in/tree | tail -1
if (( load > 60 || avail < 150 )); then echo "WAIT load=$load avail=$avail: not dispatching"; exit 0; fi
for t in so_step so_launch so_read; do
  L=/scratch/jjyeung/orch_n30/$t; net=""; [[ $t == so_step ]] && net="--net"
  tmux has-session -t $t 2>/dev/null && { echo "$t tmux exists"; continue; }
  tmux new-session -d -s $t "cd $L && nice -n 10 bash $B/tools/codex_local.sh implement $L $L/PROMPT.md --model gpt-6-astra --effort high --label $t --skip-git-check $net > $L/work/dispatch.log 2>&1"
  echo "started $t"
done
sleep 20; tmux ls; for t in so_step so_launch so_read; do tail -3 /scratch/jjyeung/orch_n30/$t/work/dispatch.log; done
