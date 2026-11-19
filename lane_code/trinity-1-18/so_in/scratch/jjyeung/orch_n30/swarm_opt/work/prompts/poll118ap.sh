#!/bin/bash
P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
for c in so_read_fix4:so_read:FIX4:so_cr_read5:cr_read5.md so_pack_a_fix3:so_pack_a:FIX3:so_cr_pack_a4:cr_pack_a4.md so_step_fix4:so_step:FIX4:so_cr_step5:cr_step5.md so_read_fix5:so_read:FIX5:so_cr_read6:cr_read6.md so_pack_a_fix4:so_pack_a:FIX4:so_cr_pack_a5:cr_pack_a5.md so_step_fix5:so_step:FIX5:so_cr_step6:cr_step6.md; do IFS=: read -r fx ws mk rv pr <<< "$c"
  if [[ -f /scratch/jjyeung/orch_n30/$ws/work/${mk}_STARTED_$fx ]] && ! tmux has-session -t =$fx 2>/dev/null && [[ ! -d /scratch/jjyeung/orch_n30/$rv ]]; then bash $P/cursor_start.sh $rv $P/$pr; fi; done
date -u +%H:%MZ; bash $P/qrun.sh | grep -v "ENDED\|^-- so_"
for c in so_cr_step6 so_cr_read6 so_cr_pack_a5; do [[ -d /scratch/jjyeung/orch_n30/$c ]] && echo "$c: $(head -1 /scratch/jjyeung/orch_n30/$c/REVIEW_VERDICT.md 2>/dev/null) tmux=$(tmux has-session -t =$c 2>/dev/null && echo y || echo n)"; done
for t in so_read so_pack_a so_step; do echo "$t: $(head -1 /scratch/jjyeung/orch_n30/$t/out/REPORT.md | cut -c1-160)"; done
uptime; free -g | sed -n 2p
