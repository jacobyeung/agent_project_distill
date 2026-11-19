timeout 100 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'bash -s' <<'Y'
date -u +%TZ; O=/scratch/jjyeung/orch_n30
nvidia-smi --query-gpu=index,uuid,memory.used,utilization.gpu --format=csv,noheader > /tmp/sb_g.txt
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv,noheader | while IFS=, read -r p u m; do i=$(grep "$(echo $u)" /tmp/sb_g.txt | cut -d, -f1); echo "card$i pid$p $(ps -o user= -p $p | tr -d ' ')$m"; done
cut -d, -f1,3,4 /tmp/sb_g.txt | tr "\n" ";"; echo
echo "-- carry"; tail -2 $O/sb_cachk/out/v2/LAUNCH_228.log | cut -c1-200; ls $O/sb_cachk/out/v2/track 2>/dev/null | head -8 | tr "\n" " "; echo; L=$(ls -t $O/sb_cachk/out/v2/track/*.log 2>/dev/null | head -1); [ -n "$L" ] && tail -3 "$L" | cut -c1-250
echo "-- phrase"; tail -3 $O/sb_ph2fix/LAUNCH_228.log | cut -c1-250; ls $O/sb_ph2fix/sb_mask_phrase/out/pool_part2 2>/dev/null | head -8 | tr "\n" " "; echo
echo "-- tower"; tail -2 $O/sb_ktfix2/out/tower_frames/DRIVER.log | cut -c1-200; tail -4 $O/sb_ktfix2/out/tower_frames/run_A.log | cut -c1-250
ps -u jjyeung --no-headers | wc -l; df -h /scratch | tail -1 | awk '{print $3, $4}'
Y
