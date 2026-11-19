timeout 100 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'bash -s' <<'Y'
O=/scratch/jjyeung/orch_n30; echo "$(date -u +%TZ) procs=$(ps -u jjyeung --no-headers | wc -l) used=$(df -h /scratch | tail -1 | awk '{print $3}')"
nvidia-smi --query-gpu=index,uuid --format=csv,noheader > /tmp/sb_g.txt
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv,noheader | while IFS=, read -r p u m; do i=$(grep "$(echo $u)" /tmp/sb_g.txt | cut -d, -f1); echo -n "card$i:$(ps -o user= -p $p | tr -d ' ') "; done; echo
E=$O/sb_cachk/out/v2/track/EVENTS.jsonl; echo "carry units=$(grep -c '"UNIT"' $E) last=$(tail -1 $E | cut -c1-160)"; ls $O/sb_cachk/out/v2/track | tr "\n" " "; echo; tmux has-session -t sb_carry 2>/dev/null && echo carry_alive || echo carry_ended
echo "phrase pools=$(ls $O/sb_ph2fix/sb_mask_phrase/out/pool_part2 | wc -l) $(ls $O/sb_ph2fix/sb_mask_phrase/out/pool_part2 | grep -v -E '^[0-9a-f]{16}$' | tr "\n" " ")"; tmux has-session -t sb_ph2 2>/dev/null && echo ph2_alive || { echo ph2_ended; tail -3 $O/sb_ph2fix/LAUNCH_228.log; }
echo "tower done=$(grep -c DONE $O/sb_ktfix2/out/tower_frames/run_A.log) $(tail -1 $O/sb_ktfix2/out/tower_frames/DRIVER.log | cut -c1-150)"; tmux has-session -t sb_towerA 2>/dev/null && echo towerA_alive || { echo towerA_ended; tail -3 $O/sb_ktfix2/out/tower_frames/run_A.log; }
Y
