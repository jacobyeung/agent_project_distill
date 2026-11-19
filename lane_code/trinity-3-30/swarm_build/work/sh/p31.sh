timeout 100 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'bash -s' <<'Y'
date -u +%TZ; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr "\n" " "; echo
nvidia-smi --query-compute-apps=pid,gpu_uuid --format=csv,noheader | while IFS=, read -r p u; do echo -n "$(ps -o user= -p $p) "; done; echo
ls -la /tmp/terminator/ 2>/dev/null | tail -8
O=/scratch/jjyeung/orch_n30; tail -3 $O/sb_cachk/out/v2/LAUNCH_228.log | cut -c1-250; cat $O/sb_cachk/out/v2/track/BUDGET.json | cut -c1-400; echo; cat $O/sb_ph2fix/sb_mask_phrase/out/pool_part2/KILLED.json | cut -c1-300; echo; tail -4 $O/sb_ktfix2/out/tower_frames/DRIVER.log | cut -c1-200; ls $O/sb_ktfix2/out/tower_frames/ | tr "\n" " "
Y
