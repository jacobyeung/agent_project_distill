#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
# start a Cursor review when its fix session has ended
for c in so_read_fix3:so_read:FIX3:so_cr_read4:cr_read4.md so_pack_a_fix2:so_pack_a:FIX2:so_cr_pack_a3:cr_pack_a3.md; do IFS=: read -r fx ws mk rv pr <<< "$c"
  if [[ -f /scratch/jjyeung/orch_n30/$ws/work/${mk}_STARTED_$fx ]] && ! tmux has-session -t =$fx 2>/dev/null && [[ ! -d /scratch/jjyeung/orch_n30/$rv ]]; then bash $P/cursor_start.sh $rv $P/$pr; fi; done
bash $P/poll118al.sh
